import json
import os
from typing import List, Dict, Optional


class QuerySessionManager:
    def __init__(self, session_path=None):
        if session_path is None:
            # Navigate: query_session_manager.py -> paper-qa/ -> skills/ -> .claude/ -> project_root/ -> data/
            import os
            _f = __file__
            _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_f))))
            session_path = os.path.join(_base, "data", "query_session.json")
        self.session_path = session_path
        self.state = self._load_state()

    # =========================================================
    # Initialization
    # =========================================================

    def _default_state(self):
        return {
            "current_focus_papers": [],
            "comparison_pair": [],
            "active_keywords": [],
            "recent_queries": [],
            "recent_authors": [],
            "selected_papers_for_report": [],
            "paper_aliases": {},
            "last_query_type": "",
            "last_resolved_references": {},
            "conversation_turns": []
        }

    def _load_state(self):
        if not os.path.exists(self.session_path):
            return self._default_state()

        with open(self.session_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self):
        os.makedirs(os.path.dirname(self.session_path), exist_ok=True)

        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    # =========================================================
    # Conversation Updates
    # =========================================================

    def add_query(self, query: str):
        self.state["recent_queries"].append(query)

        # keep last 10
        self.state["recent_queries"] = self.state["recent_queries"][-10:]

    def add_conversation_turn(self, user_query: str, response_summary: str):
        self.state["conversation_turns"].append({
            "user_query": user_query,
            "response_summary": response_summary
        })

        # keep lightweight history
        self.state["conversation_turns"] = self.state["conversation_turns"][-20:]

    def set_focus_papers(self, papers: List[str]):
        self.state["current_focus_papers"] = papers

    def set_comparison_pair(self, paper_a: str, paper_b: str):
        self.state["comparison_pair"] = [paper_a, paper_b]

    def add_active_keyword(self, keyword: str):
        if keyword not in self.state["active_keywords"]:
            self.state["active_keywords"].append(keyword)

    def add_recent_author(self, author: str):
        if author not in self.state["recent_authors"]:
            self.state["recent_authors"].append(author)

    def add_selected_paper(self, paper_title: str):
        if paper_title not in self.state["selected_papers_for_report"]:
            self.state["selected_papers_for_report"].append(paper_title)

    def set_last_query_type(self, query_type: str):
        self.state["last_query_type"] = query_type

    def set_last_resolved_references(self, refs: Dict):
        self.state["last_resolved_references"] = refs

    # =========================================================
    # Alias Management
    # =========================================================

    def register_alias(self, alias: str, paper_title: str):
        self.state["paper_aliases"][alias.lower()] = paper_title

    def resolve_alias(self, alias: str) -> Optional[str]:
        return self.state["paper_aliases"].get(alias.lower())

    # =========================================================
    # Reference Resolution
    # =========================================================

    def resolve_reference(self, reference: str):
        """
        Resolve conversational references like:
        - it
        - this paper
        - second paper
        - baseline
        """

        reference = reference.lower().strip()

        focus = self.state["current_focus_papers"]
        comparison = self.state["comparison_pair"]

        if reference in ["it", "this paper", "the paper"]:
            if focus:
                return focus[0]

        if reference in ["second paper", "the second one"]:
            if len(comparison) >= 2:
                return comparison[1]

        if reference in ["first paper", "the first one"]:
            if len(comparison) >= 1:
                return comparison[0]

        if reference in self.state["paper_aliases"]:
            return self.state["paper_aliases"][reference]

        return None

    # =========================================================
    # Context Accessors
    # =========================================================

    def get_focus_papers(self):
        return self.state["current_focus_papers"]

    def get_comparison_pair(self):
        return self.state["comparison_pair"]

    def get_active_keywords(self):
        return self.state["active_keywords"]

    def get_recent_queries(self):
        return self.state["recent_queries"]

    def get_selected_papers(self):
        return self.state["selected_papers_for_report"]