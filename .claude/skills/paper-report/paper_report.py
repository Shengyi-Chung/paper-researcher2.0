#!/usr/bin/env python3
"""
paper-report v1.2.0: Generate research reports from analyzed papers.
Merges upstream analysis and abstracts with arXiv HTML export enrichment
(introduction, methodology, conclusion, and recent related arXiv ids).

Workflow:
1. Read paper_analysis.json + papers.json
2. Extract abstracts -> paper_abstracts.json
3. Enrich via arXiv export (introduction/methodology/conclusion) -> paper_export_enrichment.json
4. Generate report (centered on methods & contributions) -> paper_reports.md
"""

import io
import json
import os
import sys
import time
from datetime import date, datetime
from typing import Dict, List, Optional

# Import arXiv export utilities (support both package and direct run)
try:
    from . import arxiv_utils
except ImportError:
    import arxiv_utils


def get_data_dir() -> str:
    """Get path to data directory"""
    # Navigate: paper-report/ -> skills/ -> .claude/ -> project_root/ -> data/
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data"
    )


def load_search_results() -> Optional[Dict]:
    """Load search results from papers.json (normalized name)"""
    # Try both naming conventions
    for filename in ["papers.json", "search_results.json"]:
        filepath = os.path.join(get_data_dir(), filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None


def load_analysis_results() -> Optional[Dict]:
    """Load analysis results from paper_analysis.json (normalized name)"""
    # Try both naming conventions
    for filename in ["paper_analysis.json", "analysis_results.json"]:
        filepath = os.path.join(get_data_dir(), filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None


def get_paper_by_id(papers: List[Dict], arxiv_id: str) -> Optional[Dict]:
    """Find paper by arxiv_id"""
    for paper in papers:
        if paper.get('arxiv_id') == arxiv_id:
            return paper
    return None


def safe_print(text: str):
    """Safe print with encoding handling"""
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        print(text)


def get_paper_score(paper: Dict) -> float:
    """
    Get relevance score from paper data.
    Supports both 'relevance_score' (direct) and 'pagerank_score' (normalized to 0-10).
    """
    rs = paper.get('relevance_score')
    if rs is not None:
        return float(rs)
    ps = paper.get('pagerank_score', 0)
    # Normalize pagerank_score to 0-10 scale
    # Typical range: 0.01-0.15, scale to ~10
    return min(10.0, ps * 100)


def extract_abstracts(papers: List[Dict], ranked_papers: List[Dict]) -> Dict:
    """Extract and align abstracts with ranked list -> paper_abstracts.json"""
    abstracts = {
        "generated_at": datetime.now().isoformat(),
        "papers": []
    }
    
    for ranked in ranked_papers:
        arxiv_id = ranked.get('arxiv_id')
        paper = get_paper_by_id(papers, arxiv_id)
        if paper:
            abstracts["papers"].append({
                "arxiv_id": arxiv_id,
                "title": paper.get('title', ''),
                "abstract": paper.get('abstract', ''),
                "rank": ranked.get('rank')
            })
    
    return abstracts


def enrich_with_exports(ranked_papers: List[Dict], as_of_date: Optional[date] = None) -> Dict:
    """
    Enrich papers via arXiv HTML export.
    Priority: relevance_score >= 8 first, cap at ~20 papers.
    -> paper_export_enrichment.json
    """
    as_of = as_of_date or date.today()
    
    # Separate high and low priority (use pagerank_score normalized to 10 as fallback)
    high_priority = [p for p in ranked_papers if get_paper_score(p) >= 8]
    medium_priority = [p for p in ranked_papers if 5 <= get_paper_score(p) < 8]
    
    # Cap total enrichment at 20 papers
    priority_order = high_priority + medium_priority
    priority_order = priority_order[:20]
    
    enrichment = {
        "generated_at": datetime.now().isoformat(),
        "as_of_date": as_of.isoformat(),
        "enrichment_version": "1.2",
        "papers": []
    }
    
    safe_print(f"\n[ENRICH] Fetching arXiv exports for {len(priority_order)} papers...")
    
    for i, paper in enumerate(priority_order, 1):
        arxiv_id = paper.get('arxiv_id', '')
        if not arxiv_id:
            continue
        
        safe_print(f"  [{i}/{len(priority_order)}] Fetching {arxiv_id}...")
        
        entry = {
            "arxiv_id": arxiv_id,
            "canonical_id": arxiv_id,
            "rank": paper.get('rank'),
            "relevance_score": get_paper_score(paper),
            "introduction_text": "",
            "methodology_text": "",
            "conclusion_text": "",
            "related_arxiv_ids_recent": [],
            "has_references_section": False,
            "export_error": None
        }
        
        try:
            bundle = arxiv_utils.fetch_paper_export_bundle(arxiv_id, as_of=as_of)
            entry["introduction_text"] = bundle.get("introduction_text", "")
            entry["methodology_text"] = bundle.get("methodology_text", "")
            entry["conclusion_text"] = bundle.get("conclusion_text", "")
            entry["related_arxiv_ids_recent"] = bundle.get("related_arxiv_ids_recent", [])
            entry["has_references_section"] = bundle.get("has_references_section", False)
        except Exception as e:
            entry["export_error"] = str(e)[:100]
        
        enrichment["papers"].append(entry)
        
        # Brief pause between fetches
        time.sleep(0.3)
    
    return enrichment


def generate_report(
    search_data: Dict,
    analysis_data: Dict,
    abstracts: Dict,
    enrichment: Dict
) -> str:
    """Generate markdown report with three-layer merge"""
    
    query = search_data.get('query', 'Unknown')
    total_papers = search_data.get('total_results', 0)
    # Support both "ranked_papers" and "pagerank_scores" naming conventions
    ranked_papers = analysis_data.get('ranked_papers') or analysis_data.get('pagerank_scores', [])
    papers = search_data.get('papers', [])
    
    # Build enrichment lookup
    enrichment_by_id = {p['arxiv_id']: p for p in enrichment.get('papers', [])}
    
    # High-relevance papers (score >= 8)
    high_relevance = [p for p in ranked_papers if get_paper_score(p) >= 8]
    
    # Build markdown
    md = []
    md.append(f"# Research Report: {query}")
    md.append("")
    md.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**Total Papers**: {total_papers}")
    md.append(f"**High-Relevance Papers**: {len(high_relevance)}")
    md.append(f"**Enrichment**: Introduction / methodology / conclusion + recent related arXiv ids from export HTML")
    md.append("")
    md.append("---")
    md.append("")
    
    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    md.append("This report analyzes papers retrieved for the query **\"{}\"**. ".format(query))
    md.append(f"Among {total_papers} papers, {len(high_relevance)} achieved high relevance scores (≥8). ")
    md.append("The following sections provide detailed analysis based on upstream rankings, ")
    md.append("paper abstracts, and arXiv export enrichment (introduction, **methodology**, conclusion, and recent citations).")
    md.append("This report **centers on methods and contributions** per paper and for the field.")
    md.append("")
    md.append("---")
    md.append("")
    
    # High-Relevance Papers
    md.append("## ⭐ High-Relevance Papers (Top Picks)")
    md.append("")
    
    for paper in high_relevance[:10]:
        arxiv_id = paper.get('arxiv_id', '')
        title = paper.get('title', 'Unknown')
        authors = paper.get('authors', [])
        score = get_paper_score(paper)
        contributions = paper.get('key_contributions', 'N/A')
        methods = paper.get('methods', 'N/A')
        
        # Get paper metadata
        paper_data = get_paper_by_id(papers, arxiv_id)
        abstract = paper_data.get('abstract', '')[:500] if paper_data else ''
        
        # Get enrichment
        enrich = enrichment_by_id.get(arxiv_id, {})
        intro = enrich.get('introduction_text', '')[:300]
        methodology = enrich.get('methodology_text', '')[:500]  # Longer excerpt for methodology
        conclusion = enrich.get('conclusion_text', '')[:300]
        recent_ids = enrich.get('related_arxiv_ids_recent', [])
        
        md.append(f"> **[{title}](https://arxiv.org/abs/{arxiv_id})**")
        md.append(f"> Relevance: {score}/10 | Authors: {', '.join(authors[:3])}{'...' if len(authors) > 3 else ''}")
        md.append(">")
        
        # Methods & Methodology (center of the report)
        combined_methods = methods if methods != 'N/A' else methodology
        if combined_methods and combined_methods != 'N/A':
            md.append(f"> **Methods & Methodology**: {combined_methods[:300]}...")
        md.append(">")
        
        # Contributions
        md.append(f"> **Contributions (Key Claims)**: {contributions}")
        md.append(">")
        
        # Abstract (supporting context)
        if abstract:
            md.append(f"> **Abstract** (supporting): {abstract}...")
            md.append(">")
        
        # Introduction (excerpt, supporting)
        if intro:
            md.append(f"> **Introduction (excerpt)**: {intro}...")
        # Conclusion (excerpt, supporting)
        if conclusion:
            md.append(f"> **Conclusion (excerpt)**: {conclusion}...")
        
        # Recent related arXiv ids
        if recent_ids:
            ids_str = ", ".join([f"[{rid}](https://arxiv.org/abs/{rid})" for rid in recent_ids[:5]])
            md.append(f"> **Recent related arXiv ids** (last 2 years): {ids_str}")
        
        md.append("")
    
    # Detailed Analysis
    md.append("---")
    md.append("")
    md.append("## Detailed Analysis by Category")
    md.append("")
    
    medium_papers = [p for p in ranked_papers if 5 <= get_paper_score(p) < 8]
    low_papers = [p for p in ranked_papers if get_paper_score(p) < 5]
    
    if medium_papers:
        md.append("### Medium Relevance Papers")
        for p in medium_papers[:5]:
            arxiv_id = p.get('arxiv_id', '')
            enrich = enrichment_by_id.get(arxiv_id, {})
            conclusion = enrich.get('conclusion_text', '')[:200]
            md.append(f"- **{p.get('title', 'Unknown')}** (ID: {arxiv_id}, Score: {p.get('relevance_score', 0)})")
            if conclusion:
                md.append(f"  - {conclusion}...")
    
    if low_papers:
        md.append("")
        md.append("### Lower Relevance Papers")
        for p in low_papers[:5]:
            md.append(f"- {p.get('title', 'Unknown')} (ID: {p.get('arxiv_id', '')}, Score: {get_paper_score(p):.1f})")
    
    # Comparison Table
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Comparison Table")
    md.append("")
    md.append("| Rank | Paper | Relevance | Key Methods | Main Contribution | Recent related ids |")
    md.append("|------|-------|-----------|-------------|-------------------|--------------------|")
    
    for p in ranked_papers[:15]:
        arxiv_id = p.get('arxiv_id', '')
        title = p.get('title', 'Unknown')[:40]
        score = p.get('relevance_score', 0)
        methods = str(p.get('methods', ''))[:25]
        contributions = str(p.get('key_contributions', ''))[:30]
        enrich = enrichment_by_id.get(arxiv_id, {})
        recent_ids = ", ".join(enrich.get('related_arxiv_ids_recent', [])[:3])
        
        md.append(f"| {p.get('rank', '-')} | {title}... | {score}/10 | {methods} | {contributions} | {recent_ids} |")
    
    md.append("")
    
    return "\n".join(md)


def display_report(top_n: int = 10):
    """Generate and display paper recommendation report directly to user (legacy mode)"""
    
    # Load data
    search_data = load_search_results()
    if not search_data:
        safe_print("\n[ERROR] No search results found. Please run paper-search first.")
        return

    analysis_data = load_analysis_results()
    if not analysis_data:
        safe_print("\n[ERROR] No analysis results found. Please run paper-analyze first.")
        return

    papers = search_data.get('papers', [])
    query = search_data.get('query', 'Unknown')
    total_results = search_data.get('total_results', len(papers))
    pagerank_scores = analysis_data.get('pagerank_scores', [])
    network_stats = analysis_data.get('network_stats', {})

    # Header
    safe_print("\n" + "=" * 70)
    safe_print("  PAPER RECOMMENDATION REPORT")
    safe_print("=" * 70)
    safe_print(f"  Query: {query}")
    safe_print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print("=" * 70)

    # Overview
    safe_print("\n📊 OVERVIEW")
    safe_print("-" * 40)
    safe_print(f"  Total Papers Found:  {total_results}")
    safe_print(f"  Papers Analyzed:     {len(papers)}")
    safe_print(f"  Network Nodes:       {network_stats.get('nodes', 'N/A')}")
    safe_print(f"  Network Edges:       {network_stats.get('edges', 'N/A')}")
    safe_print(f"  Network Density:     {network_stats.get('density', 'N/A')}")
    safe_print(f"  Clustering Coef:    {network_stats.get('avg_clustering', 'N/A')}")

    # Top Recommended Papers
    safe_print(f"\n🏆 TOP {top_n} RECOMMENDED PAPERS")
    safe_print("-" * 40)
    safe_print("  (Ranked by PageRank algorithm based on similarity network)")
    safe_print("-" * 40)

    for item in pagerank_scores[:top_n]:
        paper = get_paper_by_id(papers, item['arxiv_id'])
        if paper:
            title = paper.get('title', 'Unknown')
            authors = paper.get('authors', [])
            published = paper.get('published', '')[:10] if paper.get('published') else 'N/A'
            categories = paper.get('categories', [])[:2]
            pdf_url = paper.get('pdf_url', '')

            safe_print(f"\n  [{item['rank']}] {title}")
            safe_print(f"      ID:        {item['arxiv_id']}")
            safe_print(f"      Authors:   {', '.join(authors[:3])}{'...' if len(authors) > 3 else ''}")
            safe_print(f"      Date:      {published}")
            safe_print(f"      Categories: {', '.join(categories) if categories else 'N/A'}")
            safe_print(f"      Score:     {item['pagerank_score']:.4f} | Connections: {item['connections']}")
            safe_print(f"      PDF:       {pdf_url}")
            safe_print(f"      → Recommended: Rank #{item['rank']} with {item['connections']} similar papers")

    # Most Connected
    safe_print(f"\n\n🔗 MOST CONNECTED PAPERS")
    safe_print("-" * 40)
    sorted_by_connections = sorted(pagerank_scores, 
                                   key=lambda x: x['connections'], 
                                   reverse=True)[:5]
    for i, item in enumerate(sorted_by_connections, 1):
        paper = get_paper_by_id(papers, item['arxiv_id'])
        if paper:
            safe_print(f"  {i}. {item['arxiv_id']} - {paper.get('title', 'Unknown')[:50]}...")
            safe_print(f"     Connections: {item['connections']}")

    # Most Recent
    safe_print(f"\n\n📅 MOST RECENT PAPERS")
    safe_print("-" * 40)
    sorted_by_date = sorted(papers, 
                            key=lambda x: x.get('published', ''), 
                            reverse=True)[:5]
    for p in sorted_by_date:
        safe_print(f"  • {p.get('arxiv_id')} - {p.get('published', '')[:10]}")
        safe_print(f"    {p.get('title', 'Unknown')[:55]}...")

    # Footer
    safe_print("\n" + "=" * 70)
    safe_print("  Methodology: PageRank on TF-IDF similarity network")
    safe_print("  Weights: 80% text similarity + 20% same author bonus")
    safe_print("=" * 70)
    safe_print("")


def generate_full_report(enable_export_enrichment: bool = True):
    """
    Generate full research report (v1.1 mode) with arXiv export enrichment.
    Outputs: paper_abstracts.json, paper_export_enrichment.json, paper_reports.md
    """
    safe_print("\n[REPORT v1.2] Starting full report generation...")
    
    # Step 1: Load data
    search_data = load_search_results()
    if not search_data:
        safe_print("[ERROR] No search results found. Please run paper-search first.")
        return

    analysis_data = load_analysis_results()
    if not analysis_data:
        safe_print("[ERROR] No analysis results found. Please run paper-analyze first.")
        return

    papers = search_data.get('papers', [])
    # Support both "ranked_papers" and "pagerank_scores" naming conventions
    ranked_papers = analysis_data.get('ranked_papers') or analysis_data.get('pagerank_scores', [])
    
    safe_print(f"[STEP 1] Loaded {len(papers)} papers, {len(ranked_papers)} ranked")
    
    # Step 2: Extract abstracts
    abstracts = extract_abstracts(papers, ranked_papers)
    abstracts_path = os.path.join(get_data_dir(), "paper_abstracts.json")
    with open(abstracts_path, 'w', encoding='utf-8') as f:
        json.dump(abstracts, f, indent=2, ensure_ascii=False)
    safe_print(f"[STEP 2] Saved paper_abstracts.json ({len(abstracts['papers'])} papers)")
    
    # Step 3: Enrich via arXiv export
    if enable_export_enrichment:
        enrichment = enrich_with_exports(ranked_papers)
        enrichment_path = os.path.join(get_data_dir(), "paper_export_enrichment.json")
        with open(enrichment_path, 'w', encoding='utf-8') as f:
            json.dump(enrichment, f, indent=2, ensure_ascii=False)
        safe_print(f"[STEP 3] Saved paper_export_enrichment.json ({len(enrichment['papers'])} enriched)")
    else:
        enrichment = {"papers": []}
        safe_print("[STEP 3] Skipped export enrichment (disabled)")
    
    # Step 4: Generate report
    report_md = generate_report(search_data, analysis_data, abstracts, enrichment)
    report_path = os.path.join(get_data_dir(), "paper_reports.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
    safe_print(f"[STEP 4] Saved paper_reports.md")
    
    safe_print("\n✅ Full report generation complete!")
    safe_print(f"   Outputs in {get_data_dir()}/:")
    safe_print("   - paper_abstracts.json")
    if enable_export_enrichment:
        safe_print("   - paper_export_enrichment.json")
    safe_print("   - paper_reports.md")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate paper recommendation report (v1.2)')
    parser.add_argument('--top', '-t', type=int, default=10,
                       help='Number of top papers to display')
    parser.add_argument('--skip-enrich', dest='skip_enrich', action='store_true',
                       help='Skip arXiv export enrichment (faster, no network calls)')
    parser.add_argument('--full', '-f', action='store_true',
                       help='Generate full report with enrichment (outputs .json/.md files)')
    
    args = parser.parse_args()
    
    if args.full:
        generate_full_report(enable_export_enrichment=not args.skip_enrich)
    else:
        display_report(top_n=args.top)


if __name__ == "__main__":
    main()
