"""
paper-report: Paper recommendation report generation skill v1.1.0

Generates research reports from analyzed papers, merging:
- Layer A: upstream analysis rankings and scores
- Layer B: paper abstracts from search
- Layer C: arXiv export enrichment (intro/conclusion/recent citations)

Outputs:
- paper_abstracts.json
- paper_export_enrichment.json (with arXiv enrichment)
- paper_reports.md
"""

from .paper_report import (
    display_report,
    generate_full_report,
    main,
    load_search_results,
    load_analysis_results,
    get_data_dir,
    extract_abstracts,
    enrich_with_exports,
    generate_report,
)

__all__ = [
    'display_report',
    'generate_full_report',
    'main',
    'load_search_results',
    'load_analysis_results',
    'get_data_dir',
    'extract_abstracts',
    'enrich_with_exports',
    'generate_report',
]
