# RecruitAI-Orchestrator                                                      
                                                                                
  An intelligent staffing automation system that analyzes candidate CVs,        
  semantically groups them by professional domain, forms balanced teams, and    
  schedules kick-off meetings — all driven by a 5-agent AI pipeline.            
                                                                                
  ---

  ## How It Works

  CVs (PDF/DOCX)
       │
       ▼
  ┌─────────────────┐
  │  CV Parser Agent │  ── Extracts name, email, skills, education, experience
  └────────┬────────┘                                                           
           │
           ▼                                                                    
  ┌──────────────────────┐                                                    
  │  Embeddings Agent     │  ── Encodes each profile into a 384-dim semantic
  vector
  └────────┬─────────────┘
           │                                                                    
           ▼
  ┌──────────────────┐                                                          
  │   Search Agent    │  ── Matches candidates to selected domains via Qdrant 
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────────┐                                                      
  │   Grouping Agent      │  ── Forms balanced teams with complementary skill
  sets                                                                          
  └────────┬─────────────┘                                                    
           │
           ▼
  ┌──────────────────────┐
  │   Calendar Agent      │  ── Schedules kick-offs, syncs & 1:1s on Google     
  Calendar
  └──────────────────────┘                                                      
           │                                                                  
           ▼
     Web UI (results + chart visualization)
     
  Each agent uses **GPT-4o-mini** (via OpenRouter) for reasoning, with graceful
  fallbacks to regex extraction and keyword search when the LLM or vector DB is 
  unavailable.
                                                                                
  ---                                                                         

  ## Features

  - **Semantic CV matching** — cosine similarity on sentence-transformer        
  embeddings, not just keyword search
  - **Multi-domain support** — Education, Digital, Social, Backend, Frontend,   
  Data Science, and more                                                      
  - **Balanced team formation** — max 10 members per team, ≤30% size variance
  across groups
  - **LLM reasoning traces** — every agent logs its decision rationale
  - **Google Calendar integration** — automatic meeting scheduling after        
  confirming results
  - **Three-tier fallback** — OpenRouter + Qdrant → regex + keyword search →    
  basic contact extraction                                                    
  - **Modern web UI** — dark glassmorphism design with animated particle
  background and interactive donut chart                                        
   
  ---                                                                           
                                                                              
  ## Tech Stack

  | Layer | Technology |
  |---|---|
  | Backend | FastAPI + Uvicorn (port 7000) |
  | Agent Orchestration | CrewAI v0.11.2 + LangChain |
  | LLM | GPT-4o-mini via OpenRouter |
  | Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |                   
  | Vector DB | Qdrant Cloud (cosine similarity) |
  | Document Parsing | pdfplumber, python-docx |                                
  | Calendar | Google Calendar API |                                            
  | Frontend | Vanilla JS, HTML5, CSS3 |
                                                                                
  ---                                                                         

  ## Project Structure

  RecruitAI-Orchestrator/
  ├── server.py                    # FastAPI app & API routes
  ├── main.py                      # Entry point                                
  ├── requirements.txt
  │                                                                             
  ├── core/                                                                   
  │   ├── agents/
  │   │   ├── crew_orchestrator.py # Main 5-agent pipeline
  │   │   ├── cv_parser_agent.py
  │   │   ├── embeddings_agent.py                                               
  │   │   ├── search_agent.py
  │   │   ├── grouping_agent.py                                                 
  │   │   └── calendar_agent.py                                               
  │   │
  │   └── tools/
  │       ├── cv_parser_tools.py                                                
  │       ├── embedding_tools.py
  │       ├── search_tools.py                                                   
  │       ├── grouping_tools.py                                               
  │       └── calendar_tools.py
  │
  ├── web/                                                                      
  │   ├── index.html
  │   ├── app.js                                                                
  │   └── styles.css                                                          
  │
  └── cvs/                         # Drop PDF/DOCX files here (gitignored)

  ---

  ## API Endpoints                                                              
   
  | Method | Endpoint | Description |                                           
  |---|---|---|                                                               
  | `GET` | `/` | Serves the web UI |
  | `GET` | `/api/health` | System status check |
  | `POST` | `/api/analyze-crew` | Trigger multi-agent analysis (returns
  `analysis_id`) |                                                              
  | `GET` | `/api/analysis/{id}` | Retrieve analysis results |
  | `POST` | `/api/confirm-and-schedule/{id}` | Confirm results and schedule    
  calendar meetings |                                                         
  | `GET` | `/api/domains` | List available professional domains |
                                                                                
  ---
                                                                                
  ## Setup                                                                    

  ### Prerequisites

  - Python 3.9+
  - An [OpenRouter](https://openrouter.ai/) API key (for GPT-4o-mini)
  - A [Qdrant Cloud](https://cloud.qdrant.io/) cluster
  - Google Calendar API credentials (optional, for meeting scheduling)          
   
  ### Install                                                                   
                                                                              
  ```bash
  git clone
  https://github.com/mohammedoussamachelly-debug/RecruitAI-Orchestrator.git
  cd RecruitAI-Orchestrator
  pip install -r requirements.txt                                               
   
  Configure                                                                     
                                                                              
  Create a .env file:

  OPENROUTER_API_KEY=your_openrouter_key
  QDRANT_URL=https://your-cluster.qdrant.io
  QDRANT_API_KEY=your_qdrant_key                                                
  GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json  # optional
                                                                                
  Run                                                                         

  1. Place CV files (PDF or DOCX) in the cvs/ folder                            
  2. Start the server:
                                                                                
  python server.py                                                            
  # or
  python main.py

  3. Open your browser at http://localhost:7000

  ---
  Workflow

  1. Select domains — choose which professional domains to recruit for
  2. Analyze — the 5-agent pipeline processes all CVs in cvs/
  3. Review results — see ranked candidate groups with AI-generated explanations
   and a domain chart
  4. Confirm & Schedule — trigger Google Calendar meeting creation for each team
                                                                              
  ---    
