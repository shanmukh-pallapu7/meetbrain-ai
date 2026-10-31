import chromadb
import pytest

from meeting_store import (
    save_meeting_to_collection,
    search_meetings_in_collection,
    embedding_model,
)


@pytest.fixture
def test_collection():
    """Create an isolated, temporary ChromaDB collection."""
    client = chromadb.EphemeralClient()

    collection = client.create_collection(
        name="test_meeting_history",
        metadata={"hnsw:space": "cosine"},
    )

    yield collection

    client.delete_collection("test_meeting_history")


def test_save_preserves_action_item_details(test_collection):
    report = {
        "title": "Checkout Release Planning",
        "summary": "The team planned the checkout release.",
        "key_decisions": ["Proceed with integration testing"],
        "action_items": [
            {
                "task": "Complete payment API testing",
                "owner": "Ananya",
                "deadline": "Wednesday",
            }
        ],
        "open_questions": ["What is the rollback window?"],
        "follow_up_email": "Hi team, here are the meeting updates.",
    }

    save_meeting_to_collection(
        test_collection,
        embedding_model,
        "meeting-1",
        report,
    )

    stored = test_collection.get(
        ids=["meeting-1"],
        include=["documents", "metadatas"],
    )

    document = stored["documents"][0]
    metadata = stored["metadatas"][0]

    assert metadata["title"] == "Checkout Release Planning"
    assert metadata["meeting_id"] == "meeting-1"
    assert "Complete payment API testing" in document
    assert "Ananya" in document
    assert "Wednesday" in document
    assert "Proceed with integration testing" in document
    assert "What is the rollback window?" in document


def test_search_is_scoped_to_selected_meeting(test_collection):
    checkout_report = {
        "title": "Checkout Release",
        "summary": "Payment integration testing is assigned to Ananya.",
        "key_decisions": [],
        "action_items": [
            {
                "task": "Complete payment API testing",
                "owner": "Ananya",
                "deadline": "Wednesday",
            }
        ],
        "open_questions": [],
    }

    monitoring_report = {
        "title": "Monitoring Review",
        "summary": "The team reviewed infrastructure monitoring.",
        "key_decisions": ["Use the Grafana dashboard"],
        "action_items": [],
        "open_questions": [],
    }

    save_meeting_to_collection(
        test_collection,
        embedding_model,
        "meeting-1",
        checkout_report,
    )

    save_meeting_to_collection(
        test_collection,
        embedding_model,
        "meeting-2",
        monitoring_report,
    )

    results = search_meetings_in_collection(
        test_collection,
        embedding_model,
        "Who owns payment API testing and when is it due?",
        meeting_id="meeting-1",
    )

    assert results
    assert all(item["title"] == "Checkout Release" for item in results)
    assert all("Ananya" in item["text"] for item in results)
    assert all("Wednesday" in item["text"] for item in results)
    assert all("Grafana" not in item["text"] for item in results)


def test_unknown_meeting_id_returns_no_results(test_collection):
    report = {
        "title": "Existing Meeting",
        "summary": "Payment testing was discussed.",
        "key_decisions": [],
        "action_items": [],
        "open_questions": [],
    }

    save_meeting_to_collection(
        test_collection,
        embedding_model,
        "existing-meeting",
        report,
    )

    results = search_meetings_in_collection(
        test_collection,
        embedding_model,
        "payment testing",
        meeting_id="does-not-exist",
    )

    assert results == []


def test_blank_query_returns_no_results(test_collection):
    results = search_meetings_in_collection(
        test_collection,
        embedding_model,
        "   ",
    )

    assert results == []
