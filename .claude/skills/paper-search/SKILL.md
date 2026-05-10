---
name: paper-search
description: "Search arXiv papers and extract metadata. Triggers: 'search papers about [topic]', '找关于[主题]的文章', '搜索[关键词]论文'"
author: Shengyi-Chung
version: 1.0.0
tags:
  - arxiv
  - paper-search
  - information-retrieval
---

# paper-search

## Role
Extract keywords from user input, search arXiv papers, and extract complete metadata. Save results as JSON for downstream skills.

## Workflow

### Step 1: Parse User Query
Extract search keywords from user input.

**Examples:**
- "帮我搜索关于 MoE 的论文" → Keywords: "MoE"
- "找一些 transformer 的文章" → Keywords: "transformer"
- "search papers about LLM alignment" → Keywords: "LLM alignment"

### Step 2: Call arXiv API
Search papers using arXiv API.

**API Endpoint:** `http://export.arxiv.org/api/query`

**Parameters:**
- `search_query`: Search keywords
- `start`: Pagination offset
- `max_results`: Number of results (default: 20)
- `sortBy`: "submittedDate" (newest first)

### Step 3: Extract Metadata
Extract the following fields from XML response:

| Field | Description |
|-------|-------------|
| `arxiv_id` | arXiv paper ID |
| `title` | Paper title |
| `abstract` | Abstract |
| `authors` | Author list |
| `published` | Publication date |
| `updated` | Last update date |
| `categories` | Paper categories |
| `doi` | DOI (if available) |
| `pdf_url` | PDF download link |

### Step 4: Save Data
Save metadata to `data/search_results.json`

## Data Format

```json
{
  "query": "transformer",
  "search_time": "2026-05-10T19:23:00",
  "total_results": 20,
  "papers": [
    {
      "arxiv_id": "1706.03762",
      "title": "Attention Is All You Need",
      "abstract": "The dominant sequence transduction models...",
      "authors": ["Ashish Vaswani", "Noam Shazeer", ...],
      "published": "2017-06-12",
      "updated": "2023-08-23",
      "categories": ["cs.CL", "cs.LG", "cs.NE"],
      "doi": "10.48550/arXiv.1706.03762",
      "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
      "citation_count": null
    }
  ]
}
```

## Usage

### Python API
```python
from paper_search import search_papers

# Search papers
results = search_papers("transformer", max_results=20)

# Access results
for paper in results["papers"]:
    print(f"{paper['title']} - {paper['authors']}")
```

### Command Line
```bash
python paper_search.py --query "MoE" --max 20
```

## Output Files
- `data/search_results.json` - Search results
- `data/search_params.json` - Search parameters

## Error Handling

| Error | Handling |
|-------|----------|
| API timeout | Retry once, increase timeout |
| No results | Prompt user to try different keywords |
| XML parse error | Log error, return empty list |
| Network error | Retry 3 times, then report failure |

## Dependencies
- `requests`
- `xml.etree.ElementTree` (built-in)
- `urllib.parse` (built-in)
- `datetime` (built-in)
