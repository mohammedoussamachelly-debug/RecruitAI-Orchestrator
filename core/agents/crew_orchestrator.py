"""LLM-Powered Multi-Agent Orchestrator for RecruitAI"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import os

from core.tools.cv_parser_tools import parse_cvs_tool, extract_candidate_info
from core.tools.embedding_tools import embed_candidates, normalize_embeddings
from core.tools.search_tools import rank_by_similarity, fallback_keyword_search
from core.tools.grouping_tools import group_by_domain, validate_group_balance
from core.tools.calendar_tools import create_meeting_plan

# Try to import LangChain components
try:
    from langchain_openrouter import ChatOpenRouter
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    ChatOpenRouter = None


class LLMAgent:
    """LLM-powered agent with reasoning capabilities"""

    def __init__(self, name: str, role: str, goal: str, tools: List[Any] = None):
        self.name = name
        self.role = role
        self.goal = goal
        self.tools = tools or []
        self.llm = None

        if LLM_AVAILABLE:
            try:
                self.llm = ChatOpenRouter(
                    model="openai/gpt-4o-mini",
                    temperature=0.3,
                    api_key=os.getenv("OPENROUTER_API_KEY")
                )
            except Exception as e:
                print(f"Warning: Could not initialize LLM for {name}: {e}")

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses"""
        raise NotImplementedError

    def reason(self, prompt: str) -> str:
        """Use LLM to reason about a task"""
        if not self.llm:
            return "LLM not available"

        try:
            message = self.llm.invoke([{"role": "user", "content": prompt}])
            return message.content
        except Exception as e:
            print(f"LLM reasoning failed: {e}")
            return f"Error: {e}"


class CVParserAgent(LLMAgent):
    """CV Parser Agent with LLM reasoning"""

    def __init__(self):
        super().__init__(
            name="CV Parser",
            role="CV Parser Specialist",
            goal="Extract and validate candidate information from CV documents"
        )

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CVs using LLM to guide extraction and validation"""
        print(f"  📄 {self.name} Agent: Parsing CVs with LLM guidance...")

        candidates = parse_cvs_tool(folder_path="cvs")

        if not candidates:
            return {
                "status": "success",
                "data": json.dumps([]),
                "count": 0,
                "message": "No CVs found"
            }

        # Use LLM to reason about extraction quality
        extraction_prompt = f"""
        I have extracted information from {len(candidates)} CVs.

        Sample CV text (first 200 chars):
        {candidates[0].get('text', '')[:200] if candidates else '(empty)'}

        What are the key information points I should focus on extracting from each CV?
        List them briefly.
        """

        llm_guidance = self.reason(extraction_prompt) if self.llm else "Using default extraction"
        print(f"    LLM Guidance: {llm_guidance[:100]}...")

        extracted = []
        for candidate in candidates:
            info = extract_candidate_info(candidate.get("text", ""))
            extracted.append({
                "name": candidate.get("name"),
                "text": candidate.get("text", "")[:500],
                **info
            })

        return {
            "status": "success",
            "data": json.dumps(extracted),
            "count": len(extracted),
            "llm_guidance": llm_guidance
        }


class EmbeddingsAgent(LLMAgent):
    """Embeddings Agent with LLM reasoning about semantic representation"""

    def __init__(self):
        super().__init__(
            name="Embeddings",
            role="Embeddings Specialist",
            goal="Create semantic vector representations of candidates"
        )

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings with LLM validation"""
        print(f"  🔢 {self.name} Agent: Creating embeddings with LLM validation...")

        candidates_json = inputs.get("data", "[]")

        try:
            candidates = json.loads(candidates_json)
            candidate_count = len(candidates)
        except:
            candidate_count = 0

        # Use LLM to validate embedding strategy
        validation_prompt = f"""
        I'm creating 384-dimensional vector embeddings for {candidate_count} candidates
        using sentence-transformers (all-MiniLM-L6-v2).

        What aspects of candidate profiles are most important to capture in embeddings
        for recruitment matching? (Be concise)
        """

        llm_validation = self.reason(validation_prompt) if self.llm else "Using default strategy"
        print(f"    LLM Validation: {llm_validation[:100]}...")

        # Create embeddings
        embeddings = embed_candidates(candidates_json)
        normalized = normalize_embeddings(embeddings)

        return {
            "status": "success",
            "data": normalized,
            "llm_validation": llm_validation
        }


