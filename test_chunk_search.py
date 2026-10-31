from meeting_store import (
    chunk_collection,
    embedding_model,
    search_meeting_chunks,
)

meeting_id = "chunk_test_001"

queries = [
    "Who owns regression testing and when is it due?",
    "What decision did the team make?",
    "Who will be on call?",
]

for query in queries:
    print(f"\nQuestion: {query}")

    results = search_meeting_chunks(
        chunk_collection,
        embedding_model,
        query,
        top_k=2,
        meeting_id=meeting_id,
    )

    for result in results:
        print(f"Section: {result['section']}")
        print(f"Text: {result['text']}")
