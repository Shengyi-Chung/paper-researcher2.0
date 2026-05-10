---
name: paper-report-generator
description: "Generate research reports from analyzed papers. Trigger: 'generate a research report', 'create a report from these papers', 'summarize the papers into a report', 'generate report'"
author: Xiangyu-Tang
version: 1.1.0
tags:
  - productivity
  - report-automation
  - markdown
  - summarization
  - arxiv
---

# paper-report-generator

## Role
A specialized Skill that transforms analyzed paper data into structured, user-readable research reports. It **merges upstream analysis and abstracts with arXiv HTML export enrichment** (introduction, conclusion, and **recent** related arXiv ids discovered across body text—not only the bibliography) so the narrative reflects both the original pipeline output and first-party paper sections.

## Input/Output Specifications

### Input
1. **paper-analysis.json** (from paper-analyze):
   - `analysis_date`: Analysis timestamp
   - `query`: Original search query
   - `total_papers`: Number of papers
   - `ranked_papers`: Array of paper objects with `rank`, `title`, `arxiv_id`, `authors`, `relevance_score`, `key_contributions`, `methods`

2. **papers.json** (from paper-search):
   - Paper metadata including full `abstract` text

3. **Enrichment source (this Skill):** `arxiv_utils.py` in the same workspace, especially `fetch_paper_export_bundle(arxiv_export_id, as_of=...)`, which performs **one** HTTP GET per paper to `export.arxiv.org` and returns:
   - Plain-text **introduction** and **conclusion** excerpts (heading-based extraction; conclusion falls back to “Discussion and conclusion” when needed)
   - `related_arxiv_ids_recent`: arXiv ids cited in introduction + conclusion + references, **filtered to the last two calendar years** from `as_of` (default: report generation date)

### Output

**1. paper_abstracts.json**  
Same as before: extracted abstracts aligned with the ranked list.

**2. paper_export_enrichment.json** (new)  
Written after enrichment passes; merges export data with original ids for traceability.

```json
{
  "generated_at": "ISO timestamp",
  "as_of_date": "YYYY-MM-DD used for two-year arXiv id cutoff",
  "enrichment_version": "1.1",
  "papers": [
    {
      "arxiv_id": "2604.xxxxx",
      "canonical_id": "2604.xxxxx",
      "rank": 1,
      "relevance_score": 9,
      "introduction_text": "...",
      "conclusion_text": "...",
      "related_arxiv_ids_recent": ["2405.01234", "2501.09999"],
      "has_references_section": true,
      "export_error": null
    }
  ]
}
```

If a paper cannot be fetched (network, 429, or no export HTML for very old ids), set `export_error` to a short string and leave text fields empty; still generate the report from original inputs.

**3. paper_reports.md**  
Markdown report that **explicitly combines three layers**:
- **Layer A (original):** `paper_analysis.json` rankings, scores, key contributions, methods
- **Layer B (metadata):** abstracts from `papers.json`
- **Layer C (export):** introduction/conclusion excerpts and `related_arxiv_ids_recent` from `paper_export_enrichment.json`

Use Layer C to sharpen the Executive Summary (claims, limitations, positioning) and to add a **Recent citation neighborhood** subsection per high-impact paper (ids only, with links to `https://arxiv.org/abs/<id>`—no extra web search).

## Workflow

### Step 1: Read Input Data
Read:
- `/data/papers.json`
- `/data/paper_analysis.json` (or `paper-analysis.json` if that is the filename used upstream—normalize to one convention and document in the run)

### Step 2: Extract Abstracts
Produce `paper_abstracts.json` as in v1.0.

### Step 3: Enrich via arXiv export (new)
For papers that have a valid `arxiv_id` in `ranked_papers`:

1. **Throttle:** Respect `arxiv_utils` query pacing (do not parallel-burst `export.arxiv.org`).
2. **Priority:** Enrich `relevance_score >= 8` first; then next tiers until a sensible cap (e.g. top 15–20) to limit rate limits.
3. For each id, call `fetch_paper_export_bundle(canonical_id, as_of=today)` from `arxiv_utils.py`.
4. Build `paper_export_enrichment.json`, joining **original** `rank`, `relevance_score`, `title`, `arxiv_id` with export fields.

**Two-year rule:** Only ids in `related_arxiv_ids_recent` are those passing `recent_two_years_eligible` in `arxiv_utils` (introduction + conclusion + references combined). Do not substitute a broader arXiv API search here—this list is export-derived only.

**Fetch eligibility:** Papers whose id has `YY < 23` in the arXiv numbering may lack HTML export; record `export_error` and continue.

### Step 4: Identify High-Relevance Papers
Same threshold: `relevance_score >= 8` for top billing.

### Step 5: Generate Report Structure
Build `paper_reports.md` in this order:

