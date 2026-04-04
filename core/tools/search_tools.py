"""Tools for searching candidates using vector similarity"""

import json
from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


def search_qdrant(
    domain: str, embedding: List[float], top_k: int = 5, collection_name: str = "candidates"
) -> str:
    """
    Query Qdrant vector database for similar candidates.

    Args:
        domain: Domain/job type to search
        embedding: Query embedding vector
        top_k: Number of top results to return
        collection_name: Name of Qdrant collection

    Returns:
        JSON string with ranked candidates
    """
    try:
        client = QdrantClient(":memory:")  # For demo, use in-memory. Update to remote in prod

        # Attempt to search
        try:
            results = client.search(
                collection_name=collection_name,
                query_vector=embedding,
                limit=top_k,
                score_threshold=0.0,
            )

            candidates = [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]

            return json.dumps({
                "domain": domain,
                "results": candidates,
                "count": len(candidates),
            })
        except Exception as e:
            # Collection doesn't exist yet or search failed
            return json.dumps({
                "domain": domain,
                "results": [],
                "count": 0,
                "note": f"Qdrant collection not available: {str(e)}. Using fallback.",
            })
    except Exception as e:
        return json.dumps({
            "error": f"Failed to search Qdrant: {str(e)}",
            "domain": domain,
            "results": [],
        })


def rank_by_similarity(results_json: str) -> str:
    """
    Sort search results by similarity score.

    Args:
        results_json: JSON string with search results

    Returns:
        JSON string with sorted results
    """
    try:
        data = json.loads(results_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    results = data.get("results", [])

    # Sort by score (descending)
    sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    data["results"] = sorted_results
    data["count"] = len(sorted_results)
    return json.dumps(data)


def fallback_keyword_search(domain: str, candidates_json: str) -> str:
    """
    Fallback keyword-based search when Qdrant is unavailable.

    Args:
        domain: Domain/job type to search
        candidates_json: JSON string with candidate data

    Returns:
        JSON string with ranked candidates based on keyword match
    """
    try:
        candidates = json.loads(candidates_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    # Define keywords for each domain
    domain_keywords = {
        "backend": [
            "python",
            "java",
            "node",
            "sql",
            "database",
            "api",
            "server",
        ],
        "frontend": [
            "react",
            "javascript",
            "css",
            "html",
            "ui",
            "frontend",
            "web",
        ],
        "data_science": [
            "machine learning",
            "python",
            "data",
            "ai",
            "tensorflow",
            "pandas",
        ],
        "devops": [
            "docker",
            "kubernetes",
            "aws",
            "ci/cd",
            "deployment",
            "infrastructure",
        ],
        "fullstack": [
            "react",
            "node",
            "javascript",
            "python",
            "database",
            "web",
        ],
    }

    keywords = domain_keywords.get(domain.lower(), [])
    if not keywords:
        keywords = domain.lower().split()

    # Score candidates based on keyword matches
    scored_candidates = []
    for candidate in candidates:
        text = (candidate.get("text", "") + candidate.get("skills", "")).lower()
        score = sum(1 for keyword in keywords if keyword.lower() in text)

        if score > 0:
            scored_candidates.append(
                {
                    "name": candidate.get("name"),
                    "score": score / len(keywords),
                    "payload": candidate,
                }
            )

    # Sort by score
    scored_candidates.sort(key=lambda x: x["score"], reverse=True)

    return json.dumps({
        "domain": domain,
        "results": scored_candidates[:10],  # Top 10
        "count": len(scored_candidates),
        "method": "keyword_fallback",
    })
