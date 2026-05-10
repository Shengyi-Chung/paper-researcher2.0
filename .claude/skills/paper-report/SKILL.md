---
name: paper-report-generator
description: "Generate research reports from analyzed papers. Trigger: 'generate a research report', 'create a report from these papers', 'summarize the papers into a report', 'generate report'"
author: Xiangyu-Tang
version: 1.2.0
tags:
  - productivity
  - report-automation
  - markdown
  - summarization
  - arxiv
---

# paper-report-generator

## Role
A specialized Skill that transforms analyzed paper data into structured, user-readable research reports. It **merges upstream analysis and abstracts with arXiv HTML export enrichment** (introduction, **methods/methodology**, conclusion, and **recent** related arXiv ids discovered across body text—not only the bibliography) so the narrative reflects both the original pipeline output and first-party paper sections.

### Agent behavior: what to emphasize
- **Primary (must summarize clearly):** **methods / methodology** and **contributions** (novelty, claims, takeaways). Combine upstream `key_contributions` and `methods` with export `methodology_text` and conclusion/intro only as needed to ground those two themes.
- **Secondary (keep shorter):** broad background from introductions, long related-work lists, peripheral comparison tables, and raw citation-id dumps—use only to support the methods/contributions story.
- When writing **`paper_reports.md`**, aim for **full, polished prose** (clear structure, complete sentences, coherent flow).
- When replying **in chat** about the same task, stay **concise**: short status, key takeaways, and pointers to paths (for example `paper_reports.md` / `paper_export_enrichment.json`) rather than pasting the whole report unless the user asks.

## Input/Output Specifications

### Input
1. **paper-analysis.json** (from paper-analyze):
   - `analysis_date`: Analysis timestamp
   - `query`: Original search query
   - `total_papers`: Number of papers
   - `ranked_papers`: Array of paper objects with `rank`, `title`, `arxiv_id`, `authors`, `relevance_score`, `key_contributions`, `methods`

2. **papers.json** (from paper-search):
   - Paper metadata including full `abstract` text

3. **Enrichment source (this Skill):** `arxiv_utils.py` in the same workspace, especially `fetch_paper_export_bundle(arxiv_export_id, as_of=...)`, which performs **one** HTTP GET per paper to `export.arxiv.org` and returns:
   - Plain-text **introduction**, **methodology** (Methods / Methodology / Materials and methods / similar headings), and **conclusion** excerpts (heading-based; conclusion may fall back to “Discussion and conclusion”)
   - `related_arxiv_ids_recent`: arXiv ids cited in introduction + methodology + conclusion + references, **filtered to the last two calendar years** from `as_of` (default: report generation date)

### Output

**1. paper_abstracts.json**  
Same as before: extracted abstracts aligned with the ranked list.

**2. paper_export_enrichment.json** (new)  
Written after enrichment passes; merges export data with original ids for traceability.

```json
{
  "generated_at": "ISO timestamp",
  "as_of_date": "YYYY-MM-DD used for two-year arXiv id cutoff",
  "enrichment_version": "1.2",
  "papers": [
    {
      "arxiv_id": "2604.xxxxx",
      "canonical_id": "2604.xxxxx",
      "rank": 1,
      "relevance_score": 9,
      "introduction_text": "...",
      "methodology_text": "...",
      "conclusion_text": "...",
      "related_arxiv_ids_recent": ["2405.01234", "2501.09999"],
      "has_references_section": true,
      "export_error": null
    }
  ]
}
```

If a paper cannot be fetched (network, 429, or no export HTML for very old ids), set `export_error` to a short string and leave text fields empty; still generate the report from original inputs.

**3. paper_reports.md**  
Markdown report that **explicitly combines three layers**:
- **Layer A (original):** `paper_analysis.json` rankings, scores, key contributions, methods
- **Layer B (metadata):** abstracts from `papers.json`
- **Layer C (export):** introduction / **methodology** / conclusion excerpts and `related_arxiv_ids_recent` from `paper_export_enrichment.json`

Use Layer C so the written report **centers methods and contributions**: methodology excerpts and upstream `methods` should align; contributions should integrate `key_contributions`, conclusion claims, and abstract. Use intro and citation neighborhoods as **supporting** detail. In chat, summarize that center of gravity briefly and point to the saved report.

## Workflow

### Step 1: Read Input Data
Read:
- `/data/papers.json`
- `/data/paper_analysis.json` (or `paper-analysis.json` if that is the filename used upstream—normalize to one convention and document in the run)

### Step 2: Extract Abstracts
Produce `paper_abstracts.json` as in v1.0.

### Step 3: Enrich via arXiv export (new)
For papers that have a valid `arxiv_id` in `ranked_papers`:

1. **Throttle:** Respect `arxiv_utils` query pacing (do not parallel-burst `export.arxiv.org`).
2. **Priority:** Enrich `relevance_score >= 8` first; then next tiers until a sensible cap (e.g. top 15–20) to limit rate limits.
3. For each id, call `fetch_paper_export_bundle(canonical_id, as_of=today)` from `arxiv_utils.py`.
4. Build `paper_export_enrichment.json`, joining **original** `rank`, `relevance_score`, `title`, `arxiv_id` with export fields.

**Two-year rule:** Only ids in `related_arxiv_ids_recent` are those passing `recent_two_years_eligible` in `arxiv_utils` (introduction + methodology + conclusion + references combined). Do not substitute a broader arXiv API search here—this list is export-derived only.

**Fetch eligibility:** Papers whose id has `YY < 23` in the arXiv numbering may lack HTML export; record `export_error` and continue.

### Step 4: Identify High-Relevance Papers
Same threshold: `relevance_score >= 8` for top billing.

### Step 5: Generate Report Structure
Build `paper_reports.md` in this order:

