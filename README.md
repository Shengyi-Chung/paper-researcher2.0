# Paper Researcher 2.0

> AI-powered academic paper research assistant using PageRank-based network analysis

---

## Overview

Paper Researcher 2.0 transforms research queries into ranked papers through **similarity network analysis** and **PageRank ranking**. Unlike traditional keyword matching, this agent identifies influential papers by analyzing the relationship structure between papers.

---

## Quick Start

```bash
# Install dependencies
pip install "arxiv>=2.0" "networkx>=3.0"

# One-liner: search + analyze + report
python .claude/skills/paper-search/paper_search.py -q "NLP" -m 20
python .claude/skills/paper-analyze/paper_analyze.py -v
python .claude/skills/paper-report/paper_report.py
```

### Command Reference

| Command | Function |
|---------|----------|
| `-q <query>` | Search keywords |
| `-m <n>` | Max results (default: 20) |
| `-s <field>` | Sort by: submittedDate, relevance |
| `-v` | Verbose output |

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ paper-search│────▶│ paper-analyze│────▶│ paper-report    │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐       ┌─────────────────┐
                    │query-holder  │       │ similarity.png   │
                    │(multi-turn)  │       └─────────────────┘
                    └──────────────┘
```

### Data Flow

1. **paper-search** fetches papers from arXiv API
2. **paper-analyze** computes TF-IDF similarity and PageRank
3. **paper-report** generates ranked research briefing
4. **query-holder** enables conversational follow-ups

---

## Core Algorithm

### Similarity Scoring

```
edge_weight(i,j) = 5.0 × cosine_sim(abstract_i, abstract_j) 
                   + 0.2 × same_author(i,j)
```

- **TF-IDF cosine similarity**: Measures content overlap between abstracts
- **Author bonus**: +0.2 for shared authors (fosters collaboration clusters)

### PageRank Ranking

PageRank treats the similarity network as a citation graph:
- Papers with many similar papers rank higher
- Papers connected to highly-ranked papers inherit influence
- Edge threshold (0.3) filters weak connections

### Network Metrics

| Metric | Description |
|--------|-------------|
| `nodes` | Number of papers |
| `edges` | Number of similarity connections |
| `density` | Edge density (0-1) |
| `clustering` | Avg clustering coefficient |

---

## Project Structure

```
paper-researcher2.0/
├── README.md
├── AGENT.md
│
├── .claude/skills/
│   ├── paper-search/         # arXiv API integration
│   │   └── paper_search.py
│   ├── paper-analyze/        # Network + PageRank
│   │   └── paper_analyze.py
│   ├── paper-report/          # Report generation
│   │   └── paper_report.py
│   └── paper-qa/             # Q&A engine
│       ├── query_holder.py
│       ├── keyword_expander.py
│       └── query_session_manager.py
│
└── data/
    ├── papers.json            # Raw search results
    ├── paper_analysis.json   # PageRank scores
    ├── similarity_network.png # Visualization
    ├── paper_reports.md      # Generated report
    └── query_session.json    # Q&A session state
```

---

## Usage Examples

### Search & Analyze

```bash
# Search for transformer papers
python .claude/skills/paper-search/paper_search.py \
    -q "transformer architecture" -m 20 -s submittedDate

# Analyze + generate network visualization
python .claude/skills/paper-analyze/paper_analyze.py -v

# Generate report
python .claude/skills/paper-report/paper_report.py
```

### Conversational Q&A

```bash
# Ask about top-ranked paper
python .claude/skills/paper-qa/query_holder.py \
    -q "tell me more about rank 1"

# Compare two papers
python .claude/skills/paper-qa/query_holder.py \
    -q "compare paper A and paper B"

# Follow-up with context
python .claude/skills/paper-qa/query_holder.py \
    -q "what datasets does it use?"

# View session state
python .claude/skills/paper-qa/query_holder.py --session
```

---

## Q&A Query Types

| Type | Pattern | Example |
|------|---------|---------|
| `detail` | "tell me about X" | "tell me more about UniPool" |
| `compare` | "compare A and B" | "compare Cubit and SoftSAE" |
| `author` | "papers by X" | "papers by Chuanyang Zheng" |
| `keyword` | "what about X?" | "what methods are used?" |
| `followup` | pronouns | "it uses what dataset?" |

Session features: context tracking, pronoun resolution ("it", "this paper"), paper aliases, multi-turn memory.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `arxiv` | ≥2.0 | arXiv API client |
| `networkx` | ≥3.0 | Graph + PageRank |
| `matplotlib` | any | Network visualization |
| `scikit-learn` | any | TF-IDF vectorizer |

Install: `pip install arxiv networkx matplotlib scikit-learn`

---

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sim_weight` | 5.0 | Similarity score weight |
| `author_weight` | 0.2 | Same-author bonus |
| `threshold` | 0.3 | Network edge threshold |
| `top_n` | 15 | Papers in report |

---

## Output Files

| File | Content |
|------|---------|
| `papers.json` | Raw arXiv response |
| `paper_analysis.json` | PageRank scores + rankings |
| `similarity_network.png` | Network graph visualization |
| `paper_reports.md` | Markdown research briefing |
| `query_session.json` | Q&A conversation state |

---

## Author

Paper Researcher 2.0 — CodeBuddy
