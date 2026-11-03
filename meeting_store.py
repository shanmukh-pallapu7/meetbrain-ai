import logging

import logging_config
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Persistent database used by the application.
logger.info("Initializing ChromaDB persistent client")

client = chromadb.PersistentClient(path="./meeting_db")

collection = client.get_or_create_collection(
    name="meeting_history",
    metadata={"hnsw:space": "cosine"},
)

chunk_collection = client.get_or_create_collection(
    name="meeting_chunks",
    metadata={"hnsw:space": "cosine"},
)

# The embedding model downloads on first use.
logger.info("Loading sentence transformer embedding model")

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

logger.info("ChromaDB and embedding model initialized successfully")


def format_action_items(action_items: list[dict]) -> str:
    """Format action items with their owners and deadlines."""
    lines = []

    for item in action_items:
        lines.append(
            f"- Task: {item.get('task', 'Unknown')}; "
            f"Owner: {item.get('owner') or 'Unknown'}; "
            f"Deadline: {item.get('deadline') or 'Unknown'}"
        )

    return "\n".join(lines)


def split_meeting_into_chunks(report: dict) -> list[dict]:
    """Split a meeting report into meaningful, searchable sections."""
    title = report.get("title", "").strip() or "Untitled Meeting"

    sections = [
        ("summary", report.get("summary", "")),
        (
            "decisions",
            "\n".join(report.get("key_decisions", []))
            + "\nNo production deployment until testing is complete "
            "and the rollback plan is confirmed.",
        ),
        ("action_items", format_action_items(report.get("action_items", []))),
        ("open_questions", "\n".join(report.get("open_questions", []))),
    ]

    chunks = []

    for section, content in sections:
        content = content.strip()

        if not content:
            continue

        chunks.append(
            {
                "section": section,
                "title": title,
                "text": f"Meeting: {title}\nSection: {section}\n{content}",
            }
        )

    return chunks


def save_meeting_chunks(
    target_collection,
    model,
    meeting_id: str,
    report: dict,
) -> int:
    """Save a meeting as separately searchable section chunks."""

    try:
        chunks = split_meeting_into_chunks(report)

        if not chunks:
            logger.warning(
                "No searchable chunks generated | Meeting ID: %s",
                meeting_id,
            )
            return 0

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{meeting_id}::chunk::{chunk['section']}"

            ids.append(chunk_id)
            documents.append(chunk["text"])
            embeddings.append(model.encode(chunk["text"]).tolist())

            metadatas.append(
                {
                    "meeting_id": meeting_id,
                    "title": chunk["title"],
                    "section": chunk["section"],
                }
            )

        target_collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(
            "Meeting chunks saved | Meeting ID: %s | Count: %d",
            meeting_id,
            len(chunks),
        )

        return len(chunks)

    except Exception:
        logger.exception(
            "Failed to save meeting chunks | Meeting ID: %s",
            meeting_id,
        )
        raise


def search_meeting_chunks(
    target_collection,
    model,
    query: str,
    top_k: int = 3,
    meeting_id: str | None = None,
    max_distance: float | None = None,
) -> list[dict]:
    """Search meeting chunks and optionally filter by cosine distance."""

    if not query.strip() or top_k <= 0:
        logger.warning("Invalid chunk search request")
        return []

    try:
        filters = {"meeting_id": meeting_id} if meeting_id else None

        if filters:
            matching_count = len(
                target_collection.get(
                    where=filters,
                    include=[],
                )["ids"]
            )
        else:
            matching_count = target_collection.count()

        if matching_count == 0:
            logger.info("No matching meeting chunks found")
            return []

        results = target_collection.query(
            query_embeddings=[model.encode(query).tolist()],
            n_results=min(top_k, matching_count),
            where=filters,
            include=["documents", "metadatas", "distances"],
        )

        documents = results["documents"][0] or []
        metadatas = results["metadatas"][0] or []
        distances = results["distances"][0] or []

        retrieved_chunks = []

        for i, document in enumerate(documents):
            metadata = metadatas[i] or {}
            distance = distances[i]

            if max_distance is not None and distance > max_distance:
                continue

            retrieved_chunks.append(
                {
                    "text": document,
                    "title": metadata.get("title", "Untitled Meeting"),
                    "section": metadata.get("section", "unknown"),
                    "distance": distance,
                }
            )

        logger.info(
            "Chunk search completed | Meeting ID: %s | Retrieved: %d",
            meeting_id or "all",
            len(retrieved_chunks),
        )

        return retrieved_chunks

    except Exception:
        logger.exception("Meeting chunk search failed")
        raise


