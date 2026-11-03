import logging
from typing import TypedDict

import logging_config
from langgraph.graph import StateGraph, START, END
from schemas import MeetingReport
from meeting_service import generate_meeting_report

logger = logging.getLogger(__name__)


class MeetingState(TypedDict):
    transcript: str
    report: dict | None
    error: str | None


def generate_report_node(state: MeetingState) -> dict:
    try:
        logger.info("Starting report generation node")

        report = generate_meeting_report(state["transcript"])

        logger.info("Report generation node completed successfully")

        return {
            "report": report.model_dump(),
            "error": None,
        }

    except Exception:
        logger.exception("Report generation node failed")

        return {
            "report": None,
            "error": "Could not generate the meeting report. Please try again.",
        }


def validate_report_node(state: MeetingState) -> dict:
    try:
        logger.info("Starting report validation node")

        report = MeetingReport.model_validate(state["report"])

        logger.info("Report validation completed successfully")

        return {
            "report": report.model_dump(),
            "error": None,
        }

    except Exception:
        logger.exception("Report validation node failed")

        return {
            "report": None,
            "error": "The generated report failed validation. Please try again.",
        }


def route_after_generation(state: MeetingState) -> str:
    if state.get("error") or not state.get("report"):
        logger.warning("Report generation unsuccessful. Ending workflow.")
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
    if not transcript or not transcript.strip():
        logger.warning("Empty transcript received by meeting workflow")

        return {
            "transcript": transcript,
            "report": None,
            "error": "Please provide a non-empty meeting transcript.",
        }

    initial_state: MeetingState = {
        "transcript": transcript,
        "report": None,
        "error": None,
    }

    try:
        logger.info("Meeting graph execution started")

        result = meeting_graph.invoke(initial_state)

        logger.info("Meeting graph execution completed")

        return result

    except Exception:
        logger.exception("Unexpected meeting graph execution failure")
        raise
