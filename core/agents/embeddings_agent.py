"""Embeddings Agent - Creates vector representations of candidates"""

from core.tools.embedding_tools import (
    embed_candidates,
    normalize_embeddings,
    validate_embeddings,
)


def create_embeddings_tools():
    """Create tool functions that work with embeddings"""

    def create_and_normalize_embeddings(candidates_json):
        """Create embeddings and normalize them"""
        embeddings = embed_candidates(candidates_json)
        normalized = normalize_embeddings(embeddings)
        return normalized

    return [create_and_normalize_embeddings]


def create_embeddings_agent():
    """Create Embeddings Agent"""
    return {
        "role": "Embeddings Specialist",
        "goal": "Transform candidate information into vector embeddings",
    }


def create_embeddings_task(agent):
    """Create task for Embeddings Agent"""
    return {
        "description": "Create vector embeddings for candidates",
        "agent": agent,
    }