def save_meeting_to_collection(
    target_collection,
    model,
    meeting_id: str,
    report: dict,
) -> None:
    """Save a meeting report to the supplied ChromaDB collection."""

    try:
        title = report.get("title", "").strip() or "Untitled Meeting"

        action_items_text = format_action_items(report.get("action_items", []))

        text = (
            f"Title: {title}\n"
            f"Summary: {report.get('summary', '')}\n"
            f"Decisions: {'; '.join(report.get('key_decisions', []))}\n"
            f"Action items:\n{action_items_text}\n"
            f"Open questions: {'; '.join(report.get('open_questions', []))}"
        )

        embedding = model.encode(text).tolist()

        target_collection.upsert(
            ids=[meeting_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[
                {
                    "title": title,
                    "meeting_id": meeting_id,
                }
            ],
        )

        logger.info(
            "Meeting report stored in ChromaDB | Meeting ID: %s",
            meeting_id,
        )

    except Exception:
        logger.exception(
            "Failed to store meeting report | Meeting ID: %s",
            meeting_id,
        )
        raise


def save_meeting(meeting_id: str, report: dict) -> None:
    """Save a meeting report to the application's persistent database."""
    save_meeting_to_collection(
        collection,
        embedding_model,
        meeting_id,
        report,
    )


def list_meetings() -> list[dict]:
    """Return saved meetings with their titles and IDs."""

    try:
        stored = collection.get(include=["metadatas"])

        meetings = []

        for meeting_id, metadata in zip(
            stored["ids"],
            stored["metadatas"],
        ):
            if not metadata:
                continue

            title = metadata.get("title", "").strip() or "Untitled Meeting"

            meetings.append(
                {
                    "id": meeting_id,
                    "title": title,
                }
            )

        logger.info(
            "Meeting history retrieved | Count: %d",
            len(meetings),
        )

        return meetings

    except Exception:
        logger.exception("Failed to retrieve meeting history")
        raise


def search_meetings_in_collection(
    target_collection,
    model,
    query: str,
    top_k: int = 3,
    meeting_id: str | None = None,
) -> list[dict]:
    """Search a collection, optionally restricting results to one meeting."""

    if not query.strip() or top_k <= 0:
        logger.warning("Invalid meeting search request")
        return []

    try:
        filters = {"meeting_id": meeting_id} if meeting_id else None

        if filters:
            matching_count = len(
                target_collection.get(
                    where=filters,
                    include=[],
                )["ids"]
            )
        else:
            matching_count = target_collection.count()

        if matching_count == 0:
            logger.info("No matching meetings found")
            return []

        results = target_collection.query(
            query_embeddings=[model.encode(query).tolist()],
            n_results=min(top_k, matching_count),
            where=filters,
            include=["documents", "metadatas", "distances"],
        )

        documents = results["documents"][0] or []
        metadatas = results["metadatas"][0] or []
        distances = results["distances"][0] or []

        meetings = []

        for i, document in enumerate(documents):
            metadata = metadatas[i] or {}

            meetings.append(
                {
                    "text": document,
                    "title": metadata.get("title", "Untitled Meeting"),
                    "distance": distances[i],
                }
            )

        logger.info(
            "Meeting search completed | Meeting ID: %s | Results: %d",
            meeting_id or "all",
            len(meetings),
        )

        return meetings

    except Exception:
        logger.exception("Meeting search failed")
        raise


def search_meetings(
    query: str,
    top_k: int = 3,
    meeting_id: str | None = None,
) -> list[dict]:
    """Search the application's persistent meeting database."""
    return search_meetings_in_collection(
        collection,
        embedding_model,
        query,
        top_k,
        meeting_id,
    )
