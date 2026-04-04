"""Tools for grouping candidates into teams"""

import json
from typing import Any, Dict, List


def group_by_domain(
    candidates_json: str, domains: List[str] = None, per_group: int = 3
) -> str:
    """
    Group candidates into teams by domain ensuring balanced expertise.

    Args:
        candidates_json: JSON string with candidate search results by domain
        domains: List of domains to group
        per_group: Number of members per team

    Returns:
        JSON string with organized teams
    """
    if domains is None:
        domains = []

    try:
        candidates_data = json.loads(candidates_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    groups = {}

    # Handle different input formats
    if isinstance(candidates_data, dict) and "domains" in candidates_data:
        # Format: {"domains": {"backend": [...], "frontend": [...]}}
        domain_results = candidates_data.get("domains", {})
    elif isinstance(candidates_data, dict) and "results" in candidates_data:
        # Single domain result
        domain_results = {candidates_data.get("domain", "general"): candidates_data.get("results", [])}
    elif isinstance(candidates_data, list):
        # List of candidates
        domain_results = {"general": candidates_data}
    else:
        domain_results = candidates_data

    # Group candidates by domain
    for domain, results in domain_results.items():
        if not isinstance(results, list):
            continue

        # Create teams for this domain
        team_count = max(1, len(results) // per_group)
        teams = []

        for i in range(team_count):
            start_idx = i * per_group
            end_idx = min(start_idx + per_group, len(results))
            team_members = results[start_idx:end_idx]

            team = {
                "domain": domain,
                "team_id": f"{domain}_team_{i+1}",
                "members": team_members,
                "size": len(team_members),
            }
            teams.append(team)

        # Handle remaining candidates
        remaining_start = team_count * per_group
        if remaining_start < len(results):
            remaining = results[remaining_start:]
            team = {
                "domain": domain,
                "team_id": f"{domain}_team_{team_count + 1}",
                "members": remaining,
                "size": len(remaining),
            }
            teams.append(team)

        groups[domain] = teams

    return json.dumps({
        "groups": groups,
        "total_teams": sum(len(teams) for teams in groups.values()),
        "per_group": per_group,
    })


def validate_group_balance(groups_json: str, max_size_variance: float = 0.3) -> str:
    """
    Validate that groups are balanced and no team is too large.

    Args:
        groups_json: JSON string with grouped candidates
        max_size_variance: Maximum allowed variance (30% by default)

    Returns:
        JSON with validation results
    """
    try:
        data = json.loads(groups_json)
    except json.JSONDecodeError:
        return json.dumps({"valid": False, "error": "Invalid JSON input"})

    groups = data.get("groups", {})
    validation = {
        "valid": True,
        "total_teams": 0,
        "total_members": 0,
        "warnings": [],
    }

    all_sizes = []

    for domain, teams in groups.items():
        for team in teams:
            size = team.get("size", 0)
            all_sizes.append(size)
            validation["total_members"] += size
            validation["total_teams"] += 1

            if size > 10:
                validation["warnings"].append(
                    f"Team {team.get('team_id')} is large ({size} members)"
                )
            if size == 0:
                validation["valid"] = False
                validation["warnings"].append(
                    f"Team {team.get('team_id')} is empty"
                )

    # Check variance
    if all_sizes:
        avg_size = sum(all_sizes) / len(all_sizes)
        max_dev = max(abs(size - avg_size) for size in all_sizes) / avg_size
        if max_dev > max_size_variance:
            validation["warnings"].append(
                f"Group size variance is high ({max_dev:.1%})"
            )

    validation["average_team_size"] = (
        validation["total_members"] / validation["total_teams"]
        if validation["total_teams"] > 0
        else 0
    )
    return json.dumps(validation)


def create_team_summary(team_json: str) -> str:
    """
    Generate a summary description for a team.

    Args:
        team_json: JSON string with team data

    Returns:
        JSON with team summary
    """
    try:
        team = json.loads(team_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    domain = team.get("domain", "Unknown")
    team_id = team.get("team_id", "Unknown")
    members = team.get("members", [])
    size = team.get("size", 0)

    # Extract member names
    member_names = []
    for member in members:
        if isinstance(member, dict):
            member_names.append(member.get("name", "Unknown"))
        else:
            member_names.append(str(member))

    summary = {
        "team_id": team_id,
        "domain": domain,
        "size": size,
        "member_names": member_names,
        "description": f"{domain.title()} Team '{team_id}' with {size} specialists: {', '.join(member_names[:3])}",
    }

    return json.dumps(summary)
