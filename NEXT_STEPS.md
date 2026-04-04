# RecruitAI Multi-Agent Implementation Plan

**Last Updated:** 2026-04-01  
**Status:** Ready for Implementation Tomorrow  
**Current State:** Beautiful UI with expandable circle ✅ | Need: Multi-Agent Backend 🚀

---

## What We Accomplished Today ✅

### Frontend (COMPLETE)
- ✅ Built beautiful donut/circular chart with glassmorphism design
- ✅ Created expandable circle view with smooth animations
- ✅ Added candidate names popup with staggered reveals
- ✅ Perfect centering and responsive design
- ✅ Running on http://localhost:7002

### Backend (PARTIAL)
- ✅ FastAPI server with CV analysis
- ✅ OpenRouter LLM integration for CV extraction
- ✅ Qdrant vector database connection
- ✅ Semantic grouping of candidates
- ❌ **NO multi-agent orchestration yet** (THIS IS NEXT)

---

## What We're Building Tomorrow 🚀

### GOAL: Multi-Agent System with CrewAI

Transform RecruitAI from **single synchronous pipeline** to **specialized agent team**:

```
┌─────────────────────────────────────────┐
│  ORCHESTRATOR (CrewAI Crew)             │
└─────────────────────────────────────────┘
         ↓ Manages ↓
┌────────────────────────────────────────────────────────┐
│ 5 SPECIALIZED AGENTS                                   │
├────────────────────────────────────────────────────────┤
│ 1. CV Parser Agent      → Extract text from PDFs/DOCX  │
│ 2. Embeddings Agent     → Create vector representations│
│ 3. Search Agent         → Query Qdrant, rank results   │
│ 4. Grouping Agent       → Create optimal teams         │
│ 5. Calendar Agent       → Schedule meetings + sync      │
└────────────────────────────────────────────────────────┘
```

### Key Differences from Today
- **Before:** 1 Agent → 8 Tools (linear, deterministic)
- **After:** 5 Agents → Each has own tools (specialized, parallel)
- **Result:** Better reasoning, easier to debug, more maintainable

---

## Implementation Roadmap

### PHASE 1: Setup CrewAI
```bash
# Install
pip install crewai crewai-tools langchain-openrouter

# Files to create
core/agents/
  ├── __init__.py
  ├── cv_parser_agent.py      # Agent 1
  ├── embeddings_agent.py     # Agent 2
  ├── search_agent.py         # Agent 3
  ├── grouping_agent.py       # Agent 4
  ├── calendar_agent.py       # Agent 5
  └── crew_orchestrator.py    # Main orchestrator
```

### PHASE 2: Create Each Agent
Each agent follows this structure:

```python
from crewai import Agent, Task
from langchain_openrouter import ChatOpenRouter

# Agent definition
agent = Agent(
    role="Role Name",
    goal="What this agent tries to achieve",
    tools=[tool1, tool2, ...],  # Agent's specific tools
    llm=ChatOpenRouter(model="openai/gpt-4o-mini"),
    verbose=True
)

# Task for this agent
task = Task(
    description="Specific task to accomplish",
    agent=agent,
    expected_output="What the task should produce"
)
```

### PHASE 3: Orchestration with Crew
```python
from crewai import Crew

crew = Crew(
    agents=[agent1, agent2, agent3, agent4, agent5],
    tasks=[task1, task2, task3, task4, task5],
    verbose=True,
    max_iterations=10
)

result = crew.kickoff()
```

### PHASE 4: Frontend Integration
- Update `/api/analyze` endpoint to use `crew.kickoff()`
- Add confirmation step (display results, wait for user approval)
- On approval: trigger calendar agent flow
- Show planning in a nice timeline view

---

## Detailed Agent Specifications

### AGENT 1: CV Parser Agent
**Role:** Extract candidate information  
**Tools:**
- `parse_cvs_tool(folder_path)` → Extract text from all CVs
- `extract_candidate_info(text)` → Regex fallback if LLM fails
- `validate_extraction(data)` → Check quality

**Task:** "Parse all CVs in 'cvs/' folder and extract: name, email, phone, skills, experience, education"

**Output:** JSON list of candidates with structured data

---

### AGENT 2: Embeddings Agent
**Role:** Convert candidates to vectors  
**Tools:**
- `embed_candidates(candidates_json)` → Create 384-dim vectors
- `normalize_embeddings(embeddings)` → Normalize for Qdrant
- `validate_embeddings(embeddings)` → Check dimension

**Task:** "Create vector embeddings for each candidate using sentence-transformers"

**Output:** JSON with candidates + their embeddings

---

### AGENT 3: Search Agent
**Role:** Find best matches per domain  
**Tools:**
- `search_qdrant(domain, embedding, top_k)` → Query vector DB
- `rank_by_similarity(results)` → Sort by score
- `fallback_keyword_search(domain, candidates)` → If Qdrant fails

**Task:** "For each domain, find top candidates using semantic search"

**Output:** Ranked candidates per domain

---

### AGENT 4: Grouping Agent
**Role:** Create optimal teams  
**Tools:**
- `group_by_domain(candidates, per_group)` → Distribute fairly
- `validate_group_balance(groups)` → Check no overflow
- `create_team_summary(group)` → Generate description

**Task:** "Group candidates into teams ensuring balanced expertise"

**Output:** Final groups with summaries ready for display

---

### AGENT 5: Calendar Agent
**Role:** Schedule meetings  
**Tools:**
- `confirm_groups(groups_json)` → Wait user approval ⏳
- `create_meeting_plan(groups)` → Generate kick-off, sync, 1:1s
- `send_to_google_calendar(plan)` → Add to everyone's calendar
- `send_confirmation_email(participants)` → Notify all