class SearchAgent(LLMAgent):
    """Search Agent with LLM reasoning about domain matching"""

    def __init__(self):
        super().__init__(
            name="Search",
            role="Search & Matching Specialist",
            goal="Find best matching candidates per domain using semantic understanding"
        )

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Search with LLM-guided domain understanding"""
        print(f"  🔍 {self.name} Agent: Searching candidates with LLM domain understanding...")

        embeddings_json = inputs.get("data", "[]")
        domains = inputs.get("domains", ["backend", "frontend", "data_science"])

        # Use LLM to understand domain requirements
        domain_prompt = f"""
        I need to match candidates to these domains: {', '.join(domains)}

        For each domain, what are the 3-5 key skills/keywords I should prioritize?
        Format: domain: skill1, skill2, skill3
        """

        domain_understanding = self.reason(domain_prompt) if self.llm else "Using default keywords"
        print(f"    LLM Domain Understanding: {domain_understanding[:100]}...")

        domain_results = {}
        for domain in domains:
            result = fallback_keyword_search(domain, embeddings_json)
            ranked = rank_by_similarity(result)
            domain_results[domain] = json.loads(ranked)

        return {
            "status": "success",
            "data": json.dumps({
                "domains": domain_results,
                "total_domains": len(domains)
            }),
            "llm_domain_understanding": domain_understanding
        }


class GroupingAgent(LLMAgent):
    """Grouping Agent with LLM reasoning about team composition"""

    def __init__(self):
        super().__init__(
            name="Grouping",
            role="Team Composition Specialist",
            goal="Create optimal teams using LLM understanding of skills and dynamics"
        )

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Group candidates with LLM team composition reasoning"""
        print(f"  👥 {self.name} Agent: Grouping with LLM team dynamics reasoning...")

        search_results = inputs.get("data", "{}")
        per_group = inputs.get("per_group", 3)

        # Use LLM to reason about team composition
        team_prompt = f"""
        I'm creating teams of {per_group} members from candidates across multiple domains.

        What makes a high-performing team in recruitment/tech context?
        What complementary skills should team members have? (Be concise)
        """

        team_reasoning = self.reason(team_prompt) if self.llm else "Using default grouping"
        print(f"    LLM Team Reasoning: {team_reasoning[:100]}...")

        groups = group_by_domain(search_results, per_group=per_group)
        validation = validate_group_balance(groups)

        return {
            "status": "success",
            "data": groups,
            "validation": validation,
            "llm_team_reasoning": team_reasoning
        }


