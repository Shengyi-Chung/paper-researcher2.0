---
name: paper-report
description: "Generate paper recommendation reports based on search results and ranking analysis. Triggers: '生成报告', '推荐报告', '论文总结', 'generate report', 'recommend papers'"
author: Shengyi-Chung
version: 1.0.0
tags:
  - paper
  - report
  - recommendation
  - summary
---

# Paper Report Generator

## Core Capabilities

Generate comprehensive paper recommendation reports based on search results and analysis rankings.

## Input

Read from:
- `data/search_results.json` - Paper metadata
- `data/analysis_results.json` - Ranking and network analysis

## Workflow

### Step 1: Load Data
Load paper metadata and analysis results from JSON files.

### Step 2: Analyze Papers
For each paper, gather:
- Basic info (title, authors, date)
- PageRank score and rank
- Connection count (related papers)
- Similarity connections details

### Step 3: Generate Report Sections

#### 3.1 Overview
- Total papers analyzed
- Search query and time
- Network statistics (nodes, edges, density)

#### 3.2 Top Recommendations
Rank papers by PageRank, for each include:
- Rank and importance score
- Paper title/ID
- Key authors
- Why recommended (high PageRank, many connections)
- Related papers

#### 3.3 Research Clusters
Identify research clusters based on network:
- Groups of highly connected papers
- Shared themes/topics

#### 3.4 Detailed Analysis
- Papers with most connections
- Papers with highest similarity scores
- Author overlap analysis

### Step 4: Format Output

#### Markdown Format
```markdown
# Paper Recommendation Report

## Overview
...

## Top 10 Recommended Papers
1. **[Paper Title]** - Score: X.XX
   - Authors: ...
   - Why: ...
   - Related: ...

## Research Clusters
...

## Detailed Analysis
...
```

#### JSON Format
```json
{
  "report_time": "ISO timestamp",
  "query": "search query",
  "overview": {...},
  "top_papers": [...],
  "clusters": [...],
  "detailed_analysis": {...}
}
```

## Tech Stack

- Python (standard library)
- JSON parsing
- String formatting (markdown)

## Usage

### Python API
```python
from paper_report import generate_report, print_report

# Generate report
report = generate_report()

# Print to console
print_report(report)

# Save to file
with open('data/paper_report.md', 'w') as f:
    f.write(report['markdown'])
```

### Command Line
```bash
python paper_report.py
python paper_report.py --format json
python paper_report.py --top 20
```
