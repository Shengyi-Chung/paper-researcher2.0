---
name: paper-analyze
description: "Analyze paper similarity, build relationship networks, and rank papers by PageRank importance. Uses TF-IDF cosine similarity and shared author overlap to construct similarity networks. Triggers: '分析论文', '构建网络', 'compute pagerank', 'build network'"
author: Shengyi-Chung
version: 1.0.0
tags:
  - network-analysis
  - pagerank
  - similarity
  - paper-analysis
  - graph
---

# Paper Analyzer Skill

## Core Capabilities

Analyze paper similarity, build relationship networks, and rank papers by importance based on search results.

## Input

Read paper list from `data/search_results.json`.

## Workflow

### 1. Paper Data Extraction
Extract from JSON for each paper:
- `title` - Paper title
- `abstract` - Abstract text
- `authors` - Author list

### 2. Similarity Calculation
Use TF-IDF vectorization + cosine similarity to compute pairwise paper similarity:
```
similarity = cosine_similarity(tfidf(abstract1), tfidf(abstract2))
```

### 3. Combined Score Calculation
```
score = 0.8 * similarity + 0.2 * same_author_flag
```
Where `same_author_flag = 1` if two papers share common authors, otherwise `0`.

### 4. Network Graph Construction
- Nodes: Papers (using arxiv_id as identifier)
- Edges: Paper pairs with score > threshold (e.g., 0.3)
- Edge weight: Combined score value

### 5. PageRank Ranking
Use NetworkX pagerank algorithm to rank papers by importance.

### 6. Output Results
Generate ranked paper list with:
- Paper info (title, authors, date)
- PageRank score
- Main connected papers

## Output Format

```json
{
  "analysis_time": "ISO timestamp",
  "total_papers": number,
  "pagerank_scores": [
    {
      "rank": 1,
      "arxiv_id": "xxx",
      "title": "Title",
      "authors": ["Author list"],
      "pagerank_score": 0.xxx,
      "connections": number of connections
    }
  ],
  "network_stats": {
    "nodes": node count,
    "edges": edge count,
    "avg_clustering": average clustering coefficient
  }
}
```

## Tech Stack

- scikit-learn: TF-IDF vectorization
- networkx: Network graph and PageRank
- numpy: Numerical computation
