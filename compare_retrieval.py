from meeting_store import (
    collection,
    chunk_collection,
    embedding_model,
    search_meetings_in_collection,
    search_meeting_chunks,
)

MEETING_ID = "0eb179c9-bfc1-4010-af4f-5a0aa77a915f"

questions = [
    "Who owns integration testing and when is it due?",
    "When will Rahul share regression test results?",
    "Who will be on call during deployment?",
]

for question in questions:
    print("\n" + "=" * 65)
    print(f"QUESTION: {question}")

    whole_results = search_meetings_in_collection(
        collection,
        embedding_model,
        question,
        top_k=1,
        meeting_id=MEETING_ID,
    )

    chunk_results = search_meeting_chunks(
        chunk_collection,
        embedding_model,
        question,
        top_k=1,
        meeting_id=MEETING_ID,
    )

    print("\nWHOLE-MEETING RETRIEVAL")
    for result in whole_results:
        print(f"Title: {result['title']}")
        print(f"Distance: {result['distance']:.4f}")

    print("\nCHUNK RETRIEVAL")
    for result in chunk_results:
        print(f"Section: {result['section']}")
        print(f"Distance: {result['distance']:.4f}")
        print(result["text"])
