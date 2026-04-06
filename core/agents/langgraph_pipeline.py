"""LangGraph-backed grep-style pipeline for RecruitAI.

Pipeline shape:
parse_cvs -> create_embeddings -> search_domain -> group_teams -> quality_gate -> schedule_meetings
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from core.tools.calendar_tools import create_meeting_plan
from core.tools.cv_parser_tools import extract_candidate_info, parse_cvs_tool
from core.tools.embedding_tools import embed_candidates, normalize_embeddings
from core.tools.grouping_tools import group_by_domain, validate_group_balance
from core.tools.search_tools import fallback_keyword_search, rank_by_similarity

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    END = None
    StateGraph = None


class RecruitPipelineState(TypedDict, total=False):
    domains: List[str]
    per_group: int
    cv_folder: str
    candidates: List[Dict[str, Any]]
    embeddings: Any
    search_results: Dict[str, Any]
    groups: Any
    meetings: Any
    metadata: Dict[str, Any]
    quality_gate: Dict[str, Any]
    regroup_attempts: int
    errors: List[str]
    status: str


def _append_stage(state: RecruitPipelineState, stage_name: str, result: Any) -> None:
    metadata = state.setdefault(
        "metadata",
        {
            "timestamp": datetime.now().isoformat(),
            "stages": [],
            "engine": "langgraph" if LANGGRAPH_AVAILABLE else "sequential_fallback",
        },
    )
    metadata["stages"].append(
        {
            "name": stage_name,
            "timestamp": datetime.now().isoformat(),
            "result_type": type(result).__name__,
        }
    )


def parse_cvs_node(state: RecruitPipelineState) -> RecruitPipelineState:
    candidates_raw = parse_cvs_tool(folder_path=state.get("cv_folder", "cvs"))

    extracted: List[Dict[str, Any]] = []
    for candidate in candidates_raw or []:
        info = extract_candidate_info(candidate.get("text", ""))
        extracted.append(
            {
                "name": candidate.get("name"),
                "text": candidate.get("text", "")[:500],
                **info,
            }
        )

    state["candidates"] = extracted
    _append_stage(state, "parse_cvs", extracted)
    return state


def create_embeddings_node(state: RecruitPipelineState) -> RecruitPipelineState:
    candidates_json = json.dumps(state.get("candidates", []))
    embeddings = embed_candidates(candidates_json)
    state["embeddings"] = normalize_embeddings(embeddings)
    _append_stage(state, "create_embeddings", state["embeddings"])
    return state


def search_domain_node(state: RecruitPipelineState) -> RecruitPipelineState:
    domains = state.get("domains", [])
    embeddings_payload = state.get("embeddings", [])
    embeddings_json = (
        embeddings_payload
        if isinstance(embeddings_payload, str)
        else json.dumps(embeddings_payload)
    )

    domain_results: Dict[str, Any] = {}
    for domain in domains:
        result = fallback_keyword_search(domain, embeddings_json)
        ranked = rank_by_similarity(result)
        domain_results[domain] = json.loads(ranked)

    search_results = {
        "domains": domain_results,
        "total_domains": len(domains),
    }
    state["search_results"] = search_results
    _append_stage(state, "search_domain", search_results)
    return state


def group_teams_node(state: RecruitPipelineState) -> RecruitPipelineState:
    grouped = group_by_domain(
        json.dumps(state.get("search_results", {})),
        per_group=int(state.get("per_group", 3)),
    )

    validation_raw = validate_group_balance(grouped)
    try:
        validation = json.loads(validation_raw)
    except Exception:
        validation = {"valid": True, "warnings": [], "raw": validation_raw}

    state["groups"] = grouped
    state.setdefault("metadata", {})["group_validation"] = validation
    _append_stage(state, "group_teams", grouped)
    return state


def quality_gate_node(state: RecruitPipelineState) -> RecruitPipelineState:
    """Evaluate grouping quality and decide whether to continue or regroup."""
    validation = state.get("metadata", {}).get("group_validation", {})
    warnings = validation.get("warnings", []) if isinstance(validation, dict) else []
    valid = validation.get("valid", True) if isinstance(validation, dict) else True
    attempts = int(state.get("regroup_attempts", 0))

    needs_regroup = (not valid or len(warnings) > 0) and attempts < 1

    decision = {
        "action": "regroup" if needs_regroup else "proceed",
        "reason": "quality_warnings" if needs_regroup else "quality_ok",
        "warnings": warnings,
        "attempts": attempts,
    }

    state["quality_gate"] = decision
    _append_stage(state, "quality_gate", decision)
    return state


def regroup_teams_node(state: RecruitPipelineState) -> RecruitPipelineState:
    """Try one regroup pass with a slightly adjusted team size."""
    attempts = int(state.get("regroup_attempts", 0)) + 1
    current_per_group = int(state.get("per_group", 3))
    adjusted_per_group = max(2, current_per_group - 1)

    grouped = group_by_domain(
        json.dumps(state.get("search_results", {})),
        per_group=adjusted_per_group,
    )

    validation_raw = validate_group_balance(grouped)
    try:
        validation = json.loads(validation_raw)
    except Exception:
        validation = {"valid": True, "warnings": [], "raw": validation_raw}

    state["groups"] = grouped
    state["per_group"] = adjusted_per_group
    state["regroup_attempts"] = attempts
    state.setdefault("metadata", {})["group_validation"] = validation

    _append_stage(
        state,
        "regroup_teams",
        {
            "per_group": adjusted_per_group,
            "attempts": attempts,
            "validation": validation,
        },
    )
    return state


def _quality_route(state: RecruitPipelineState) -> str:
    decision = state.get("quality_gate", {})
    return "regroup_teams" if decision.get("action") == "regroup" else "schedule_meetings"


def schedule_meetings_node(state: RecruitPipelineState) -> RecruitPipelineState:
    meetings = create_meeting_plan(
        json.dumps(state.get("groups", {}))
        if not isinstance(state.get("groups"), str)
        else state.get("groups")
    )
    state["meetings"] = meetings
    _append_stage(state, "schedule_meetings", meetings)
    return state


def _run_sequential_fallback(initial_state: RecruitPipelineState) -> RecruitPipelineState:
    state = parse_cvs_node(initial_state)
    state = create_embeddings_node(state)
    state = search_domain_node(state)
    state = group_teams_node(state)
    state = quality_gate_node(state)
    if state.get("quality_gate", {}).get("action") == "regroup":
        state = regroup_teams_node(state)
    state = schedule_meetings_node(state)
    return state


def build_grep_style_graph():
    """Build a LangGraph workflow for the grep-style pipeline."""
    if not LANGGRAPH_AVAILABLE:
        return None

    graph = StateGraph(RecruitPipelineState)
    graph.add_node("parse_cvs", parse_cvs_node)
    graph.add_node("create_embeddings", create_embeddings_node)
    graph.add_node("search_domain", search_domain_node)
    graph.add_node("group_teams", group_teams_node)
    graph.add_node("quality_gate", quality_gate_node)
    graph.add_node("regroup_teams", regroup_teams_node)
    graph.add_node("schedule_meetings", schedule_meetings_node)

    graph.set_entry_point("parse_cvs")
    graph.add_edge("parse_cvs", "create_embeddings")
    graph.add_edge("create_embeddings", "search_domain")
    graph.add_edge("search_domain", "group_teams")
    graph.add_edge("group_teams", "quality_gate")
    graph.add_conditional_edges(
        "quality_gate",
        _quality_route,
        {
            "regroup_teams": "regroup_teams",
            "schedule_meetings": "schedule_meetings",
        },
    )
    graph.add_edge("regroup_teams", "schedule_meetings")
    graph.add_edge("schedule_meetings", END)
    return graph.compile()


def run_langgraph_pipeline(
    domains: Optional[List[str]] = None,
    per_group: int = 3,
    cv_folder: str = "cvs",
) -> Dict[str, Any]:
    """Run grep-style pipeline on LangGraph (with graceful fallback)."""
    initial_state: RecruitPipelineState = {
        "domains": domains or ["backend", "frontend", "data_science", "devops", "fullstack"],
        "per_group": per_group,
        "cv_folder": cv_folder,
        "errors": [],
        "regroup_attempts": 0,
        "status": "running",
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "stages": [],
            "engine": "langgraph" if LANGGRAPH_AVAILABLE else "sequential_fallback",
            "pipeline_style": "grep",
        },
    }

    try:
        graph = build_grep_style_graph()
        if graph is None:
            final_state = _run_sequential_fallback(initial_state)
        else:
            final_state = graph.invoke(initial_state)

        final_state["status"] = "success"
        return {
            "status": "success",
            "data": final_state.get("meetings"),
            "groups": final_state.get("groups"),
            "search_results": final_state.get("search_results"),
            "metadata": final_state.get("metadata", {}),
            "langgraph_enabled": LANGGRAPH_AVAILABLE,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "metadata": initial_state.get("metadata", {}),
            "langgraph_enabled": LANGGRAPH_AVAILABLE,
            "timestamp": datetime.now().isoformat(),
        }
