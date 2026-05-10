# Paper Researcher 2.0

A four-skill agent that, given a natural-language research query (English or Chinese), searches arXiv, builds a paper similarity network, computes PageRank to rank results, and provides multi-turn Q&A with context tracking.

---

## Table of contents

- [Paper Researcher 2.0](#paper-researcher-20)
  - [Table of contents](#table-of-contents)
  - [What the agent does](#what-the-agent-does)
  - [Workflow: a 4-skill pipeline](#workflow-a-4-skill-pipeline)
  - [Directory structure](#directory-structure)
  - [Quick start](#quick-start)
    - [Prerequisites](#prerequisites)
    - [Option A — natural language end-to-end (recommended)](#option-a--natural-language-end-to-end-recommended)
    - [Option B — per-skill slash commands (explicit control)](#option-b--per-skill-slash-commands-explicit-control)
    - [Option C — run the scripts directly (outside Claude Code)](#option-c--run-the-scripts-directly-outside-claude-code)
  - [Skills](#skills)
    - [1. `paper-search` — arXiv retrieval](#1-paper-search--arxiv-retrieval)
    - [2. `paper-analyze` — similarity network analysis](#2-paper-analyze--similarity-network-analysis)
    - [3. `paper-report` — research briefing](#3-paper-report--research-briefing)
    - [4. `query-holder` — multi-turn Q&A](#4-query-holder--multi-turn-qa)
    - [Default I/O behavior every skill MUST implement](#default-io-behavior-every-skill-must-implement)
  - [Score formula](#score-formula)
  - [Session features](#session-features)
  - [Contributions](#contributions)

---

## What the agent does

Type a natural-language request such as

> *"为我寻找近两年有关 attention 的论文，重点关注 Transformer 架构"*

or

> *"find recent papers on diffusion models for medical imaging from the last 6 months"*

and the agent will:

1. Parse the request into a structured `search_results.json` (containing search terms, date range, arXiv categories, max_results).
2. Hit the arXiv API, deduplicate, and cache the response.
3. Build a paper similarity network based on content (abstracts) and author overlap.
4. **Compute PageRank scores to identify the most influential papers** (this is the core ranking).
5. Render a Markdown research briefing with PageRank-ranked papers.
6. Answer follow-up questions (*"tell me more about rank 1"*, *"compare paper A vs B"*, *"what methods does it use?"*) with multi-turn context tracking.

The whole run is cached on disk under `data/`, so the briefing is fully reproducible and the Q&A is grounded.

---

## Workflow: a 4-skill pipeline

```
paper-search ──→ search_results.json ──→ paper-analyze ──→ analysis_results.json
                                         │
                                         ├──────────────────────────────┐
                                         │                              │
                                         │                    similarity_network.png
                                         │                              │
                                         │                              │
                                         └──────────────────┬───────────┘
                                                            │
                                         ┌──────────────────┴───────────┐
                                         │                              │
                                         ▼                              ▼
                                    paper-report                  query-holder
                                    (one-time)                     (multi-turn)
                                    ──────────                     ──────────
                                    research_report               Q&A answers
```

Two contracts make this pipeline composable:

1. **JSON-file-only interface.** Skills never import each other's Python code. They communicate by reading and writing structured JSON in the `data/` directory. This keeps each skill independently runnable and testable.
2. **Auto-discovery convention.** Each downstream skill reads from `data/search_results.json` and `data/analysis_results.json`, so the common case is zero-config after the initial search.

---

## Directory structure

```
paper-researcher2.0/
├── README.md                          # this file
├── AGENT.md                           # agent workflow and contracts
│
├── .claude/
│   └── skills/
│   ├── paper-search/                  # Skill 1 — arXiv retrieval
│   │   ├── SKILL.md
│   │   └── paper_search.py
│   ├── paper-analyze/                 # Skill 2 — similarity network
│   │   ├── SKILL.md
│   │   └── paper_analyze.py
│   ├── paper-report/                 # Skill 3 — research briefing
│   │   ├── SKILL.md
│   │   └── paper_report.py
│   └── paper-qa/                     # Skill 4 — multi-turn Q&A
│       ├── SKILL.md
│       ├── query_holder.py           # main entry
│       ├── keyword_expander.py       # query expansion
│       └── query_session_manager.py  # session state
│
└── data/
    ├── search_results.json            # paper-search output
    ├── analysis_results.json          # paper-analyze output
    ├── citation_network.png           # similarity network visualization
    ├── research_report.md             # paper-report output
    └── query_session.json             # query-holder session state
```

---

## Quick start

### Prerequisites

- Python 3.9+.
- Two PyPI packages: `arxiv >= 2.0` (for `paper-search`), `networkx >= 3.0` (for `paper-analyze`). The other two skills (`paper-report`, `query-holder`) are stdlib-only.

```bash
# one-shot install
pip install "arxiv>=2.0" "networkx>=3.0"
```

### Option A — natural language end-to-end (recommended)

Just type your research question in plain language inside Claude Code — no slash command needed:

```
为我寻找近两年有关 attention 的论文，重点关注 Transformer 架构
```

or

```
find recent papers on diffusion models for medical imaging from the last 6 months
```

Claude (the agent) recognizes the intent, runs `paper-search` → `paper-analyze` → `paper-report`, and then you can ask follow-up questions using `query-holder`:

```
详细讲讲排行第一的论文
对比 Cubit 和 SoftSAE
排行第一的论文的主要方法是什么？
```

This is the typical use mode — zero config, no scripts.

### Option B — per-skill slash commands (explicit control)

When you want to re-run a single stage, each skill has its own kebab-case slash trigger:

```
/paper-search 为我寻找近两年有关 attention 的论文，重点关注 Transformer 架构
/paper-analyze
/paper-report
/query-holder 详细讲讲排行第一的论文
```

### Option C — run the scripts directly (outside Claude Code)

```bash
# 1. Search arXiv
python .claude/skills/paper-search/paper_search.py -q "attention" -m 20 -s submittedDate

# 2. Build similarity network + compute PageRank
python .claude/skills/paper-analyze/paper_analyze.py -v

# 3. Generate research briefing
python .claude/skills/paper-report/paper_report.py

# 4. Ask follow-up questions
python .claude/skills/paper-qa/query_holder.py -q "tell me more about rank 1"
python .claude/skills/paper-qa/query_holder.py -q "compare Cubit and SoftSAE"
python .claude/skills/paper-qa/query_holder.py -q "排行第一的论文的主要方法"
```

Each script supports `--verbose` for detailed output.

---

## Skills

| # | Skill | Reads | Writes | Stdlib-only? |
|---|---|---|---|---|
| 1 | `paper-search` | `-q`, `-m`, `-s` args | `data/search_results.json` | requires `arxiv` |
| 2 | `paper-analyze` | `data/search_results.json` | `data/analysis_results.json`, `data/citation_network.png` | requires `networkx` |
| 3 | `paper-report` | `data/search_results.json`, `data/analysis_results.json` | `data/research_report.md` | yes |
| 4 | `query-holder` | `data/search_results.json`, `data/analysis_results.json` | `data/query_session.json` | yes |

### 1. `paper-search` — arXiv retrieval

Translates query parameters into an arXiv API call and writes deduplicated paper metadata. Supports:
- Query terms (`-q`)
- Max results (`-m`)
- Sort by (`-s`: relevance, submittedDate, lastUpdatedDate)
- Date range filtering
- Category filtering

### 2. `paper-analyze` — similarity network + PageRank analysis

Builds a paper similarity network based on:
- **Content similarity**: TF-IDF cosine similarity over abstracts
- **Author overlap**: shared authors boost similarity

**Core ranking: PageRank** — measures paper influence based on network structure

**Score formula**: `score = 5.0 × similarity + 0.2 × same_author`

Outputs:
- `analysis_results.json`: papers ranked by PageRank score
- `similarity_network.png`: similarity network visualization

### 3. `paper-report` — research briefing

Joins `search_results.json` and `analysis_results.json` and renders a Markdown research briefing with:
- Top-N papers ranked by PageRank
- Network statistics (nodes, edges, clustering coefficient, density)
- Per-paper details (title, authors, abstract, link)

### 4. `query-holder` — multi-turn Q&A

Answers questions using only cached run JSON — no LLM, no arXiv calls.

**Supported query types**:

| Query Type | Example | Description |
|---|---|---|
| Paper Detail | "tell me more about Cubit" | Returns paper details by title match |
| Comparison | "compare Cubit and SoftSAE" | Side-by-side comparison of two papers |
| Keyword Filter | "what methods are used?" | Finds papers matching keywords |
| Author Search | "papers by Cubit author" | Finds papers by the same author |
| Follow-up | "it uses what dataset?" | Resolves references using session context |

**Session features**:
- Multi-turn context tracking (current focus papers, comparison pairs, active keywords)
- Reference resolution ("it", "this paper", "second one" → actual paper)
- Alias registration for paper titles
- Session state persistence to `data/query_session.json`

---

### Default I/O behavior every skill MUST implement

- Read inputs from `data/` directory by default.
- Write outputs into the **same** `data/` directory.
- Support `--verbose` for detailed output.
- Support `--help` for usage information.

---

## Score formula

The similarity network uses a weighted score combining content similarity and author overlap:

```
score = 5.0 × similarity + 0.2 × same_author
```

Where:
- `similarity`: TF-IDF cosine similarity between paper abstracts (0-1)
- `same_author`: 1 if papers share at least one author, 0 otherwise

Edge threshold (default: 0.3) controls network density. Increase for sparser networks, decrease for denser ones.

---

## Session features

The `query-holder` skill maintains session state across queries:

```json
{
  "current_focus_papers": ["Cubit"],
  "comparison_pair": ["Cubit", "SoftSAE"],
  "active_keywords": ["attention", "transformer"],
  "selected_papers_for_report": [],
  "paper_aliases": {},
  "conversation_turns": [
    {"query": "...", "response": "..."}
  ]
}
```

Key features:
- **Auto-discovery**: Identifies "rank 1", "top paper" based on PageRank from latest analysis
- **Reference resolution**: Maps pronouns and aliases to actual papers
- **Keyword expansion**: Expands search terms (e.g., "in-context learning" → "in-context learning, ICL, few-shot")
- **Multi-turn tracking**: Remembers context across the conversation

---

## Contributions

| Skills | Author |
|---|---|
| `paper-search`, `paper-analyze` | CodeBuddy |
| `paper-report`, `query-holder` | CodeBuddy |

---
