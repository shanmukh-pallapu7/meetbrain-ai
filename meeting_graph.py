from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from meeting_service import generate_meeting_report

from schemas import MeetingReport


class MeetingState(TypedDict):
    transcript: str
    report: dict | None
    error: str | None


def generate_report_node(state: MeetingState) -> dict:
    """Generate a meeting report using the existing LLM service."""
    try:
        report = generate_meeting_report(state["transcript"])

        return {
            "report": report.model_dump(),
            "error": None,
        }

    except Exception as exc:
        return {
            "report": None,
            "error": str(exc),
        }


def validate_report_node(state: MeetingState) -> dict:
    try:
        report = MeetingReport.model_validate(state["report"])
        return {"report": report.model_dump(), "error": None}
    except Exception as exc:
        return {"report": None, "error": str(exc)}


def route_after_generation(state: MeetingState) -> str:
    if state.get("error") or not state.get("report"):
        return "end"
    return "validate"


builder = StateGraph(MeetingState)

builder.add_node("generate", generate_report_node)
builder.add_node("validate", validate_report_node)

builder.add_edge(START, "generate")

builder.add_conditional_edges(
    "generate",
    route_after_generation,
    {
        "validate": "validate",
        "end": END,
    },
)

builder.add_edge("validate", END)

meeting_graph = builder.compile()


def run_meeting_graph(transcript: str) -> dict:
    initial_state: MeetingState = {
        "transcript": transcript,
        "report": None,
        "error": None,
    }

    return meeting_graph.invoke(initial_state)
