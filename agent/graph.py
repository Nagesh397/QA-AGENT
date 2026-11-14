import os
from typing import List, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from .excel_writer import write_excel
from .jira_source import LocalJiraSource
from .models import TestSuite

MAX_RETRIES = 2

# Use a Gemini model that is generally available to standard developers.
# Override this via GEMINI_MODEL in the environment or .env file if needed.
DEFAULT_MODEL = "gemini-2.5-flash"


class AgentState(TypedDict):
    story_file: str
    output_path: str
    story: dict
    test_cases: List[dict]
    missing_acs: List[str]
    retries: int


def _llm():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to .env or your environment before running the app."
        )

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL") or DEFAULT_MODEL,
        google_api_key=api_key,
        temperature=0.2,
        request_timeout=30,
        max_retries=1,
    ).with_structured_output(TestSuite)


SYSTEM_PROMPT = """You are a senior QA engineer. Write thorough, manual-executable test cases
from Jira acceptance criteria.

Rules:
- Every test case must link to exactly one acceptance criterion ID (e.g. AC1).
- Every acceptance criterion must get at least one Positive and, where applicable,
  Negative / Boundary / Edge cases.
- Steps must be atomic and ordered. Use concrete test data (real-looking values, not 'valid input').
- Expected results must be specific and verifiable.
- Do not invent features that are not implied by the story or criteria.
- Avoid duplicate test cases."""


# ---------- nodes ----------
def read_criteria(state: AgentState) -> dict:
    story = LocalJiraSource().get_story(state["story_file"])
    print(f"Read {story['story_id']} with {len(story['acceptance_criteria'])} acceptance criteria")
    return {"story": story, "test_cases": [], "missing_acs": [], "retries": 0}


def generate_tests(state: AgentState) -> dict:
    story = state["story"]
    target_ids = state["missing_acs"] or [a["id"] for a in story["acceptance_criteria"]]
    targets = [a for a in story["acceptance_criteria"] if a["id"] in target_ids]

    criteria_text = "\n".join(f"{a['id']}: {a['text']}" for a in targets)
    user_msg = (
        f"Story: {story['story_id']} - {story['title']}\n"
        f"Description: {story['description']}\n\n"
        f"Generate test cases for these acceptance criteria:\n{criteria_text}"
    )

    try:
        suite: TestSuite = _llm().invoke(
            [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)]
        )
    except Exception as exc:
        raise RuntimeError(
            "Gemini request failed. Check that GEMINI_API_KEY is valid, the selected model is available, "
            "and the network can reach Google AI."
        ) from exc
    new_cases = [tc.model_dump() for tc in suite.test_cases]
    print(f"Generated {len(new_cases)} test cases for {', '.join(target_ids)}")
    return {"test_cases": state["test_cases"] + new_cases}


def review_coverage(state: AgentState) -> dict:
    covered = {tc["linked_ac"] for tc in state["test_cases"]}
    missing = [a["id"] for a in state["story"]["acceptance_criteria"] if a["id"] not in covered]
    if missing:
        print(f"Coverage gap: {missing}")
    return {"missing_acs": missing, "retries": state["retries"] + 1}


def route_after_review(state: AgentState) -> str:
    if state["missing_acs"] and state["retries"] <= MAX_RETRIES:
        return "generate_tests"
    return "write_excel"


def write_excel_node(state: AgentState) -> dict:
    path = write_excel(state["story"], state["test_cases"], state["output_path"])
    print(f"Saved {len(state['test_cases'])} test cases to {path}")
    return {}


# ---------- graph ----------
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("read_criteria", read_criteria)
    g.add_node("generate_tests", generate_tests)
    g.add_node("review_coverage", review_coverage)
    g.add_node("write_excel", write_excel_node)

    g.add_edge(START, "read_criteria")
    g.add_edge("read_criteria", "generate_tests")
    g.add_edge("generate_tests", "review_coverage")
    g.add_conditional_edges(
        "review_coverage",
        route_after_review,
        {"generate_tests": "generate_tests", "write_excel": "write_excel"},
    )
    g.add_edge("write_excel", END)
    return g.compile()
