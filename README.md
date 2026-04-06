# RecruitAI

RecruitAI is a staffing assistant for associations. It analyzes CVs from the `cvs/` folder, extracts candidate data, builds embeddings, groups candidates by domain, and schedules meetings.

## Highlights

- LangGraph pipeline with conditional routing (`quality_gate`)
- Debug endpoint exposing executed stage path
- LLM-powered crew workflow still available
- FastAPI backend + web interface

## Main workflow (LangGraph)

```text
parse_cvs -> create_embeddings -> search_domain -> group_teams -> quality_gate -> schedule_meetings
```

If grouping quality is weak, `quality_gate` can route once to `regroup_teams` before scheduling.

## API endpoints

- `GET /api/health`
- `POST /api/analyze-pipeline`
- `POST /api/analyze-pipeline-debug`
- `POST /api/analyze-crew`
- `GET /api/analysis/{analysis_id}`
- `POST /api/confirm-and-schedule/{analysis_id}`

### Example request

```json
{
  "domains": ["backend", "frontend"],
  "per_group": 3,
  "cv_folder": "cvs"
}
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env`:

```env
OPENROUTER_API_KEY=your_openrouter_key
QDRANT_HOST=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key
ENABLE_SEMANTIC_RAG=1
```

3. Put CV files (`.pdf` / `.docx`) in `cvs/`.

4. Run server:

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 7000
```

## Project structure

```text
├── server.py
├── core/
│   ├── agents/
│   │   ├── crew_orchestrator.py
│   │   ├── langgraph_pipeline.py
│   │   ├── cv_parser_agent.py
│   │   ├── embeddings_agent.py
│   │   ├── search_agent.py
│   │   ├── grouping_agent.py
│   │   └── calendar_agent.py
│   └── tools/
│       ├── cv_parser_tools.py
│       ├── embedding_tools.py
│       ├── search_tools.py
│       ├── grouping_tools.py
│       └── calendar_tools.py
├── web/
├── cvs/
├── requirements.txt
└── README.md
```

## Notes

- Legacy first pipeline files were removed.
- The project now centers on the LangGraph pipeline.
