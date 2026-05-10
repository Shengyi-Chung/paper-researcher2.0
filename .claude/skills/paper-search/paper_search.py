#!/usr/bin/env python3
"""
paper-search: Search arXiv papers and extract metadata
"""

import requests
import xml.etree.ElementTree as ET
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace"""
    if not text:
        return ""
    # Replace newlines with spaces and collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def search_papers(query: str, max_results: int = 20, 
                  sort_by: str = "submittedDate",
                  sort_order: str = "descending") -> Dict:
    """
    Search arXiv for papers matching the query.
    
    Args:
        query: Search keywords
        max_results: Maximum number of results (default: 20)
        sort_by: Sort by 'submittedDate' or 'relevance'
        sort_order: 'descending' or 'ascending'
    
    Returns:
        Dict with search metadata and papers list
    """
    import urllib.parse
    
    # Encode query for URL
    encoded_query = urllib.parse.quote(query)
    
    # Build API URL
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={encoded_query}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy={sort_by}"
        f"&sortOrder={sort_order}"
    )
    
    print(f"Searching arXiv for: '{query}'")
    print(f"URL: {url[:100]}...")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return {
            "query": query,
            "search_time": datetime.now().isoformat(),
            "total_results": 0,
            "papers": [],
            "error": str(e)
        }
    
    # Parse XML response
    papers = parse_arxiv_response(response.text)
    
    # Build result
    result = {
        "query": query,
        "search_time": datetime.now().isoformat(),
        "total_results": len(papers),
        "max_results_requested": max_results,
        "sort_by": sort_by,
        "papers": papers
    }
    
    print(f"Found {len(papers)} papers")
    
    return result


def parse_arxiv_response(xml_text: str) -> List[Dict]:
    """Parse arXiv API XML response into paper list"""
    
    root = ET.fromstring(xml_text)
    
    # Define namespace
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    
    papers = []
    
    for entry in root.findall('atom:entry', ns):
        try:
            # Basic info
            paper_id = entry.find('atom:id', ns).text
            if paper_id:
                paper_id = paper_id.split('/')[-1]
            
            title = clean_text(entry.find('atom:title', ns).text)
            summary = clean_text(entry.find('atom:summary', ns).text)
            
            # Dates
            published = entry.find('atom:published', ns).text[:10] if entry.find('atom:published', ns) is not None else None
            updated = entry.find('atom:updated', ns).text[:10] if entry.find('atom:updated', ns) is not None else None
            
            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text)
            
            # Categories
            categories = []
            for cat in entry.findall('atom:category', ns):
                cat_term = cat.get('term')
                if cat_term:
                    categories.append(cat_term)
            
            # Primary category
            primary_cat_elem = entry.find('arxiv:primary_category', ns)
            primary_category = primary_cat_elem.get('term') if primary_cat_elem is not None else None
            
            # DOI
            doi_elem = entry.find('arxiv:doi', ns)
            doi = doi_elem.text if doi_elem is not None and doi_elem.text else None
            
            # Links
            pdf_url = None
            abstract_url = None
            for link in entry.findall('atom:link', ns):
                href = link.get('href', '')
                rel = link.get('rel', '')
                link_title = link.get('title', '')
                link_type = link.get('type', '')
                
                if 'pdf' in link_title.lower() or link_type == 'application/pdf':
                    pdf_url = href
                elif rel == 'alternate':
                    abstract_url = href
                elif 'arxiv.org/abs' in href:
                    abstract_url = href
                elif 'arxiv.org/pdf' in href and not pdf_url:
                    pdf_url = href
            
            # Comments
            comment_elem = entry.find('arxiv:comment', ns)
            comments = comment_elem.text if comment_elem is not None and comment_elem.text else None
            
            # Journal ref
            journal_elem = entry.find('arxiv:journal_ref', ns)
            journal_ref = journal_elem.text if journal_elem is not None and journal_elem.text else None
            
            paper = {
                "arxiv_id": paper_id,
                "title": title,
                "abstract": summary,
                "authors": authors,
                "author_count": len(authors),
                "published": published,
                "updated": updated,
                "categories": categories,
                "primary_category": primary_category,
                "doi": doi,
                "pdf_url": pdf_url,
                "abstract_url": abstract_url,
                "comments": comments,
                "journal_ref": journal_ref
            }
            
            papers.append(paper)
            
        except Exception as e:
            print(f"Error parsing entry: {e}")
            continue
    
    return papers


def get_shared_data_dir() -> str:
    """Get the path to the shared data directory"""
    # Navigate: paper-search/ -> skills/ -> .claude/ -> project_root/ -> data/
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data"
    )


def save_results(result: Dict, output_dir: str = None) -> str:
    """Save search results to JSON file"""
    
    if output_dir is None:
        output_dir = get_shared_data_dir()
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save main results
    results_path = os.path.join(output_dir, "papers.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Save params for reference
    params = {
        "query": result["query"],
        "search_time": result["search_time"],
        "total_results": result["total_results"],
        "source": "arXiv API"
    }
    params_path = os.path.join(output_dir, "search_params.json")
    with open(params_path, 'w', encoding='utf-8') as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to {results_path}")
    return results_path


def load_search_results(filepath: str = None) -> Optional[Dict]:
    """Load search results from JSON file
    
    Args:
        filepath: Path to results file. If None, loads from shared location.
    
    Returns:
        Dict with search results or None if file doesn't exist
    """
    if filepath is None:
        filepath = os.path.join(get_shared_data_dir(), "search_results.json")
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Search arXiv for papers')
    parser.add_argument('--query', '-q', type=str, required=True,
                       help='Search query/keywords')
    parser.add_argument('--max', '-m', type=int, default=20,
                       help='Maximum results (default: 20)')
    parser.add_argument('--sort', '-s', type=str, default='submittedDate',
                       choices=['submittedDate', 'relevance', 'lastUpdatedDate'],
                       help='Sort by (default: submittedDate)')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Output directory (default: shared data folder)')
    
    args = parser.parse_args()
    
    # Search
    result = search_papers(args.query, max_results=args.max, sort_by=args.sort)
    
    # Save
    if result["papers"]:
        save_results(result, args.output)
        
        # Print summary
        print("\n" + "=" * 60)
        print("SEARCH RESULTS SUMMARY")
        print("=" * 60)
        print(f"Query: {result['query']}")
        print(f"Found: {result['total_results']} papers")
        print()
        for i, paper in enumerate(result['papers'][:5], 1):
            print(f"{i}. {paper['title'][:60]}...")
            print(f"   Authors: {', '.join(paper['authors'][:3])}...")
            print(f"   Date: {paper['published']}")
            print()
        if len(result['papers']) > 5:
            print(f"... and {len(result['papers']) - 5} more papers")
    else:
        print("\nNo papers found. Try different keywords.")


if __name__ == "__main__":
    main()
