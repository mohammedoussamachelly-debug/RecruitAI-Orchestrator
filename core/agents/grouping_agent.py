"""Grouping Agent - Creates optimal candidate teams"""

from core.tools.grouping_tools import (
    group_by_domain,
    validate_group_balance,
)


def create_grouping_tools():
    """Create tool functions for grouping candidates"""

    def group_and_validate_candidates(search_results_json, per_group=3):
        """Group candidates into balanced teams"""
        grouped = group_by_domain(search_results_json, per_group=per_group)
        return grouped

    return [group_and_validate_candidates]


def create_grouping_agent():
    """Create Grouping Agent"""
    return {
        "role": "Team Formation Specialist",
        "goal": "Create balanced teams with complementary expertise",
    }


def create_grouping_task(agent):
    """Create task for Grouping Agent"""
    return {
        "description": "Group candidates into balanced teams",
        "agent": agent,
    }
