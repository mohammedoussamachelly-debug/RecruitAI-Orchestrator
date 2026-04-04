"""Tools for creating and managing candidate embeddings"""

import json
from typing import Any, Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer


def embed_candidates(candidates_json: str, model_name: str = "all-MiniLM-L6-v2") -> str:
    """
    Create vector embeddings for candidates using sentence-transformers.

    Args:
        candidates_json: JSON string with candidate data containing 'text' field
        model_name: Sentence-transformers model to use

    Returns:
        JSON string with candidates plus their embeddings
    """
    try:
        candidates = json.loads(candidates_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    model = SentenceTransformer(model_name)

    embeddings_data = []
    for candidate in candidates:
        text = candidate.get("text", "")
        if not text:
            continue

        # Create embedding
        embedding = model.encode(text, convert_to_numpy=True)

        embeddings_data.append(
            {
                "name": candidate.get("name"),
                "text": text[:500],  # Truncate for storage
                "embedding": embedding.tolist(),  # Convert to list for JSON
                "embedding_dim": len(embedding),
            }
        )

    return json.dumps(embeddings_data)


def normalize_embeddings(embeddings_json: str) -> str:
    """
    Normalize embeddings to unit vectors for Qdrant compatibility.

    Args:
        embeddings_json: JSON string with embedding data

    Returns:
        JSON string with normalized embeddings
    """
    try:
        data = json.loads(embeddings_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    normalized_data = []
    for item in data:
        embedding = np.array(item.get("embedding", []))
        if embedding.size == 0:
            continue

        # L2 normalization
        norm = np.linalg.norm(embedding)
        if norm > 0:
            normalized = (embedding / norm).tolist()
        else:
            normalized = embedding.tolist()

        item["embedding"] = normalized
        normalized_data.append(item)

    return json.dumps(normalized_data)


def validate_embeddings(embeddings_json: str, expected_dim: int = 384) -> str:
    """
    Validate embeddings have correct dimension and format.

    Args:
        embeddings_json: JSON string with embedding data
        expected_dim: Expected embedding dimension (default 384 for sentence-transformers)

    Returns:
        JSON with validation results
    """
    try:
        data = json.loads(embeddings_json)
    except json.JSONDecodeError:
        return json.dumps({"valid": False, "error": "Invalid JSON input"})

    if not isinstance(data, list):
        return json.dumps({"valid": False, "error": "Expected list of embeddings"})

    validation_results = {
        "total": len(data),
        "valid": 0,
        "invalid": 0,
        "errors": [],
    }

    for i, item in enumerate(data):
        embedding = item.get("embedding", [])
        if not isinstance(embedding, list):
            validation_results["invalid"] += 1
            validation_results["errors"].append(
                f"Item {i}: embedding is not a list"
            )
            continue

        if len(embedding) != expected_dim:
            validation_results["invalid"] += 1
            validation_results["errors"].append(
                f"Item {i}: expected {expected_dim} dimensions, got {len(embedding)}"
            )
            continue

        validation_results["valid"] += 1

    validation_results["all_valid"] = validation_results["invalid"] == 0
    return json.dumps(validation_results)