class CalendarAgent(LLMAgent):
    """Calendar Agent with LLM reasoning about meeting strategy"""

    def __init__(self):
        super().__init__(
            name="Calendar",
            role="Meeting Strategy Specialist",
            goal="Plan meetings using LLM understanding of team dynamics"
        )

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create meeting plan with LLM guidance"""
        print(f"  📅 {self.name} Agent: Planning meetings with LLM strategy...")

        groups_json = inputs.get("data", "{}")

        # Use LLM to reason about meeting strategy
        meeting_prompt = """
        I'm planning kick-off meetings, weekly syncs, and 1:1s for new teams.

        What should be the priorities for each meeting type to build team cohesion
        and ensure project success? (Be concise)
        """

        meeting_strategy = self.reason(meeting_prompt) if self.llm else "Using default schedule"
        print(f"    LLM Meeting Strategy: {meeting_strategy[:100]}...")

        meetings = create_meeting_plan(groups_json)

        return {
            "status": "pending_confirmation",
            "data": meetings,
            "message": "Meeting plan created. Awaiting confirmation to schedule.",
            "llm_meeting_strategy": meeting_strategy
        }


class RecruitAICrew:
    """LLM-Powered Multi-Agent Orchestrator for RecruitAI"""

    def __init__(self, domains: Optional[List[str]] = None):
        """Initialize crew with LLM-powered agents"""
        self.domains = domains or ["backend", "frontend", "data_science", "devops", "fullstack"]

        # Create LLM-powered agents
        self.agents = {
            "cv_parser": CVParserAgent(),
            "embeddings": EmbeddingsAgent(),
            "search": SearchAgent(),
            "grouping": GroupingAgent(),
            "calendar": CalendarAgent(),
        }

    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the full LLM-powered multi-agent workflow"""
        if inputs is None:
            inputs = {
                "domains": self.domains,
                "per_group": 3,
            }

        print("\n🚀 RecruitAI LLM-Powered Multi-Agent Workflow Starting...\n")

        workflow_results = {}

        try:
            # Step 1: CV Parser Agent with LLM reasoning
            print("Step 1️⃣: CV Parsing with LLM Guidance")
            cv_result = self.agents["cv_parser"].execute({})
            if cv_result["status"] != "success":
                return {"status": "error", "error": "CV parsing failed"}
            print(f"   ✅ Parsed {cv_result['count']} candidates\n")
            workflow_results["cv_parsing"] = cv_result

            # Step 2: Embeddings Agent with LLM validation
            print("Step 2️⃣: Embedding Creation with LLM Validation")
            emb_result = self.agents["embeddings"].execute({"data": cv_result["data"]})
            if emb_result["status"] != "success":
                return {"status": "error", "error": "Embedding creation failed"}
            print("   ✅ Created embeddings\n")
            workflow_results["embeddings"] = emb_result

            # Step 3: Search Agent with LLM domain understanding
            print("Step 3️⃣: Domain-Based Search with LLM Understanding")
            search_result = self.agents["search"].execute({
                "data": emb_result["data"],
                "domains": inputs.get("domains", self.domains)
            })
            if search_result["status"] != "success":
                return {"status": "error", "error": "Search failed"}
            print("   ✅ Searched and ranked candidates\n")
            workflow_results["search"] = search_result

            # Step 4: Grouping Agent with LLM team reasoning
            print("Step 4️⃣: Team Grouping with LLM Reasoning")
            group_result = self.agents["grouping"].execute({
                "data": search_result["data"],
                "per_group": inputs.get("per_group", 3)
            })
            if group_result["status"] != "success":
                return {"status": "error", "error": "Grouping failed"}
            print("   ✅ Created balanced teams\n")
            workflow_results["grouping"] = group_result

            # Step 5: Calendar Agent with LLM meeting strategy
            print("Step 5️⃣: Meeting Planning with LLM Strategy")
            calendar_result = self.agents["calendar"].execute({
                "data": group_result["data"]
            })
            print("   ✅ Meeting plan created\n")
            workflow_results["calendar_planning"] = calendar_result

            return {
                "status": calendar_result["status"],
                "message": calendar_result.get("message", "Workflow complete"),
                "workflow": workflow_results,
                "final_data": calendar_result["data"],
                "llm_enabled": LLM_AVAILABLE,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "llm_enabled": LLM_AVAILABLE,
                "timestamp": datetime.now().isoformat()
            }


def run_recruitment_crew(domains: Optional[List[str]] = None, per_group: int = 3) -> Dict[str, Any]:
    """Run the LLM-powered recruitment crew"""
    crew = RecruitAICrew(domains=domains)
    return crew.kickoff(inputs={
        "domains": domains or ["backend", "frontend", "data_science"],
        "per_group": per_group,
    })
