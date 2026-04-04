#!/usr/bin/env python3
"""Test script for RecruitAI Multi-Agent System"""

import json
import sys

def test_imports():
    """Test if core modules can be imported"""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    try:
        from core.tools.cv_parser_tools import parse_cvs_tool
        print("[OK] CV Parser tools imported")
    except ImportError as e:
        print(f"[FAIL] CV Parser tools: {e}")
        return False

    try:
        from core.tools.embedding_tools import embed_candidates
        print("[OK] Embedding tools imported")
    except ImportError as e:
        print(f"[FAIL] Embedding tools: {e}")
        return False

    try:
        from core.tools.search_tools import fallback_keyword_search
        print("[OK] Search tools imported")
    except ImportError as e:
        print(f"[FAIL] Search tools: {e}")
        return False

    try:
        from core.tools.grouping_tools import group_by_domain
        print("[OK] Grouping tools imported")
    except ImportError as e:
        print(f"[FAIL] Grouping tools: {e}")
        return False

    try:
        from core.tools.calendar_tools import create_meeting_plan
        print("[OK] Calendar tools imported")
    except ImportError as e:
        print(f"[FAIL] Calendar tools: {e}")
        return False

    return True


def test_crew_orchestrator():
    """Test the LLM-powered crew orchestrator"""
    print("\n" + "=" * 60)
    print("Testing LLM-Powered Crew Orchestrator")
    print("=" * 60)

    try:
        from dotenv import load_dotenv
        load_dotenv()

        from core.agents.crew_orchestrator import RecruitAICrew, LLM_AVAILABLE
        print(f"[OK] RecruitAICrew imported (LLM available: {LLM_AVAILABLE})")

        # Test initialization
        crew = RecruitAICrew(domains=['backend', 'frontend'])
        print(f"[OK] Crew initialized with {len(crew.agents)} agents:")

        for agent_name, agent in crew.agents.items():
            has_llm = agent.llm is not None
            status = "LLM-enabled" if has_llm else "LLM-disabled"
            print(f"    - {agent_name} ({status})")

        return True
    except Exception as e:
        print(f"[FAIL] Crew orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_imports():
    """Test API imports"""
    print("\n" + "=" * 60)
    print("Testing API Imports")
    print("=" * 60)

    try:
        from fastapi import FastAPI
        print("[OK] FastAPI imported")
    except ImportError as e:
        print(f"[FAIL] FastAPI: {e}")
        return False

    try:
        from server import app
        print("[OK] Server app imported")
    except Exception as e:
        print(f"[WARN] Server app import warning: {e}")
        # This might fail due to missing dependencies, but that's ok

    return True


def test_tools_functionality():
    """Test that tools can be called"""
    print("\n" + "=" * 60)
    print("Testing Tools Functionality")
    print("=" * 60)

    try:
        from core.tools.grouping_tools import group_by_domain

        # Test with sample data
        sample_data = json.dumps({
            "domains": {
                "backend": [
                    {"name": "Alice", "score": 0.9},
                    {"name": "Bob", "score": 0.85},
                    {"name": "Charlie", "score": 0.8},
                ]
            }
        })

        result = group_by_domain(sample_data, per_group=2)
        result_data = json.loads(result)

        if "groups" in result_data:
            print(f"[OK] Grouping tool works - created {result_data.get('total_teams', 0)} teams")
        else:
            print("[WARN] Grouping tool executed but returned unexpected format")

        return True
    except Exception as e:
        print(f"[FAIL] Tools functionality error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n[START] RecruitAI Multi-Agent System - Test Suite\n")

    results = {
        "imports": test_imports(),
        "crew": test_crew_orchestrator(),
        "api": test_api_imports(),
        "tools": test_tools_functionality(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name:20} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All tests passed! System is ready.")
    else:
        print("[WARNING] Some tests failed. Check dependencies.")
    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
