import meeting_qa


def test_answer_uses_selected_meeting(monkeypatch):
    def fake_search(
        target_collection,
        model,
        query,
        top_k=3,
        meeting_id=None,
        max_distance=None,
    ):
        assert meeting_id == "checkout_meeting"
        assert max_distance == meeting_qa.DEFAULT_MAX_DISTANCE

        return [
            {
                "title": "E-Commerce Checkout Release Planning",
                "distance": 0.2,
                "section": "action_items",
                "text": (
                    "Title: E-Commerce Checkout Release Planning\n"
                    "Action items:\n"
                    "- Task: Complete integration testing; "
                    "Owner: Ananya; Deadline: Wednesday"
                ),
            }
        ]

    def fake_completion(prompt):
        assert "Owner: Ananya" in prompt
        assert "Deadline: Wednesday" in prompt
        return "Ananya is responsible, and it is due Wednesday."

    monkeypatch.setattr(meeting_qa, "search_meeting_chunks", fake_search)
    monkeypatch.setattr(meeting_qa, "get_completion", fake_completion)

    answer = meeting_qa.ask_meeting_history(
        "Who owns integration testing, and when is it due?",
        meeting_id="checkout_meeting",
    )

    assert "Ananya" in answer
    assert "Wednesday" in answer


def test_returns_fallback_when_no_results(monkeypatch):
    def fake_search(
        target_collection,
        model,
        query,
        top_k=3,
        meeting_id=None,
        max_distance=None,
    ):
        return []

    def fake_completion(prompt):
        raise AssertionError("LLM should not be called when retrieval is empty")

    monkeypatch.setattr(meeting_qa, "search_meeting_chunks", fake_search)
    monkeypatch.setattr(meeting_qa, "get_completion", fake_completion)

    answer = meeting_qa.ask_meeting_history(
        "What happened in the meeting?",
        meeting_id="meeting-1",
    )

    assert "couldn't find sufficiently relevant information" in answer


def test_retrieval_is_scoped_to_selected_meeting(monkeypatch):
    requested_meeting = "checkout_meeting"

    def fake_search(
        target_collection,
        model,
        query,
        top_k=3,
        meeting_id=None,
        max_distance=None,
    ):
        assert meeting_id == requested_meeting

        return [
            {
                "title": "E-Commerce Checkout Release Planning",
                "distance": 0.2,
                "section": "action_items",
                "text": "Owner: Ananya; Deadline: Wednesday",
            }
        ]

    def fake_completion(prompt):
        assert "Monday" not in prompt
        return "Ananya is responsible, and the deadline is Wednesday."

    monkeypatch.setattr(meeting_qa, "search_meeting_chunks", fake_search)
    monkeypatch.setattr(meeting_qa, "get_completion", fake_completion)

    answer = meeting_qa.ask_meeting_history(
        "When is integration testing due?",
        meeting_id=requested_meeting,
    )

    assert "Wednesday" in answer


def test_unresolved_on_call_question_uses_meeting_context(monkeypatch):
    meeting_context = (
        "Meeting: E-commerce Checkout Release Planning\n"
        "Section: open_questions\n"
        "What is the monitoring duration (30 minutes or one hour)?; "
        "Who will be on call during deployment?"
    )

    def fake_search(
        target_collection,
        model,
        query,
        top_k=3,
        meeting_id=None,
        max_distance=None,
    ):
        assert meeting_id == "meeting-1"

        return [
            {
                "text": meeting_context,
                "title": "E-commerce Checkout Release Planning",
                "section": "open_questions",
                "distance": 0.2,
            }
        ]

    def fake_completion(prompt):
        assert "Who will be on call during deployment?" in prompt

        return (
            "The team did not confirm who will be on call "
            "during deployment. It remains an open question."
        )

    monkeypatch.setattr(meeting_qa, "search_meeting_chunks", fake_search)
    monkeypatch.setattr(meeting_qa, "get_completion", fake_completion)

    answer = meeting_qa.ask_meeting_history(
        "Did the team confirm who will be on call during deployment?",
        meeting_id="meeting-1",
    )

    assert "open question" in answer
