"""Tools for parsing CVs and extracting candidate information"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pdfplumber
from docx import Document


def parse_cvs_tool(folder_path: str = "cvs") -> List[Dict[str, Any]]:
    """
    Extract text from all PDFs and DOCX files in the specified folder.

    Args:
        folder_path: Path to folder containing CV files

    Returns:
        List of dicts with 'name' (filename) and 'text' (extracted content)
    """
    cv_folder = Path(folder_path)
    if not cv_folder.exists():
        return []

    candidates = []

    # Process PDF files
    for pdf_file in cv_folder.glob("*.pdf"):
        try:
            with pdfplumber.open(pdf_file) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                candidates.append({"name": pdf_file.stem, "text": text})
        except Exception as e:
            print(f"Error parsing {pdf_file}: {e}")

    # Process DOCX files
    for docx_file in cv_folder.glob("*.docx"):
        try:
            doc = Document(docx_file)
            text = "\n".join(para.text for para in doc.paragraphs)
            candidates.append({"name": docx_file.stem, "text": text})
        except Exception as e:
            print(f"Error parsing {docx_file}: {e}")

    return candidates


def extract_candidate_info(text: str) -> Dict[str, Any]:
    """
    Extract structured candidate information from CV text using regex patterns.
    Fallback when LLM extraction fails.

    Args:
        text: Raw CV text

    Returns:
        Dict with extracted fields: name, email, phone, skills, experience, education
    """
    # Email pattern
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    email = email_match.group() if email_match else "N/A"

    # Phone pattern (various formats)
    phone_match = re.search(
        r"(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text
    )
    phone = phone_match.group() if phone_match else "N/A"

    # Skills (look for common skill keywords)
    skills = []
    skill_keywords = [
        "python",
        "javascript",
        "java",
        "react",
        "node",
        "sql",
        "mongodb",
        "aws",
        "docker",
        "kubernetes",
        "git",
        "machine learning",
        "ai",
        "data science",
    ]
    for skill in skill_keywords:
        if skill.lower() in text.lower():
            skills.append(skill.title())

    # Education (look for degree patterns)
    education = []
    degree_patterns = [
        r"(Bachelor|B\.S\.|B\.Sc\.|B\.A\.)",
        r"(Master|M\.S\.|M\.Sc\.|M\.A\.)",
        r"(PhD|Ph\.D\.)",
    ]
    for pattern in degree_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        education.extend(matches)

    return {
        "email": email,
        "phone": phone,
        "skills": list(set(skills)) if skills else ["N/A"],
        "experience": "N/A",  # Would need NLP for this
        "education": list(set(education)) if education else ["N/A"],
    }


def validate_extraction(data: Dict[str, Any]) -> bool:
    """
    Validate extracted candidate data quality.

    Args:
        data: Extracted candidate information

    Returns:
        True if data passes validation, False otherwise
    """
    # Check for required fields
    required_fields = ["email", "phone"]
    for field in required_fields:
        if field not in data or data[field] == "N/A":
            continue

    # Email validation
    if data.get("email") != "N/A":
        if not re.match(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", data["email"]):
            return False

    # Phone validation (basic check)
    if data.get("phone") != "N/A":
        if len(re.sub(r"\D", "", data["phone"])) < 10:
            return False

    return True
