from meeting_store import (
    collection,
    chunk_collection,
    embedding_model,
    search_meeting_chunks,
)

meeting_id = "0eb179c9-bfc1-4010-af4f-5a0aa77a915f"

stored = collection.get(
    ids=[meeting_id],
    include=["documents", "metadatas"],
)

if not stored["ids"]:
    raise ValueError(f"Meeting not found: {meeting_id}")

document = stored["documents"][0]
metadata = stored["metadatas"][0] or {}
title = metadata.get("title", "Untitled Meeting")

# Extract the original sections without reconstructing action items.
sections = {
    "summary": [],
    "decisions": [],
    "action_items": [],
    "open_questions": [],
}
current_section = None

for line in document.splitlines():
    stripped = line.strip()

    if stripped.startswith("Summary:"):
        current_section = "summary"
        sections[current_section].append(stripped.removeprefix("Summary:").strip())
    elif stripped.startswith("Decisions:"):
        current_section = "decisions"
        sections[current_section].append(stripped.removeprefix("Decisions:").strip())
    elif stripped == "Action items:":
        current_section = "action_items"
    elif stripped.startswith("Open questions:"):
        current_section = "open_questions"
        sections[current_section].append(
            stripped.removeprefix("Open questions:").strip()
        )
    elif current_section and stripped:
        sections[current_section].append(stripped)

# Build section chunks while preserving the stored text.
ids = []
documents = []
embeddings = []
metadatas = []

for section, lines in sections.items():
    content = "\n".join(lines).strip()
    if not content:
        continue

    chunk_text = f"Meeting: {title}\nSection: {section}\n{content}"

    ids.append(f"{meeting_id}::chunk::{section}")
    documents.append(chunk_text)
    embeddings.append(embedding_model.encode(chunk_text).tolist())
    metadatas.append(
        {
            "meeting_id": meeting_id,
            "title": title,
            "section": section,
        }
    )

chunk_collection.upsert(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas,
)

print(f"Saved {len(ids)} chunks for {meeting_id}")

for question in [
    "Who owns integration testing and when is it due?",
    "When will Rahul share regression test results?",
    "Who will be on call during deployment?",
]:
    print(f"\nQuestion: {question}")

    results = search_meeting_chunks(
        chunk_collection,
        embedding_model,
        question,
        top_k=2,
        meeting_id=meeting_id,
    )

    for result in results:
        print(f"Section: {result['section']}")
        print(result["text"][:500])
