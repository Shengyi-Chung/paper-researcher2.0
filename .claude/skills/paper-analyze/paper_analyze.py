#!/usr/bin/env python3
"""
paper-analyze: Analyze papers from search results, build similarity network,
and rank papers using PageRank.
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Font settings for visualization
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def get_shared_data_dir() -> str:
    """Get the path to the shared data directory"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data"
    )


def load_search_results() -> Optional[Dict]:
    """Load search results from shared data directory"""
    filepath = os.path.join(get_shared_data_dir(), "search_results.json")
    
    if not os.path.exists(filepath):
        safe_print(f"Error: Search results not found at {filepath}")
        safe_print("Please run paper-search first to get paper data.")
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_paper_texts(papers: List[Dict]) -> List[Dict]:
    """Extract title and abstract from papers for analysis"""
    paper_texts = []
    for paper in papers:
        # Combine title and abstract for better representation
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        paper_texts.append({
            'arxiv_id': paper.get('arxiv_id', ''),
            'title': paper.get('title', ''),
            'abstract': paper.get('abstract', ''),
            'authors': paper.get('authors', []),
            'published': paper.get('published', ''),
            'text': text
        })
    return paper_texts


def calculate_similarity_matrix(paper_texts: List[Dict]) -> np.ndarray:
    """Calculate TF-IDF based similarity matrix between papers"""
    if not paper_texts:
        return np.array([])
    
    # Extract text content
    texts = [p['text'] for p in paper_texts]
    
    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 2)
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # Cosine similarity
    similarity_matrix = cosine_similarity(tfidf_matrix)
    
    return similarity_matrix


def get_common_authors(authors1: List[str], authors2: List[str]) -> bool:
    """Check if two papers share any common authors"""
    if not authors1 or not authors2:
        return False
    
    # Normalize author names for comparison
    set1 = set(author.lower().strip() for author in authors1)
    set2 = set(author.lower().strip() for author in authors2)
    
    return bool(set1 & set2)


def calculate_score_matrix(similarity_matrix: np.ndarray, 
                           paper_texts: List[Dict],
                           sim_weight: float = 5.0,
                           author_weight: float = 0.2) -> np.ndarray:
    """Calculate combined score matrix"""
    n = similarity_matrix.shape[0]
    score_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):  # Only upper triangle
            sim = similarity_matrix[i, j]
            same_author = 1.0 if get_common_authors(
                paper_texts[i]['authors'], 
                paper_texts[j]['authors']
            ) else 0.0
            
            # Score = 5.0 * similarity + 0.2 * same_author
            score = 5.0 * sim + 0.2 * same_author
            
            score_matrix[i, j] = score
            score_matrix[j, i] = score  # Symmetric
    
    return score_matrix


def build_paper_network(score_matrix: np.ndarray, 
                        paper_texts: List[Dict],
                        threshold: float = 0.05) -> nx.Graph:
    """Build network graph from score matrix"""
    G = nx.Graph()
    
    # Add nodes
    for paper in paper_texts:
        G.add_node(paper['arxiv_id'], 
                   title=paper['title'],
                   authors=paper['authors'],
                   published=paper['published'])
    
    # Add edges where score exceeds threshold
    n = score_matrix.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            if score_matrix[i, j] >= threshold:
                G.add_edge(
                    paper_texts[i]['arxiv_id'],
                    paper_texts[j]['arxiv_id'],
                    weight=score_matrix[i, j]
                )
    
    return G


def calculate_pagerank(G: nx.Graph) -> Dict[str, float]:
    """Calculate PageRank scores for papers"""
    if G.number_of_nodes() == 0:
        return {}
    
    try:
        pagerank = nx.pagerank(G, alpha=0.85)
        return pagerank
    except Exception as e:
        safe_print(f"Warning: PageRank calculation failed: {e}")
        # Fallback to equal weights
        return {node: 1.0 / G.number_of_nodes() for node in G.nodes()}


