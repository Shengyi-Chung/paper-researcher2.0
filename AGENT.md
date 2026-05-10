---
name: paper-researcher-agent
description: "AI research paper assistant with arXiv search, network analysis, PageRank ranking, multi-turn conversational Q&A, and Markdown report generation. Four independently-testable skills wired together by JSON files in a shared data directory."
author: Shengyi-Chung
version: 2.0.0
tags:
  - arxiv
  - research
  - agent
  - pagerank
  - network-analysis
  - conversational-ai
  - report-generator
skills:
  - paper-search
  - paper-analyze
  - paper-report
  - query-holder
---

# Paper Researcher Agent v2.0

A four-skill AI agent that transforms a natural-language research query into ranked papers, network visualization, conversational Q&A, and structured reports. Skills communicate through JSON files in a shared `data/` directory, enabling independent testing and debugging.

## Skills

| # | Skill | Reads | Writes |
|---|---|---|---|
| 1 | `paper-search` | query parameters | `data/search_results.json`, `data/search_params.json` |
| 2 | `paper-analyze` | `data/search_results.json` | `data/analysis_results.json`, `data/citation_network.png` |
| 3 | `paper-report` | `data/{search,analysis}_results.json` | `data/research_report.md`, `data/report_data.json` |
| 4 | `query-holder` | `data/{search,analysis}_results.json`, `data/query_session.json` | `data/query_session.json` (updates) |

Each skill ships in `.claude/skills/<name>/` with its own `SKILL.md` (I/O contract, error-handling) and a Python entry point.

## Workflow

```
User Query (NL)
      │
      ▼
paper-search ──→ search_results.json ──→ paper-analyze ──→ analysis_results.json
                                     │                              │
                                     │                              ▼
                                     │                    similarity_network.png
                                     │                    
                                     │
                                     └──────────────────────┬─────────────────┐
                                                           │                 │
                                                           ▼                 ▼
                                                     paper-report      query-holder
                                                     (one-time)         (multi-turn)
                                                     ──────────          ─────────
                                                     research_report    Q&A answers
```

**Key features:**
- `paper-search` creates the initial data set
- `paper-analyze` runs network analysis and PageRank ranking
- `paper-report` generates one-time Markdown reports
- `query-holder` supports multi-turn conversational follow-ups with context tracking

## Composition Contracts

Two contracts make the pipeline composable:

1. **JSON-file-only interface.** Skills communicate by reading and writing structured JSON in the `data/` directory.
2. **Shared data directory.** All skills read from `/data/` for papers, analysis results, and session state.

## End-to-end Invocation

### Natural language (recommended)

```
我想要寻找最近有关 attention 的论文
排行第一的论文的主要方法是什么？
帮我生成一份报告
```

The agent chains skills automatically based on intent.

### Per-skill slash commands

```
/paper-search attention
/paper-analyze -v
/paper-report
/query-holder 排行第一的论文的主要方法
```

### Direct script invocation

```bash
# 1. Search papers
python .claude/skills/paper-search/paper_search.py -q "attention" -m 20

# 2. Analyze papers (with visualization)
python .claude/skills/paper-analyze/paper_analyze.py -v

# 3. Generate report
python .claude/skills/paper-report/paper_report.py

# 4. Conversational Q&A
python .claude/skills/paper-qa/query_holder.py -q "排行第一的论文的主要方法"
```

## Input / Output Specifications

### Agent Input

| field | type | required | description |
|---|---|---|---|
| `query` | string | yes | Natural language research query |
| `max_results` | int | no | Max papers to retrieve (default: 20) |
| `sort_by` | string | no | `relevance`, `submittedDate`, `lastUpdatedDate` |

### Agent Output

| artifact | description |
|---|---|
| `data/search_results.json` | Raw papers from arXiv |
| `data/analysis_results.json` | PageRank scores and network metrics |
| `data/citation_network.png` | Network visualization graph |
| `data/research_report.md` | Markdown briefing report |
| `data/query_session.json` | Conversational context state |

## Query Types (query-holder)

| Type | Trigger | Example |
|---|---|---|
| `paper_detail` | "tell me more about X" | "tell me more about Cubit" |
| `comparison` | "compare A and B" | "compare Cubit and SoftSAE" |
| `author_search` | "papers by X" | "papers by Chuanyang Zheng" |
| `keyword_filter` | "papers about X" | "papers about transformer" |
| `followup_reference` | "it", "this paper" | "what methods does it use?" |

## Dependencies

- Python ≥ 3.9
- PyPI packages: `arxiv`, `networkx`, `matplotlib`, `scikit-learn`

```bash
pip install arxiv networkx matplotlib scikit-learn
```

## Project Structure

```
paper-researcher2.0/
├── data/                        # Shared data directory
│   ├── search_results.json      # Paper search results
│   ├── analysis_results.json    # PageRank analysis
│   ├── search_params.json      # Search parameters
│   ├── query_session.json      # Conversational state
│   ├── research_report.md      # Generated report
│   └── citation_network.png    # Network visualization
├── .claude/
│   └── skills/
│       ├── paper-search/       # arXiv paper retrieval
│       ├── paper-analyze/      # Network analysis + PageRank
│       ├── paper-report/       # Report generation
│       └── paper-qa/          # Conversational Q&A
│           ├── query_holder.py
│           ├── keyword_expander.py
│           └── query_session_manager.py
└── AGENT.md                    # This file
```

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `sim_weight` | 5.0 | Similarity score weight |
| `author_weight` | 0.2 | Same-author bonus weight |
| `threshold` | 0.3 | Network edge threshold |
| `top_n` | 15 | Papers in report |

## Usage Examples

### Full pipeline

```python
# Search for transformer papers
python .claude/skills/paper-search/paper_search.py -q "transformer" -m 20

# Analyze with visualization
python .claude/skills/paper-analyze/paper_analyze.py -v

# Generate report
python .claude/skills/paper-report/paper_report.py
```

### Conversational workflow

```bash
# Ask about top paper
python .claude/skills/paper-qa/query_holder.py -q "tell me more about rank 1"

# Compare papers
python .claude/skills/paper-qa/query_holder.py -q "compare Cubit and SoftSAE"

# Author search
python .claude/skills/paper-qa/query_holder.py -q "papers by Chuanyang Zheng"

# Follow-up (context-aware)
python .claude/skills/paper-qa/query_holder.py -q "what methods does it use?"

# View session state
python .claude/skills/paper-qa/query_holder.py --session
```

## Session Features (query-holder)

- **Multi-turn context tracking**: Remembers discussed papers
- **Reference resolution**: Understands "it", "this paper", "second one"
- **Paper aliases**: Registers custom names for papers
- **Comparison state**: Maintains active comparison pairs
- **Keyword history**: Tracks active search keywords

## Evaluation Metrics

| Metric | Description |
|---|---|
| Retrieval accuracy | Correct paper retrieval |
| PageRank quality | Importance ranking relevance |
| Network coherence | Connected papers similarity |
| Response quality | Concise contextual answers |
| Context coherence | Proper follow-up understanding |