**Task:** "Create meetings and sync with Google Calendar for each team member"

**Output:** Confirmation that all calendar invites sent ✅

---

## Critical Implementation Details

### 1. Agent Communication
Agents pass data through **Task Outputs**:

```
Agent1 → Task1 → OUTPUT: parsed_candidates
            ↓
        Agent2 → Task2 → OUTPUT: candidates_with_embeddings
                    ↓
                Agent3 → Task3 → OUTPUT: ranked_by_domain
                            ↓
                        Agent4 → Task4 → OUTPUT: final_groups
                                    ↓
                                Agent5 → Task5 → OUTPUT: ✅ Calendar synced
```

### 2. Error Handling & Fallbacks
Each agent has fallback tools:

```
PRIMARY TOOL fails → FALLBACK TOOL
┌─────────────────────────────────┐
│ OpenRouter unavailable          │
└──→ Use Regex extraction (basic) │
│ Qdrant unavailable              │
└──→ Use keyword matching         │
│ Google Calendar API fails       │
└──→ Generate ICS file instead    │
```

### 3. Confirmation Flow
Agent 5 (Calendar) must WAIT for user confirmation before sending calendar invites:

```python
# In calendar_agent.py
def confirm_and_schedule(groups_json):
    # Return confirmation prompt
    return {
        "status": "pending_confirmation",
        "groups": groups_json,
        "action_url": "/api/confirm-schedule"
    }

# Frontend shows "Confirmer & Créer Réunions" button
# User clicks → POST /api/confirm-schedule
# Agent5 then runs send_to_google_calendar()
```

---

## Updated FastAPI Endpoints

### Current (will be replaced)
```
POST /api/analyze → Returns groups immediately
```

### New with CrewAI
```
POST /api/analyze-crew
  ↓ Returns: analysis_id + groups (pending confirmation)

POST /api/confirm-and-schedule/{analysis_id}
  ↓ User confirms, triggers Calendar Agent
  ↓ Returns: Calendar invites sent ✅
```

---

## File Structure After Implementation

```
recruitai/
├── core/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── cv_parser_agent.py
│   │   ├── embeddings_agent.py
│   │   ├── search_agent.py
│   │   ├── grouping_agent.py
│   │   ├── calendar_agent.py
│   │   └── crew_orchestrator.py
│   ├── tools/
│   │   ├── cv_parser_tools.py
│   │   ├── embedding_tools.py
│   │   ├── search_tools.py
│   │   ├── grouping_tools.py
│   │   └── calendar_tools.py
│   ├── analyzer.py (keep)
│   ├── parser.py (keep)
│   ├── rag.py (keep)
│   └── vectorize.py (keep)
├── server.py (UPDATE endpoints)
├── web/ (NO CHANGES)
├── requirements.txt (ADD crewai, crewai-tools)
└── NEXT_STEPS.md (this file)
```

---

## Tomorrow's Exact Tasks

1. **Create agents directory structure** (5 min)
2. **Agent 1: CV Parser** - Parse PDFs + fallback (15 min)
3. **Agent 2: Embeddings** - Vector creation (10 min)
4. **Agent 3: Search** - Qdrant queries (10 min)
5. **Agent 4: Grouping** - Team creation (10 min)
6. **Agent 5: Calendar** - Google Calendar sync + confirmation (20 min)
7. **Crew Orchestrator** - Connect all agents (15 min)
8. **Update API endpoints** - Replace /api/analyze (10 min)
9. **Test full flow** - End-to-end testing (20 min)

**Total: ~2 hours for full implementation**

---

## Git Commit Messages for Tomorrow

```
feat(agents): Add CV Parser agent with fallback extraction

feat(agents): Add Embeddings agent for vector creation

feat(agents): Add Search agent with Qdrant integration

feat(agents): Add Grouping agent for team creation

feat(agents): Add Calendar agent with Google Calendar sync

feat(agents): Integrate CrewAI orchestrator

refactor(api): Update endpoints to use multi-agent crew

test(crew): End-to-end test of complete agent flow
```

---

## Important Notes

- ✅ Keep all existing `core/` code (reuse as fallbacks)
- ✅ Frontend stays UNCHANGED (URL/responses compatible)
- ✅ Use same LangChain LLM setup (OpenRouter API)
- ❌ Don't modify web/ folder
- 🔐 Make sure credentials.json exists for Google Calendar

---

## Quick Reference: CrewAI Syntax

```python
# Define agent
agent = Agent(
    role="Role Name",
    goal="Goal description",
    tools=[tool1, tool2],
    llm=llm,
    verbose=True
)

# Define task
task = Task(
    description="What to do",
    agent=agent,
    expected_output="What we expect back"
)

# Run crew
crew = Crew(agents=[...], tasks=[...])
result = crew.kickoff(inputs={"domains": [...], "per_group": 3})
```

---

## Questions for Tomorrow

- Should agents run in parallel or sequential? (SEQUENTIAL for now, safer)
- How long should confirmation wait? (No timeout, user clicks)
- Should we log agent reasoning? (YES, for debugging)
- Archive old single-agent code? (Keep in git history)

---

**START TOMORROW WITH:** core/agents/__init__.py (empty file)  
**THEN:** core/agents/cv_parser_agent.py  
**ENDPOINT:** Should be fully working by end of day! 🚀

---

*Last note: This is a big refactor but will make RecruitAI production-ready and scalable!*