def analyze_papers(sim_weight: float = 0.8,
                   author_weight: float = 0.2,
                   threshold: float = 0.05) -> Dict:
    """
    Main analysis function.
    
    Args:
        sim_weight: Weight for similarity score (default: 0.8)
        author_weight: Weight for same-author bonus (default: 0.2)
        threshold: Minimum score to create edge (default: 0.3)
    
    Returns:
        Analysis results dictionary
    """
    safe_print("=" * 60)
    safe_print("PAPER ANALYZER")
    safe_print("=" * 60)
    
    # Load search results
    safe_print("\n[1/6] Loading search results...")
    data = load_search_results()
    if not data:
        return {"error": "No search results found"}
    
    papers = data.get('papers', [])
    if not papers:
        return {"error": "No papers in search results"}
    
    safe_print(f"    Loaded {len(papers)} papers")
    
    # Extract paper texts
    safe_print("\n[2/6] Extracting paper texts...")
    paper_texts = extract_paper_texts(papers)
    safe_print(f"    Extracted {len(paper_texts)} paper texts")
    
    # Calculate similarity matrix
    safe_print("\n[3/6] Calculating similarity matrix...")
    similarity_matrix = calculate_similarity_matrix(paper_texts)
    safe_print(f"    Similarity matrix shape: {similarity_matrix.shape}")
    
    # Calculate combined score matrix
    # Score = 5.0 * similarity + 0.2 * same_author
    safe_print("\n[4/6] Calculating combined scores...")
    safe_print(f"    Formula: score = 5.0 * similarity + 0.2 * same_author")
    score_matrix = calculate_score_matrix(
        similarity_matrix, paper_texts, sim_weight, author_weight
    )
    
    # Build network
    safe_print(f"\n[5/6] Building paper network (threshold={threshold})...")
    G = build_paper_network(score_matrix, paper_texts, threshold)
    safe_print(f"    Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Calculate PageRank
    safe_print("\n[6/6] Calculating PageRank scores...")
    pagerank_scores = calculate_pagerank(G)
    
    # Rank papers
    ranked_papers = sorted(
        pagerank_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Build results
    results = []
    for rank, (arxiv_id, score) in enumerate(ranked_papers, 1):
        node_data = G.nodes[arxiv_id]
        connections = len(list(G.neighbors(arxiv_id)))
        
        results.append({
            'rank': rank,
            'arxiv_id': arxiv_id,
            'title': node_data.get('title', ''),
            'authors': node_data.get('authors', []),
            'published': node_data.get('published', ''),
            'pagerank_score': round(score, 6),
            'connections': connections
        })
    
    # Calculate network statistics
    network_stats = {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
    }
    
    if G.number_of_edges() > 0:
        try:
            network_stats['avg_clustering'] = round(nx.average_clustering(G), 4)
            network_stats['density'] = round(nx.density(G), 4)
        except:
            network_stats['avg_clustering'] = None
            network_stats['density'] = None
    
    # Save results
    output = {
        'analysis_time': datetime.now().isoformat(),
        'query': data.get('query', ''),
        'total_papers': len(papers),
        'weights': {
            'similarity': sim_weight,
            'same_author': author_weight
        },
        'threshold': threshold,
        'pagerank_scores': results,
        'network_stats': network_stats
    }
    
    # Save to shared data directory
    output_dir = get_shared_data_dir()
    output_path = os.path.join(output_dir, 'analysis_results.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    return output


def safe_print(text: str):
    """Print text with proper encoding handling"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace problematic characters with ASCII replacements
        import unicodedata
        ascii_text = unicodedata.normalize('NFKD', text).encode('ascii', errors='replace').decode('ascii')
        print(ascii_text)


def print_results(results: Dict):
    """Print analysis results in formatted output"""
    if 'error' in results:
        safe_print(f"\nError: {results['error']}")
        return
    
    safe_print("\n" + "=" * 70)
    safe_print("PAPER ANALYSIS RESULTS")
    safe_print("=" * 70)
    
    safe_print(f"\nQuery: {results.get('query', 'N/A')}")
    safe_print(f"Total Papers Analyzed: {results.get('total_papers', 0)}")
    safe_print(f"Weights: similarity={results['weights']['similarity']}, "
          f"same_author={results['weights']['same_author']}")
    safe_print(f"Edge Threshold: {results.get('threshold', 0.05)}")
    
    safe_print(f"\n{'='*70}")
    safe_print("PAGE RANK RANKING")
    safe_print("="*70)
    
    scores = results.get('pagerank_scores', [])
    if not scores:
        safe_print("No papers ranked.")
        return
    
    safe_print(f"\n{'Rank':<5} {'Paper ID':<15} {'Score':<10} {'Connections':<12} {'Title'}")
    safe_print("-" * 70)
    
    for item in scores[:15]:  # Show top 15
        title = item['title'][:40] + "..." if len(item['title']) > 40 else item['title']
        safe_print(f"{item['rank']:<5} {item['arxiv_id']:<15} {item['pagerank_score']:<10.6f} "
              f"{item['connections']:<12} {title}")
    
    if len(scores) > 15:
        safe_print(f"\n... and {len(scores) - 15} more papers")
    
    safe_print(f"\n{'='*70}")
    safe_print("NETWORK STATISTICS")
    safe_print("="*70)
    stats = results.get('network_stats', {})
    safe_print(f"Nodes (Papers): {stats.get('nodes', 0)}")
    safe_print(f"Edges (Connections): {stats.get('edges', 0)}")
    if stats.get('avg_clustering') is not None:
        safe_print(f"Avg Clustering Coefficient: {stats['avg_clustering']}")
    if stats.get('density') is not None:
        safe_print(f"Network Density: {stats['density']}")


def visualize_network(G: nx.Graph, output_path: str = None):
    """Visualize the paper similarity network"""
    if G.number_of_nodes() == 0:
        safe_print("No nodes in graph to visualize!")
        return
    
    safe_print("\nGenerating network visualization...")
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Calculate PageRank for node sizes
    pagerank = nx.pagerank(G, alpha=0.85)
    node_sizes = [300 + pagerank[node] * 4000 for node in G.nodes()]
    
    # Calculate node degrees
    degrees = dict(G.degree())
    
    # Node color based on degree
    node_colors = [degrees[node] for node in G.nodes()]
    
    # Use spring layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Draw edges
    edges = G.edges(data=True)
    edge_weights = [e[2].get('weight', 0.5) for e in edges]
    edge_widths = [0.5 + w * 3 for w in edge_weights]
    
    nx.draw_networkx_edges(G, pos,
                           alpha=0.4,
                           width=edge_widths,
                           edge_color='gray',
                           ax=ax)
    
    # Draw nodes
    nodes = nx.draw_networkx_nodes(G, pos,
                                   node_size=node_sizes,
                                   node_color=node_colors,
                                   cmap=plt.cm.YlOrRd,
                                   alpha=0.9,
                                   ax=ax)
    
    # Add colorbar
    plt.colorbar(nodes, ax=ax, label='Degree (Connections)', shrink=0.6)
    
    # Draw labels - using arxiv_id
    labels = {node: node.replace('v1', '') for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', ax=ax)
    
    # Title and statistics
    stats_text = f"Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()} | "
    stats_text += f"Density: {nx.density(G):.3f} | Clustering: {nx.average_clustering(G):.3f}"
    
    ax.set_title(f"Paper Similarity Network\n{stats_text}", fontsize=14, fontweight='bold')
    ax.axis('off')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        safe_print(f"Graph saved to: {output_path}")
    
    plt.show()
    safe_print("Network visualization complete!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze papers and rank by importance')
    parser.add_argument('--sim-weight', '-s', type=float, default=0.8,
                       help='Weight for similarity score (default: 0.8)')
    parser.add_argument('--author-weight', '-a', type=float, default=0.2,
                       help='Weight for same-author bonus (default: 0.2)')
    parser.add_argument('--threshold', '-t', type=float, default=0.3,
                       help='Minimum score for edge (default: 0.05)')
    parser.add_argument('--top', type=int, default=None,
                       help='Show only top N papers')
    parser.add_argument('--visualize', '-v', action='store_true',
                       help='Generate network visualization')
    
    args = parser.parse_args()
    
    # Run analysis
    results = analyze_papers(
        sim_weight=args.sim_weight,
        author_weight=args.author_weight,
        threshold=args.threshold
    )
    
    # Print results
    print_results(results)
    
    # Show top N if specified
    if args.top and 'pagerank_scores' in results:
        safe_print(f"\n{'='*70}")
        safe_print(f"TOP {args.top} PAPERS - DETAILED VIEW")
        safe_print("="*70)
        
        for item in results['pagerank_scores'][:args.top]:
            safe_print(f"\n#{item['rank']}: {item['title']}")
            safe_print(f"    ID: {item['arxiv_id']}")
            safe_print(f"    Authors: {', '.join(item['authors'][:5])}")
            if len(item['authors']) > 5:
                safe_print(f"             ... and {len(item['authors']) - 5} more")
            safe_print(f"    Published: {item['published']}")
            safe_print(f"    PageRank Score: {item['pagerank_score']:.6f}")
            safe_print(f"    Connections: {item['connections']}")
    
    # Visualize if requested
    if args.visualize:
        # Rebuild network for visualization
        data = load_search_results()
        if data:
            papers = data.get('papers', [])
            paper_texts = extract_paper_texts(papers)
            similarity_matrix = calculate_similarity_matrix(paper_texts)
            score_matrix = calculate_score_matrix(
                similarity_matrix, paper_texts, 
                args.sim_weight, args.author_weight
            )
            G = build_paper_network(score_matrix, paper_texts, args.threshold)
            
            output_dir = get_shared_data_dir()
            output_path = os.path.join(output_dir, 'similarity_network.png')
            visualize_network(G, output_path)


if __name__ == "__main__":
    main()
