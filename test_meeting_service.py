import pytest
from pydantic import ValidationError

import meeting_service
from schemas import MeetingReport

VALID_REPORT = {
    "title": "E-Commerce Checkout Release Planning",
    "summary": "Ananya will complete integration testing by Wednesday.",
    "key_decisions": ["Release only after required testing is complete."],
    "action_items": [
        {
            "task": "Complete integration testing",
            "owner": "Ananya",
            "deadline": "Wednesday",
        }
    ],
    "open_questions": ["Which monitoring dashboard will be selected?"],
    "follow_up_email": "Hi team, testing is due Wednesday.",
}


def test_valid_report_is_generated(monkeypatch):
    monkeypatch.setattr(
        meeting_service,
        "get_completion",
        lambda prompt: __import__("json").dumps(VALID_REPORT),
    )

    report = meeting_service.generate_meeting_report(
        "Ananya will complete integration testing by Wednesday."
    )

    assert isinstance(report, MeetingReport)
    assert report.title == "E-Commerce Checkout Release Planning"
    assert report.action_items[0].owner == "Ananya"
    assert report.action_items[0].deadline == "Wednesday"


def test_invalid_json_is_rejected(monkeypatch):
    monkeypatch.setattr(
        meeting_service,
        "get_completion",
        lambda prompt: "not valid JSON",
    )

    with pytest.raises(ValueError):
        meeting_service.generate_meeting_report("Sample transcript")


def test_missing_title_is_rejected(monkeypatch):
    import json

    invalid_report = {**VALID_REPORT, "title": None}

    monkeypatch.setattr(
        meeting_service,
        "get_completion",
        lambda prompt: json.dumps(invalid_report),
    )

    with pytest.raises(ValidationError):
        meeting_service.generate_meeting_report("Sample transcript")


def test_empty_title_is_rejected(monkeypatch):
    import json

    invalid_report = {**VALID_REPORT, "title": ""}

    monkeypatch.setattr(
        meeting_service,
        "get_completion",
        lambda prompt: json.dumps(invalid_report),
    )

    with pytest.raises(ValidationError):
        meeting_service.generate_meeting_report("Sample transcript")
