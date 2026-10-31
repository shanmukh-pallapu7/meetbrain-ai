import unicodedata

from evaluation_set import evaluation_cases
from meeting_store import (
    chunk_collection,
    embedding_model,
    search_meeting_chunks,
)

TOP_K = 3
THRESHOLDS = [None, 0.70, 0.60, 0.50, 0.40]


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)

    for char in ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2015"]:
        text = text.replace(char, "-")

    return text.casefold()


def evaluate_case(case, max_distance=None):
    retrieved_results = search_meeting_chunks(
        chunk_collection,
        embedding_model,
        case["question"],
        top_k=TOP_K,
        meeting_id=case["meeting_id"],
        max_distance=max_distance,
    )

    retrieved_text = normalize_text(
        "\n".join(str(result.get("text", "")) for result in retrieved_results)
    )

    expected_terms = case["expected_context_terms"]

    found_terms = [
        term for term in expected_terms if normalize_text(term) in retrieved_text
    ]

    missing_terms = [
        term for term in expected_terms if normalize_text(term) not in retrieved_text
    ]

    score = len(found_terms) / len(expected_terms) if expected_terms else 1.0

    distances = [
        result["distance"]
        for result in retrieved_results
        if result.get("distance") is not None
    ]

    return {
        "id": case["id"],
        "question": case["question"],
        "score": score,
        "chunks": len(retrieved_results),
        "distances": distances,
        "missing": missing_terms,
    }


def main():
    print("\nSIMILARITY THRESHOLD EVALUATION")
    print("=" * 75)
    print(f"Top-K: {TOP_K}")
    print(f"Evaluation questions: {len(evaluation_cases)}")

    summary = []

    for threshold in THRESHOLDS:
        results = [evaluate_case(case, threshold) for case in evaluation_cases]

        total = len(results)

        coverage = sum(result["score"] for result in results) / total if total else 0.0

        zero_results = sum(1 for result in results if result["chunks"] == 0)

        average_chunks = (
            sum(result["chunks"] for result in results) / total if total else 0.0
        )

        all_distances = [
            distance for result in results for distance in result["distances"]
        ]

        average_distance = (
            sum(all_distances) / len(all_distances) if all_distances else None
        )

        threshold_label = "No threshold" if threshold is None else str(threshold)

        summary.append(
            {
                "threshold": threshold_label,
                "coverage": coverage,
                "zero_results": zero_results,
                "average_chunks": average_chunks,
                "average_distance": average_distance,
            }
        )

        print(f"\nTHRESHOLD: {threshold_label}")
        print("-" * 75)

        for result in results:
            print(
                f"{result['id']} | "
                f"Coverage: {result['score']:.0%} | "
                f"Chunks: {result['chunks']} | "
                f"Missing: {result['missing']}"
            )

        print(f"\nAverage coverage: {coverage:.0%}")
        print(f"Questions with zero results: {zero_results}")
        print(f"Average chunks retrieved: {average_chunks:.2f}")

        if average_distance is not None:
            print(f"Average cosine distance: {average_distance:.4f}")
        else:
            print("Average cosine distance: N/A")

    print("\nFINAL THRESHOLD COMPARISON")
    print("=" * 85)

    print(
        f"{'Threshold':<16}"
        f"{'Coverage':<14}"
        f"{'Zero results':<16}"
        f"{'Avg chunks':<14}"
        f"{'Avg distance':<15}"
    )

    for item in summary:
        distance = item["average_distance"]

        distance_text = f"{distance:.4f}" if distance is not None else "N/A"

        print(
            f"{item['threshold']:<16}"
            f"{item['coverage']:.0%}{'':<12}"
            f"{item['zero_results']:<16}"
            f"{item['average_chunks']:<14.2f}"
            f"{distance_text:<15}"
        )


if __name__ == "__main__":
    main()
