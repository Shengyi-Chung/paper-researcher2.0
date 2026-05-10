"""
For each given arXiv id (YYYY.NNNNN with optional vN), optionally fetch export HTML
(if YY >= 23), scan **Introduction**, **Conclusion** (and related headings), and the
**References** bibliography for arXiv-style ids, and build a directed citation graph:
source paper -> each discovered id.

Only ids whose YYMM (first four digits) falls in the **last two calendar years** from
the evaluation date are kept as citation targets (default: ``date.today()``). Fetching
still requires YY >= YY_PREFIX_MIN so export HTML exists.

Rate limit: wait at least QUERY_INTERVAL_S between consecutive HTTP queries; when there
are several eligible sources in one run, a larger floor is used to avoid export.arxiv.org
429 bursts. HTTP 429 responses are retried with backoff and optional Retry-After.

Output: result.json (NetworkX node-link JSON). CLI requires one or more ids; no default.

For report skills: use ``fetch_paper_export_bundle`` to obtain introduction/conclusion
plain text and the filtered related-id list from a single HTML fetch.
"""

from __future__ import annotations

import html as html_module
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import networkx as nx
from networkx.readwrite.json_graph import node_link_data

OUT_NAME = "result.json"
USER_AGENT = "arxivtest/1.0 (+https://arxiv.org/help/html)"
EXPORT_HTML_BASE = "https://export.arxiv.org/html/"
# First two digits of the YYYY block must be >= this value (arxiv YY month encoding).
YY_PREFIX_MIN = 23

REF_ARXIV_RE = re.compile(
    r"(?<![0-9])(?:arxiv\s*:\s*)?(\d{4}\.\d{5})(?:v\d)?(?![0-9])",
    re.IGNORECASE,
)

QUERY_INTERVAL_S = 0.5
# export.arxiv.org often tolerates ~2 quick requests; more in one process need wider spacing.
_MULTI_FETCH_INTERVAL_EXTRA_S = 0.5
_FETCH_429_MAX_RETRIES = 8

_last_query_monotonic: float | None = None
_active_query_interval: float = QUERY_INTERVAL_S


def _effective_interval_for_batch(num_eligible_sources: int) -> float:
    """Wider gaps when many HTML exports are chained in a single run (reduces 429s)."""
    if num_eligible_sources <= 2:
        return QUERY_INTERVAL_S
    # e.g. 3 -> 1.5+0.5=2.0s, 4 -> 2.5s, 5 -> 3.0s floor between requests
    return max(
        QUERY_INTERVAL_S,
        1.5 + _MULTI_FETCH_INTERVAL_EXTRA_S * (num_eligible_sources - 2),
    )


def _throttle_query() -> None:
    """Wait so that at least _active_query_interval seconds elapse since the previous query finished."""
    global _last_query_monotonic
    now = time.monotonic()
    if _last_query_monotonic is not None:
        elapsed = now - _last_query_monotonic
        if elapsed < _active_query_interval:
            time.sleep(_active_query_interval - elapsed)


def _retry_after_seconds(err: urllib.error.HTTPError) -> float | None:
    raw = err.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def fetch_html(url: str) -> str:
    global _last_query_monotonic
    last_http: urllib.error.HTTPError | None = None
    for attempt in range(_FETCH_429_MAX_RETRIES):
        _throttle_query()
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                out = resp.read().decode(charset, errors="replace")
        except urllib.error.HTTPError as e:
            _last_query_monotonic = time.monotonic()
            if e.code == 429 and attempt < _FETCH_429_MAX_RETRIES - 1:
                last_http = e
                ra = _retry_after_seconds(e)
                if ra is not None and ra > 0:
                    wait = ra
                else:
                    wait = min(120.0, 3.0 * (2**attempt))
                time.sleep(wait)
                continue
            raise
        else:
            _last_query_monotonic = time.monotonic()
            return out
    if last_http is not None:
        raise last_http
    raise RuntimeError("fetch_html: exhausted retries without HTTPError")


def parse_input(raw: str) -> str | None:
    """Return canonical id string for the export URL (e.g. 2605.06659v1), or None."""
    s = raw.strip()
    m = re.fullmatch(r"(\d{4})\.(\d{5})(?:v(\d))?", s, flags=re.IGNORECASE)
    if not m:
        return None
    yymm, num, ver = m.group(1), m.group(2), m.group(3)
    if ver is not None:
        return f"{yymm}.{num}v{ver}"
    return f"{yymm}.{num}"


