"""CV Parser Agent - Extracts candidate information from CVs"""

import json
from core.tools.cv_parser_tools import (
    parse_cvs_tool,
    extract_candidate_info,
    validate_extraction,
)


def create_cv_parser_tools():
    """Create tool functions for CV parsing"""

    def parse_and_extract_cvs():
        """Parse CVs and extract candidate information"""
        candidates = parse_cvs_tool(folder_path="cvs")

        extracted_candidates = []
        for candidate in candidates:
            info = extract_candidate_info(candidate.get("text", ""))
            is_valid = validate_extraction(info)

            extracted_candidates.append({
                "name": candidate.get("name"),
                "text": candidate.get("text", "")[:1000],
                **info,
                "valid": is_valid,
            })

        return json.dumps(extracted_candidates)

    return [parse_and_extract_cvs]


def create_cv_parser_agent():
    """
    Create CV Parser Agent.

    Role: Extract candidate information from CV documents
    Tools: PDF/DOCX parsing, candidate data extraction, validation
    """
    return {
        "role": "CV Parser Specialist",
        "goal": "Extract structured candidate information from CV documents",
    }


def create_cv_parser_task(agent):
    """Create task for CV Parser Agent"""
    return {
        "description": "Parse all CV documents and extract information",
        "agent": agent,
    }
