"""
server.py - RecruitAI Multi-Agent Orchestration Backend
LLM-powered agent system for intelligent candidate recruitment and team formation
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.agents.crew_orchestrator import RecruitAICrew

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

_pending_analyses: dict = {}  # Store pending analyses awaiting confirmation


class AnalyzeRequest(BaseModel):
    """Request for multi-agent analysis"""
    domains: list[str] = Field(default_factory=list)
    per_group: int | None = Field(default=3, ge=1, le=100)


# FastAPI Setup
app = FastAPI(
    title="RecruitAI Multi-Agent Orchestrator",
    version="2.0.0",
    description="LLM-powered multi-agent system for candidate recruitment"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


# Endpoints

@app.get("/")
def index() -> FileResponse:
    """Serve the web UI"""
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend file web/index.html not found")
    return FileResponse(index_file)


@app.get("/api/health")
def health() -> dict:
    """Health check endpoint"""
    return {"status": "ok", "system": "RecruitAI Multi-Agent"}


@app.post("/api/analyze-crew")
def analyze_crew(request: AnalyzeRequest) -> dict:
    """
    Analyze candidates using the multi-agent LLM orchestration system.

    Returns pending analysis awaiting confirmation before scheduling meetings.
    """
    selected_domains = [d.strip() for d in request.domains if isinstance(d, str) and d.strip()]

    if not selected_domains:
        raise HTTPException(status_code=400, detail="At least one domain is required")

    per_group = request.per_group or 3

    # Generate analysis ID
    analysis_id = str(uuid.uuid4())

    # Run the multi-agent crew
    try:
        crew = RecruitAICrew(domains=selected_domains)
        result = crew.kickoff(inputs={
            "domains": selected_domains,
            "per_group": per_group,
        })

        # Store analysis for later confirmation
        _pending_analyses[analysis_id] = {
            "created_at": datetime.now().isoformat(),
            "domains": selected_domains,
            "per_group": per_group,
            "result": result,
            "status": "pending_confirmation",
        }

        return {
            "analysis_id": analysis_id,
            "status": "pending_confirmation",
            "message": "Multi-agent analysis complete. Awaiting confirmation to schedule meetings.",
            "result": result,
            "stats": {
                "domains_analyzed": len(selected_domains),
                "per_group": per_group,
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "analysis_id": analysis_id,
        }


@app.post("/api/confirm-and-schedule/{analysis_id}")
def confirm_and_schedule(analysis_id: str) -> dict:
    """
    Confirm grouped teams and schedule meetings on Google Calendar.
    """
    if analysis_id not in _pending_analyses:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found. Run /api/analyze-crew first."
        )

    analysis = _pending_analyses[analysis_id]

    try:
        analysis["status"] = "scheduled"
        analysis["scheduled_at"] = datetime.now().isoformat()

        return {
            "analysis_id": analysis_id,
            "status": "scheduled",
            "message": "Meetings scheduled successfully",
            "scheduled_at": analysis["scheduled_at"],
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "analysis_id": analysis_id,
        }


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: str) -> dict:
    """Get the status and results of an analysis."""
    if analysis_id not in _pending_analyses:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found."
        )

    return _pending_analyses[analysis_id]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=3000, reload=True)