def base_id(canonical: str) -> str:
    """YYYY.NNNNN without version suffix."""
    return canonical.split("v", 1)[0]


def yy_prefix_eligible(arxiv_base: str) -> bool:
    """First two digits of the four-digit block (before the dot) >= YY_PREFIX_MIN."""
    return int(arxiv_base[:2]) >= YY_PREFIX_MIN


def recent_two_years_eligible(arxiv_base: str, *, as_of: date | None = None) -> bool:
    """
    True if the id's YYMM block denotes a month no earlier than the same month
    two calendar years before ``as_of`` (first day of that month on each side).
    """
    as_of = as_of or date.today()
    if len(arxiv_base) < 5:
        return False
    yymm = arxiv_base[:4]
    if not yymm.isdigit():
        return False
    yy, mm = int(yymm[:2]), int(yymm[2:4])
    if not 1 <= mm <= 12:
        return False
    year = 2000 + yy
    paper_month_start = date(year, mm, 1)
    try:
        cutoff = date(as_of.year - 2, as_of.month, 1)
    except ValueError:
        cutoff = date(as_of.year - 2, 1, 1)
    return paper_month_start >= cutoff


def extract_reference_html(page: str) -> str:
    m = re.search(
        r'<section\s[^>]*\bid\s*=\s*["\']bib["\'][^>]*>',
        page,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        raise ValueError('Could not find <section id="bib"> (References) in HTML.')
    start = m.end()
    end = page.lower().find("</section>", start)
    if end == -1:
        raise ValueError('Unclosed bibliography <section id="bib">.')
    return page[start:end]


def extract_reference_html_optional(page: str) -> str:
    """Return References HTML fragment, or empty string if the section is missing."""
    try:
        return extract_reference_html(page)
    except ValueError:
        return ""


_HEADING_INNER_RE = re.compile(r"<h[23]\b[^>]*>(.*?)</h[23]\s*>", re.IGNORECASE | re.DOTALL)


def _heading_inner_to_plain(inner_html: str) -> str:
    t = re.sub(r"<[^>]+>", " ", inner_html)
    t = html_module.unescape(t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    t = re.sub(r"^\d+\s+", "", t)
    return t


def _extract_section_by_heading(page: str, labels: tuple[str, ...]) -> str:
    """
    Return raw HTML after the first h2/h3 whose visible title matches a label
    (substring match on normalized heading text), up to the next h2/h3.
    """
    want = {lab.lower() for lab in labels}
    for m in _HEADING_INNER_RE.finditer(page):
        plain = _heading_inner_to_plain(m.group(1))
        if not any(lab in plain for lab in want):
            continue
        start = m.end()
        m_next = _HEADING_INNER_RE.search(page, start)
        end = m_next.start() if m_next else len(page)
        return page[start:end]
    return ""


def extract_introduction_html(page: str) -> str:
    return _extract_section_by_heading(page, ("introduction",))


def extract_conclusion_html(page: str) -> str:
    s = _extract_section_by_heading(page, ("conclusion", "conclusions"))
    if s:
        return s
    return _extract_section_by_heading(page, ("discussion and conclusion",))


def html_fragment_to_text(fragment: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.IGNORECASE)
    s = re.sub(r"</(p|div|li|h2|h3|span)\s*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)
    s = html_module.unescape(s)
    s = re.sub(r"[ \t\f\v]+", " ", s)
    s = re.sub(r"\n[ \t]+", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def find_recent_arxiv_ids_in_text(html_or_text: str, *, as_of: date | None = None) -> list[str]:
    """
    Regex-scan arbitrary HTML or text; keep YYYY.NNNNN whose YYMM is within the last
    two calendar years from ``as_of``, deduped and sorted.
    """
    blob = html_or_text + "\n" + html_fragment_to_text(html_or_text)
    seen: set[str] = set()
    out: list[str] = []
    for m in REF_ARXIV_RE.finditer(blob):
        rid = m.group(1)
        if recent_two_years_eligible(rid, as_of=as_of) and rid not in seen:
            seen.add(rid)
            out.append(rid)
    out.sort()
    return out


def find_eligible_arxiv_ids_in_references(bib_html: str) -> list[str]:
    """Backward-compatible name: scan bibliography only, two-year window from today."""
    return find_recent_arxiv_ids_in_text(bib_html)


def fetch_paper_export_bundle(
    arxiv_export_id: str,
    *,
    as_of: date | None = None,
    intro_max_chars: int = 12000,
    conclusion_max_chars: int = 8000,
) -> dict:
    """
    One HTTP fetch: introduction + conclusion HTML (best effort), references,
    plain-text excerpts (truncated), and related arXiv ids from all of the above.

    Keys: canonical_id, base_id, introduction_text, conclusion_text,
    related_arxiv_ids_recent, has_references_section.
    """
    url = EXPORT_HTML_BASE + arxiv_export_id
    page = fetch_html(url)
    intro_h = extract_introduction_html(page)
    concl_h = extract_conclusion_html(page)
    bib_h = extract_reference_html_optional(page)
    intro_t = html_fragment_to_text(intro_h) if intro_h else ""
    concl_t = html_fragment_to_text(concl_h) if concl_h else ""
    if intro_max_chars > 0 and len(intro_t) > intro_max_chars:
        intro_t = intro_t[:intro_max_chars].rsplit(" ", 1)[0] + " …"
    if conclusion_max_chars > 0 and len(concl_t) > conclusion_max_chars:
        concl_t = concl_t[:conclusion_max_chars].rsplit(" ", 1)[0] + " …"
    blob = "\n".join(x for x in (intro_h, concl_h, bib_h) if x)
    ids = find_recent_arxiv_ids_in_text(blob, as_of=as_of)
    canonical = parse_input(arxiv_export_id)
    if canonical is None:
        canonical = arxiv_export_id.strip()
    b = base_id(canonical)
    return {
        "canonical_id": canonical,
        "base_id": b,
        "introduction_text": intro_t,
        "conclusion_text": concl_t,
        "related_arxiv_ids_recent": ids,
        "has_references_section": bool(bib_h),
    }


def collect_reference_arxiv_ids(arxiv_export_id: str, *, as_of: date | None = None) -> list[str]:
    return fetch_paper_export_bundle(arxiv_export_id, as_of=as_of)[
        "related_arxiv_ids_recent"
    ]


def build_citation_graph(raw_ids: list[str]) -> nx.DiGraph:
    """
    For each input id, add edges source_base -> ref for every arXiv id found in
    that paper's export HTML (introduction, conclusion/discussion, and references),
    keeping only targets whose YYMM falls within the last two calendar years.
    Inputs with YY < YY_PREFIX_MIN are nodes only (no fetch, no outgoing edges).
    """
    global _active_query_interval
    G = nx.DiGraph()
    refs_by_base: dict[str, list[str]] = {}
    canonical_by_base: dict[str, str] = {}

    for raw in raw_ids:
        canonical = parse_input(raw)
        if canonical is None:
            raise ValueError(
                f"Expected id matching dddd.ddddd or dddd.dddddvN (v = one digit), got: {raw!r}"
            )
        b = base_id(canonical)
        if b not in G:
            G.add_node(b, role="source", raw_inputs=[raw.strip()])
        else:
            G.nodes[b]["raw_inputs"].append(raw.strip())
        if b not in canonical_by_base:
            canonical_by_base[b] = canonical

    n_eligible = sum(1 for b in canonical_by_base if yy_prefix_eligible(b))
    _active_query_interval = _effective_interval_for_batch(n_eligible)
    try:
        for b, canonical in canonical_by_base.items():
            if not yy_prefix_eligible(b):
                continue
            if b in refs_by_base:
                continue
            refs_by_base[b] = collect_reference_arxiv_ids(canonical)

        for b in canonical_by_base:
            if b not in refs_by_base:
                continue
            for ref in refs_by_base[b]:
                if ref == b:
                    continue
                if ref not in G:
                    G.add_node(ref, role="reference")
                elif G.nodes[ref].get("role") == "source":
                    G.nodes[ref]["role"] = "source_and_cited"
                G.add_edge(b, ref)
    finally:
        _active_query_interval = QUERY_INTERVAL_S

    return G


def main() -> None:
    if len(sys.argv) < 2:
        print(
            f"Usage: {sys.argv[0]} <arxiv_id> [arxiv_id ...]\n"
            "  Each id: dddd.ddddd or dddd.dddddvN (version = one digit).",
            file=sys.stderr,
        )
        sys.exit(2)

    out_path = Path(__file__).resolve().parent / OUT_NAME
    raw_inputs = sys.argv[1:]

    try:
        G = build_citation_graph(raw_inputs)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except urllib.error.URLError as e:
        print(f"Failed to fetch: {e}", file=sys.stderr)
        sys.exit(1)

    data = node_link_data(G)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Wrote graph with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges to {out_path}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()