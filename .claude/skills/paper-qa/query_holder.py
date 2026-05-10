#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
query-holder: Conversational follow-up query manager for retrieved research papers.

Workflow:
1. Load conversation state
2. Parse user query
3. Match papers / search info
4. Update context
5. Generate response
"""

import json
import os
import re
import argparse
from typing import List, Dict, Optional, Tuple

# Import local modules
from keyword_expander import expand_keyword, expand_keywords
from query_session_manager import QuerySessionManager


# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
ANALYSIS_PATH = os.path.join(DATA_DIR, "analysis_results.json")
SEARCH_PATH = os.path.join(DATA_DIR, "search_results.json")
SESSION_PATH = os.path.join(DATA_DIR, "query_session.json")


def safe_print(msg: str):
    """Print with encoding fallback"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Try to encode/decode with replacement for problematic characters
        try:
            print(msg.encode('utf-8', errors='replace').decode('utf-8'))
        except:
            # Fallback: replace non-ASCII characters
            ascii_msg = msg.encode('ascii', errors='replace').decode('ascii')
            print(ascii_msg)


class QueryHolder:
    """Main query holder class for conversational paper retrieval"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or DATA_DIR
        self.analysis_path = os.path.join(self.data_dir, "analysis_results.json")
        self.search_path = os.path.join(self.data_dir, "search_results.json")
        self.session_path = os.path.join(self.data_dir, "query_session.json")
        
        # Initialize managers
        self.session = QuerySessionManager(self.session_path)
        
        # Load paper data
        self.analysis_data = self._load_json(self.analysis_path)
        self.search_data = self._load_json(self.search_path)
        
        # Build paper index
        self.papers = self._build_paper_index()
    
    def _load_json(self, path: str) -> Optional[Dict]:
        """Load JSON file"""
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None
    
    def _build_paper_index(self) -> List[Dict]:
        """Build paper index from analysis and search data"""
        papers = {}
        
        # From analysis results (ranked papers)
        if self.analysis_data:
            for item in self.analysis_data.get('pagerank_scores', []):
                papers[item['arxiv_id']] = {
                    'arxiv_id': item['arxiv_id'],
                    'title': item['title'],
                    'authors': item.get('authors', []),
                    'abstract': item.get('abstract', ''),
                    'published': item.get('published', ''),
                    'pagerank_score': item.get('pagerank_score', 0),
                    'connections': item.get('connections', 0),
                    'url': f"https://arxiv.org/abs/{item['arxiv_id'].replace('v1', '')}",
                    'source': 'analysis'
                }
        
        # From search results (full details)
        if self.search_data:
            for paper in self.search_data.get('papers', []):
                aid = paper.get('arxiv_id')
                if aid and aid in papers:
                    papers[aid].update({
                        'abstract': paper.get('abstract', ''),
                        'authors': paper.get('authors', [])
                    })
                elif aid:
                    papers[aid] = {
                        'arxiv_id': aid,
                        'title': paper.get('title', ''),
                        'authors': paper.get('authors', []),
                        'abstract': paper.get('abstract', ''),
                        'published': paper.get('published', ''),
                        'url': paper.get('abstract_url', ''),
                        'source': 'search'
                    }
        
        return list(papers.values())
    
    # =========================================================
    # Query Parsing
    # =========================================================
    
    def parse_query(self, query: str) -> Dict:
        """Parse user query and determine intent"""
        query_lower = query.lower()
        
        # Determine query type
        query_type = 'keyword_filter'
        
        # Paper detail queries
        if any(kw in query_lower for kw in ['tell me more', 'details of', 'what does', 'more about']):
            query_type = 'paper_detail'
        # Comparison queries
        elif any(kw in query_lower for kw in ['compare', 'difference', 'which one is better', 'vs', 'versus']):
            query_type = 'comparison'
        # Author search
        elif any(kw in query_lower for kw in ['papers by', 'written by', 'author', 'other works from']):
            query_type = 'author_search'
        # Benchmark/dataset queries
        elif any(kw in query_lower for kw in ['performs best on', 'evaluated on', 'dataset', 'benchmark']):
            query_type = 'benchmark_query'
        # Follow-up / reference
        elif any(kw in query_lower for kw in ['it', 'this paper', 'the second', 'baseline', 'what about']):
            query_type = 'followup_reference'
        
        # Extract components
        authors = self._extract_authors(query)
        keywords = self._extract_keywords(query)
        paper_titles = self._extract_paper_titles(query)
        
        return {
            'query_type': query_type,
            'raw_query': query,
            'authors': authors,
            'keywords': keywords,
            'paper_titles': paper_titles
        }
    
    def _extract_authors(self, query: str) -> List[str]:
        """Extract author names from query"""
        # Pattern: "by [Name]" or "[Name]'s papers"
        patterns = [
            r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'by\s+([A-Z][a-z]+)',
            r"([A-Z][a-z]+\s+[A-Z][a-z]+)'s",
        ]
        authors = []
        for pattern in patterns:
            matches = re.findall(pattern, query)
            authors.extend(matches)
        return list(set(authors))
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords"""
        # Remove common stop words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'what', 'which', 'how', 'about', 
                      'does', 'do', 'tell', 'me', 'more', 'compare', 'difference'}
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        return [w for w in words if w not in stop_words]
    
    def _extract_paper_titles(self, query: str) -> List[str]:
        """Extract paper titles from query"""
        # Look for quoted strings
        titles = re.findall(r'"([^"]+)"', query)
        
        # Handle "compare A and B" pattern
        compare_match = re.search(r'compare\s+(.+?)\s+and\s+(.+)', query, re.IGNORECASE)
        if compare_match:
            titles.append(compare_match.group(1).strip())
            titles.append(compare_match.group(2).strip())
        
        # Fuzzy match against known papers
        for paper in self.papers:
            title_lower = paper['title'].lower()
            # Check if significant words from title appear in query
            title_words = set(re.findall(r'\b[a-z]{3,}\b', title_lower))
            query_words = set(re.findall(r'\b[a-z]{3,}\b', query.lower()))
            overlap = title_words & query_words
            if len(overlap) >= 2:  # At least 2 significant word matches
                titles.append(paper['title'])
        
        return list(set(titles))
    
    # =========================================================
    # Paper Retrieval
    # =========================================================
    
    def match_papers(self, parsed: Dict) -> List[Dict]:
        """Match papers based on parsed query"""
        query_type = parsed['query_type']
        matched = []
        
        if query_type == 'paper_detail':
            matched = self._match_by_title(parsed['paper_titles'])
            if not matched and parsed['keywords']:
                matched = self._match_by_title(parsed['keywords'])
        
        elif query_type == 'comparison':
            if parsed['paper_titles']:
                matched = self._match_by_title(parsed['paper_titles'])
        
        elif query_type == 'author_search':
            matched = self._match_by_author(parsed['authors'])
        
        elif query_type == 'followup_reference':
            # Resolve reference first
            ref = self.session.resolve_reference(parsed['raw_query'])
            if ref:
                matched = self._match_by_title([ref])
            else:
                matched = self.session.get_focus_papers()
        
        else:  # keyword_filter
            matched = self._match_by_keywords(parsed['keywords'])
        
        return matched[:5]  # Return top 5
    
    def _match_by_title(self, titles: List[str]) -> List[Dict]:
        """Match papers by title"""
        matched = []
        for title_query in titles:
            expanded = expand_keywords([title_query])
            for paper in self.papers:
                title_lower = paper['title'].lower()
                if any(exp.lower() in title_lower for exp in expanded):
                    if paper not in matched:
                        matched.append(paper)
        return matched
    
    def _match_by_author(self, authors: List[str]) -> List[Dict]:
        """Match papers by author"""
        matched = []
        for author_query in authors:
            expanded = expand_keywords([author_query])
            for paper in self.papers:
                for author in paper.get('authors', []):
                    if any(exp.lower() in author.lower() for exp in expanded):
                        if paper not in matched:
                            matched.append(paper)
                        break
        return matched
    
    def _match_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """Match papers by keywords"""
        if not keywords:
            return sorted(self.papers, key=lambda x: x.get('pagerank_score', 0), reverse=True)[:5]
        
        matched = []
        for keyword in keywords:
            expanded = expand_keywords([keyword])
            for paper in self.papers:
                text = (paper['title'] + ' ' + paper.get('abstract', '')).lower()
                if any(exp.lower() in text for exp in expanded):
                    if paper not in matched:
                        matched.append(paper)
        
        # Sort by relevance (pagerank score)
        return sorted(matched, key=lambda x: x.get('pagerank_score', 0), reverse=True)
    
    # =========================================================
    # Response Generation
    # =========================================================
    
    def generate_response(self, query: str, matched: List[Dict], query_type: str) -> str:
        """Generate contextual response"""
        if not matched:
            return self._generate_no_match_response(query)
        
        response_parts = []
        
        # Update session
        self.session.set_focus_papers([p['title'] for p in matched[:3]])
        self.session.add_query(query)
        self.session.set_last_query_type(query_type)
        
        if query_type == 'paper_detail':
            response_parts.append(self._format_paper_detail(matched[0]))
            response_parts.append(self._format_paper_list(matched[1:]))
        
        elif query_type == 'comparison':
            self.session.set_comparison_pair(matched[0]['title'], matched[1]['title'])
            response_parts.append(self._format_comparison(matched[:2]))
        
        elif query_type == 'author_search':
            response_parts.append(self._format_author_papers(matched))
        
        else:
            response_parts.append(self._format_paper_list(matched))
        
        # Add suggestions
        response_parts.append(self._format_suggestions(query_type, matched))
        
        # Save session
        self.session.save()
        
        return '\n\n'.join(response_parts)
    
    def _format_paper_detail(self, paper: Dict) -> str:
        """Format single paper detail"""
        lines = [
            f"📄 **{paper['title']}**",
            f"",
            f"**ID:** {paper['arxiv_id']}",
            f"**Authors:** {', '.join(paper.get('authors', [])[:5])}",
            f"**Published:** {paper.get('published', 'N/A')[:10]}",
            f"**Importance:** ⭐ {'⭐' * int(paper.get('pagerank_score', 0) * 10)} ({paper.get('pagerank_score', 0):.4f})",
            f"",
        ]
        
        abstract = paper.get('abstract', '')
        if abstract:
            lines.append(f"**Abstract:**\n{self._truncate(abstract, 300)}")
        
        lines.append(f"\n🔗 {paper.get('url', '#')}")
        
        return '\n'.join(lines)
    
    def _format_paper_list(self, papers: List[Dict]) -> str:
        """Format list of papers"""
        if not papers:
            return ""
        
        lines = ["**Related Papers:**", ""]
        for i, paper in enumerate(papers, 1):
            authors = ', '.join(paper.get('authors', [])[:2])
            score = paper.get('pagerank_score', 0)
            lines.append(f"{i}. **{paper['title']}**")
            lines.append(f"   - Authors: {authors}")
            lines.append(f"   - Score: {score:.4f}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_comparison(self, papers: List[Dict]) -> str:
        """Format comparison between papers"""
        if len(papers) < 2:
            return self._format_paper_detail(papers[0])
        
        lines = [
            "## 📊 Paper Comparison",
            "",
            f"| Aspect | {self._truncate(papers[0]['title'], 30)} | {self._truncate(papers[1]['title'], 30)} |",
            f"|--------|{'-|'.join(['-' * 30] * 2)}|",
        ]
        
        # Add comparison rows
        for paper in papers:
            authors_str = ', '.join(paper.get('authors', [])[:2])
            score = paper.get('pagerank_score', 0)
        
        lines.append(f"| **Title** | {self._truncate(papers[0]['title'], 25)} | {self._truncate(papers[1]['title'], 25)} |")
        lines.append(f"| **Authors** | {', '.join(papers[0].get('authors', [])[:2])} | {', '.join(papers[1].get('authors', [])[:2])} |")
        lines.append(f"| **Score** | {papers[0].get('pagerank_score', 0):.4f} | {papers[1].get('pagerank_score', 0):.4f} |")
        lines.append(f"| **Connections** | {papers[0].get('connections', 0)} | {papers[1].get('connections', 0)} |")
        lines.append("")
        
        return '\n'.join(lines)
    
    def _format_author_papers(self, papers: List[Dict]) -> str:
        """Format papers by author"""
        lines = [f"**Found {len(papers)} paper(s) by this author:**", ""]
        for paper in papers:
            lines.append(f"- {paper['title']} ({paper.get('pagerank_score', 0):.4f})")
        return '\n'.join(lines)
    
    def _format_suggestions(self, query_type: str, matched: List[Dict]) -> str:
        """Generate follow-up suggestions"""
        suggestions = ["", "**💡 Follow-up suggestions:**"]
        
        if query_type == 'paper_detail':
            suggestions.append("- \"compare it with other papers\"")
            suggestions.append("- \"what methods does it use?\"")
        elif query_type == 'comparison':
            suggestions.append("- \"which one has better novelty?\"")
            suggestions.append("- \"compare methods in detail\"")
        else:
            suggestions.append("- \"tell me more about the first one\"")
            suggestions.append("- \"compare top 2 papers\"")
        
        return '\n'.join(suggestions)
    
    def _generate_no_match_response(self, query: str) -> str:
        """Response when no papers match"""
        return (
            f"❓ I couldn't find papers matching \"{query}\"\n\n"
            "**Suggestions:**\n"
            "- Try different keywords\n"
            "- Use paper-search to retrieve more papers\n"
            "- Check if papers have been analyzed first"
        )
    
    def _truncate(self, text: str, length: int) -> str:
        """Truncate text to length"""
        if len(text) <= length:
            return text
        return text[:length-3] + "..."
    
    # =========================================================
    # Main Query Handler
    # =========================================================
    
    def query(self, user_query: str) -> str:
        """Main query handler"""
        # Step 1: Parse query
        parsed = self.parse_query(user_query)
        
        # Step 2: Match papers
        matched = self.match_papers(parsed)
        
        # Step 3: Generate response
        response = self.generate_response(user_query, matched, parsed['query_type'])
        
        # Step 4: Update session
        self.session.add_conversation_turn(user_query, response[:200])
        self.session.save()
        
        return response
    
    def print_help(self):
        """Print help information"""
        help_text = """
============================================================
              query-holder Usage
============================================================

Example queries:

  - "tell me more about Cubit"
  - "compare Cubit and SoftSAE"
  - "papers by Cubit author"
  - "what methods are used?"
  - "which one performs best?"
  - "it uses what dataset?"

Session features:

  - Multi-turn context tracking
  - Reference resolution (it, this paper, second one)
  - Paper comparison
  - Author search

============================================================
"""
        print(help_text)


def main():
    parser = argparse.ArgumentParser(description='query-holder: Conversational paper query manager')
    parser.add_argument('--query', '-q', type=str, help='User query')
    parser.add_argument('--help-query', action='store_true', help='Show example queries')
    parser.add_argument('--session', action='store_true', help='Show current session state')
    
    args = parser.parse_args()
    
    if args.help_query:
        holder = QueryHolder()
        holder.print_help()
        return
    
    holder = QueryHolder()
    
    if args.session:
        print("\n=== Current Session State ===")
        print(json.dumps(holder.session.state, indent=2, ensure_ascii=False))
        return
    
    if not args.query:
        print("No query provided. Use -q \"your question\" or --help-query for examples.")
        return
    
    # Run query
    response = holder.query(args.query)
    print("\n" + "="*60)
    print("QUERY:", args.query)
    print("="*60)
    safe_print(response)


if __name__ == "__main__":
    main()