```markdown
# Research Report: [Topic/Query]

**Generated**: YYYY-MM-DD  
**Total Papers**: N  
**High-Relevance Papers**: M  
**Enrichment**: Introduction/conclusion + recent related arXiv ids from export HTML (`as_of` = YYYY-MM-DD)

---

## Executive Summary
Synthesize the landscape using **Layer A + B + C**: upstream contributions/methods, abstract themes, and (where present) how each top paper frames the problem in the introduction and what it claims in the conclusion. Call out **convergence** and **tension** between papers when enrichment text supports it.

---

## ⭐ High-Relevance Papers (Top Picks)

> **[Paper Title](https://arxiv.org/abs/xxxxx)**  
> Relevance: X/10 | Authors: A, B, C
>
> **Abstract** (from papers.json): ...
>
> **Introduction (excerpt)** (export): ...
>
> **Conclusion (excerpt)** (export): ...
>
> **Key Contributions** (from analysis): ...
>
> **Methods** (from analysis): ...
>
> **Recent related arXiv ids** (from intro/conclusion/refs, last 2 years): `id1`, `id2`, …

[Repeat for each high-relevance paper…]

---

## Detailed Analysis by Category
Group medium/low-relevance papers by methodology/topic. Where enrichment exists, add one short bullet per paper from its conclusion excerpt when helpful.

---

## Comparison Table

| Rank | Paper | Relevance | Key Methods | Main Contribution | Recent related ids (export) |
|------|-------|-----------|-------------|-------------------|----------------------------|
| 1 | Title | 9/10 | … | … | id1, id2 |
```

### Step 6: Save Outputs
```
/data/
├── papers.json
├── paper_analysis.json
├── paper_abstracts.json
├── paper_export_enrichment.json   # THIS SKILL (new)
└── paper_reports.md               # THIS SKILL
```

## Trigger Scenarios
Same as v1.0: after paper-analyze, or on user request to generate a report.

## Error Handling
| Error | Handling |
|-------|----------|
| paper_analysis.json not found | Request paper-analyze first |
| paper_analysis.json empty | Inform user; suggest new search |
| papers.json missing abstracts | Note unavailable; rely on analysis + export text |
| export fetch failure | Store `export_error`; report still uses Layers A+B |
| Missing Introduction/Conclusion headings in HTML | Leave excerpt blank; keep related ids from available regions |
| Invalid JSON in inputs | Skip bad entries; log counts |

## Evaluation Metrics
- **Relevance Accuracy**: High-relevance papers (score >= 8) highlighted correctly
- **Structural Clarity**: Sections ordered as specified; table includes enrichment column when data exists
- **Merge quality**: Report explicitly uses analysis + abstract + intro/conclusion + recent ids—not any single source alone
- **Markdown Compatibility**: Renders cleanly; arXiv links use full `https://arxiv.org/abs/...` URLs

## Integration with Other Skills
- **Input:** `paper-search` → `/data/papers.json`; `paper-analyze` → `/data/paper_analysis.json`
- **In-repo helper:** `arxiv_utils.fetch_paper_export_bundle` for HTML export enrichment (not a general-purpose web crawl)

---

## RESTRICTIONS (严格限制)

### ✅ 本 Skill 必须做的：
1. **读取分析结果** — 从 `paper_analysis.json` 获取排名和评分
2. **读取论文元数据** — 从 `papers.json` 获取摘要
3. **用 arxiv_utils 做导出增强** — 对优先论文调用 `fetch_paper_export_bundle`，写入 `paper_export_enrichment.json`
4. **合并三层信息写报告** — 分析结果 + 摘要 + 导出（引言/结论/近两年相关 id）写入 `paper_reports.md`
5. **高亮高相关性论文** — `relevance_score >= 8` 优先展示，并优先完成导出拉取
6. **生成 paper_abstracts.json**

### ❌ 本 Skill 禁止做的：
1. **禁止替代上游的分析/评分** — 不修改 `paper_analysis.json` 中的分数与结构化字段
2. **禁止一般网页搜索** — 除通过 `arxiv_utils` 访问 `export.arxiv.org` 外，不抓取其他站点
3. **禁止扩展“近两年”以外的引用发现** — `related_arxiv_ids_recent` 必须来自导出 HTML 扫描结果并经 `recent_two_years_eligible` 过滤；不另开 arXiv API 主题搜索
4. **禁止 briefing 格式** — 不使用 briefing-report-generator 的版式
5. **禁止无关可视化** — 不生成 PNG/HTML 图表
6. **禁止默认中文简报** — 中文简报走 briefing-report-generator

### 📌 边界情况：
- `paper_analysis.json` 不存在 → 告知先运行 paper-analyze
- 用户要简报版式 → 指向 briefing-report-generator
- 用户要图表 → 说明不支持
- 用户要 broader 文献检索 → 指向 paper-search；本 Skill 的“相关论文”仅限于导出 HTML 中解析出的近两年 arXiv id