```markdown
# Research Report: [Topic/Query]

**Generated**: YYYY-MM-DD  
**Total Papers**: N  
**High-Relevance Papers**: M  
**Enrichment**: Introduction / methodology / conclusion + recent related arXiv ids from export HTML (`as_of` = YYYY-MM-DD)

---

## Executive Summary
Synthesize the landscape using **Layer A + B + C**, but **lead with methods and contributions** per paper and for the field: what each work does technically and what it claims to add. Use abstracts and introductions as context; use conclusions for limitations and future work. Call out **convergence** and **tension** between papers when that clarifies methodological or claims-level differences.

---

## ⭐ High-Relevance Papers (Top Picks)

> **[Paper Title](https://arxiv.org/abs/xxxxx)**  
> Relevance: X/10 | Authors: A, B, C
>
> **Methods & methodology (summarized)** — Integrate upstream **Methods** with export **methodology_text** into a short, precise description (components, data, training/eval, baselines). This block should be **substantive**, not a placeholder.
>
> **Contributions (summarized)** — Integrate upstream **Key Contributions** with the conclusion (and abstract if needed) into crisp bullets or a tight paragraph emphasizing **what is new** and **what is demonstrated**.
>
> **Abstract** (from papers.json, supporting context): keep **brief** if the sections above already cover the same ground.
>
> **Introduction (excerpt)** (export, supporting): ...
>
> **Conclusion (excerpt)** (export, supporting): ...
>
> **Recent related arXiv ids** (from body + refs, last 2 years): `id1`, `id2`, …

[Repeat for each high-relevance paper…]

---

## Detailed Analysis by Category
Group medium/low-relevance papers by methodology/topic. For each paper, prefer **one or two bullets on method + one on contribution**; trim introduction-style prose.

---

## Comparison Table

| Rank | Paper | Relevance | Methods (synopsis) | Contributions (synopsis) | Recent related ids |
|------|-------|-----------|--------------------|--------------------------|----------------------|
| 1 | Title | 9/10 | … | … | id1, id2 |
```

### Step 6: Save Outputs
```
/data/
├── papers.json
├── paper_analysis.json
├── paper_abstracts.json
├── paper_export_enrichment.json   # THIS SKILL (new)
└── paper_reports.md               # THIS SKILL
```

## Trigger Scenarios
Same as v1.0: after paper-analyze, or on user request to generate a report.

## Error Handling
| Error | Handling |
|-------|----------|
| paper_analysis.json not found | Request paper-analyze first |
| paper_analysis.json empty | Inform user; suggest new search |
| papers.json missing abstracts | Note unavailable; rely on analysis + export text |
| export fetch failure | Store `export_error`; report still uses Layers A+B |
| Missing Introduction/Methodology/Conclusion headings in HTML | Leave that excerpt blank; keep related ids from available regions |
| Invalid JSON in inputs | Skip bad entries; log counts |

## Evaluation Metrics
- **Relevance Accuracy**: High-relevance papers (score >= 8) highlighted correctly
- **Structural Clarity**: Sections ordered as specified; table includes enrichment column when data exists
- **Merge quality**: Report explicitly uses analysis + abstract + export (incl. methodology) + recent ids; **methods and contributions** are synthesized, not copy-pasted wholesale
- **Chat vs artifact**: Chat response concise; `paper_reports.md` complete and well written
- **Markdown Compatibility**: Renders cleanly; arXiv links use full `https://arxiv.org/abs/...` URLs

## Integration with Other Skills
- **Input:** `paper-search` → `/data/papers.json`; `paper-analyze` → `/data/paper_analysis.json`
- **In-repo helper:** `arxiv_utils.fetch_paper_export_bundle` for HTML export enrichment (not a general-purpose web crawl)

---

## RESTRICTIONS (strict)

### ✅ This Skill **must** do:
1. **Read analysis results** — Load rankings and scores from `paper_analysis.json`.
2. **Read paper metadata** — Load abstracts (and related fields) from `papers.json`.
3. **Enrich via `arxiv_utils`** — For prioritized papers, call `fetch_paper_export_bundle` and write `paper_export_enrichment.json`.
4. **Merge three layers into the report** — Combine analysis + abstracts + export (introduction, **methodology**, conclusion, last-two-years related ids) into `paper_reports.md`; the narrative must **center methods and contributions**.
5. **Concise chat, complete report** — Keep in-chat replies brief; keep `paper_reports.md` full, fluent, and deliverable.
6. **Highlight high-relevance papers** — Surface `relevance_score >= 8` first and prioritize export fetches for them.
7. **Emit `paper_abstracts.json`**.

### ❌ This Skill **must not** do:
1. **Replace upstream analysis or scoring** — Do not alter scores or structured fields in `paper_analysis.json`.
2. **General web search** — Do not crawl arbitrary sites; the only allowed HTTP fetch target for enrichment is `export.arxiv.org` through `arxiv_utils`.
3. **Broaden citation discovery beyond the two-year rule** — `related_arxiv_ids_recent` must come only from export-HTML scanning and `recent_two_years_eligible`; do not run separate arXiv API topic searches to expand that list.
4. **Use briefing layout** — Do not use the `briefing-report-generator` format.
5. **Unrelated visualizations** — Do not generate PNG/HTML charts or figures for this skill.
6. **Default to Chinese briefing** — For Chinese briefing-style output, use `briefing-report-generator` instead.

### 📌 Edge cases:
- If `paper_analysis.json` is missing → Tell the user to run paper-analyze first.
- If the user wants briefing layout → Point them to `briefing-report-generator`.
- If the user wants charts → State that this skill does not support chart generation.
- If the user wants broader literature search → Point them to paper-search; “related papers” here are **only** recent (two-year) arXiv ids parsed from export HTML.
