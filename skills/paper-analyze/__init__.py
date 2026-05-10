"""
paper-analyze: Paper similarity analysis and ranking skill

Functions:
- load_search_results(): Load papers from shared data directory
- extract_paper_texts(): Extract title/abstract for analysis
- calculate_similarity_matrix(): TF-IDF cosine similarity
- calculate_score_matrix(): Combined score with author bonus
- build_paper_network(): NetworkX graph construction
- calculate_pagerank(): PageRank ranking
- analyze_papers(): Main analysis pipeline
"""

from .paper_analyze import (
    load_search_results,
    extract_paper_texts,
    calculate_similarity_matrix,
    calculate_score_matrix,
    build_paper_network,
    calculate_pagerank,
    analyze_papers,
    print_results,
    get_shared_data_dir
)

__all__ = [
    'load_search_results',
    'extract_paper_texts',
    'calculate_similarity_matrix',
    'calculate_score_matrix',
    'build_paper_network',
    'calculate_pagerank',
    'analyze_papers',
    'print_results',
    'get_shared_data_dir'
]
