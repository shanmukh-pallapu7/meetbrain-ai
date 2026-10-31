import meeting_graph
from schemas import MeetingReport

VALID_REPORT = {
    "title": "Checkout Release Planning",
    "summary": "Testing must finish before release.",
    "key_decisions": ["Release waits until testing is complete."],
    "action_items": [
        {
            "task": "Complete integration testing",
            "owner": "Ananya",
            "deadline": "Wednesday",
        }
    ],
    "open_questions": ["Which monitoring dashboard will be selected?"],
    "follow_up_email": "Hi team, please complete testing by Wednesday.",
}


def test_graph_success(monkeypatch):
    monkeypatch.setattr(
        meeting_graph,
        "generate_meeting_report",
        lambda transcript: MeetingReport.model_validate(VALID_REPORT),
    )

    result = meeting_graph.run_meeting_graph("Test transcript")

    assert result["error"] is None
    assert result["report"]["title"] == "Checkout Release Planning"


def test_graph_handles_generation_failure(monkeypatch):
    def fail_generation(transcript):
        raise RuntimeError("Simulated generation failure")

    monkeypatch.setattr(
        meeting_graph,
        "generate_meeting_report",
        fail_generation,
    )

    result = meeting_graph.run_meeting_graph("Test transcript")

    assert result["error"] is not None
    assert result["report"] is None


def test_graph_rejects_invalid_report(monkeypatch):
    invalid_report = {
        **VALID_REPORT,
        "title": None,
    }

    monkeypatch.setattr(
        meeting_graph,
        "generate_meeting_report",
        lambda transcript: invalid_report,
    )

    result = meeting_graph.run_meeting_graph("Test transcript")

    assert result["error"] is not None
