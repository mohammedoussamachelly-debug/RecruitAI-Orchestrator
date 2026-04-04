"""Search Agent - Finds best matching candidates per domain"""

import json
from core.tools.search_tools import (
    search_qdrant,
    rank_by_similarity,
    fallback_keyword_search,
)


def create_search_tools():
    """Create tool functions for searching candidates"""

    def search_candidates_by_domain(embeddings_json, domains):
        """Search for best candidates in each domain"""
        try:
            candidates = json.loads(embeddings_json)
        except:
            return json.dumps({"error": "Invalid input"})

        domain_results = {}

        for domain in domains:
            # Use keyword fallback search
            results = fallback_keyword_search(domain, embeddings_json)
            ranked = rank_by_similarity(results)
            domain_results[domain] = json.loads(ranked)

        return json.dumps({
            "domains": domain_results,
            "total_domains": len(domains),
            "status": "search_complete",
        })

    return [search_candidates_by_domain]


def create_search_agent():
    """Create Search Agent"""
    return {
        "role": "Search Specialist",
        "goal": "Find best matching candidates for each domain",
    }


def create_search_task(agent, domains=None):
    """Create task for Search Agent"""
    return {
        "description": f"Search candidates for domains: {domains}",
        "agent": agent,
    }
