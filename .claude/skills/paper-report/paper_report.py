#!/usr/bin/env python3
"""
paper-report: Generate and display paper recommendation reports
"""

import io
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional


def get_data_dir() -> str:
    """Get path to data directory"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data"
    )


def load_search_results() -> Optional[Dict]:
    """Load search results from JSON file"""
    filepath = os.path.join(get_data_dir(), "search_results.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_analysis_results() -> Optional[Dict]:
    """Load analysis results from JSON file"""
    filepath = os.path.join(get_data_dir(), "analysis_results.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


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


def display_report(top_n: int = 10):
    """Generate and display paper recommendation report directly to user"""
    
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


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate paper recommendation report')
    parser.add_argument('--top', '-t', type=int, default=10,
                       help='Number of top papers to display')
    
    args = parser.parse_args()
    display_report(top_n=args.top)


if __name__ == "__main__":
    main()
