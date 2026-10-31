from meeting_store import (
    chunk_collection,
    embedding_model,
    save_meeting_chunks,
)

meeting_id = "chunk_test_001"

report = {
    "title": "Demo Meeting",
    "summary": "The team reviewed the release.",
    "key_decisions": ["Deploy only after tests pass."],
    "action_items": [
        {
            "task": "Run regression tests",
            "owner": "Ananya",
            "deadline": "Wednesday",
        }
    ],
    "open_questions": ["Who will be on call?"],
}

saved = save_meeting_chunks(
    chunk_collection,
    embedding_model,
    meeting_id,
    report,
)

print("Chunks saved:", saved)
print("Collection count:", chunk_collection.count())
