from meeting_qa import ask_meeting_history

MEETING_ID = "0eb179c9-bfc1-4010-af4f-5a0aa77a915f"

answer_tests = [
    {
        "id": "answer-01",
        "question": "When will Rahul share the regression testing results?",
        "expected_terms": ["Rahul", "Friday morning"],
        "must_not_contain": [],
    },
    {
        "id": "answer-02",
        "question": "Who will be on call during the deployment?",
        "expected_terms": ["unresolved"],
        "must_not_contain": [
            "Ananya is on call",
            "Rahul is on call",
            "Priya is on call",
            "Karthik is on call",
        ],
    },
    {
        "id": "answer-03",
        "question": "What post-deployment monitoring duration was decided?",
        "expected_terms": ["does not specify", "open question"],
        "must_not_contain": [
            "30 minutes was decided",
            "one hour was decided",
        ],
    },
]


def evaluate_answer(test):
    answer = ask_meeting_history(
        test["question"],
        meeting_id=MEETING_ID,
    )

    normalized_answer = answer.casefold()

    found = [
        term for term in test["expected_terms"] if term.casefold() in normalized_answer
    ]

    missing = [
        term
        for term in test["expected_terms"]
        if term.casefold() not in normalized_answer
    ]

    forbidden = [
        term
        for term in test["must_not_contain"]
        if term.casefold() in normalized_answer
    ]

    passed = not missing and not forbidden

    return {
        "id": test["id"],
        "question": test["question"],
        "answer": answer,
        "passed": passed,
        "missing": missing,
        "forbidden": forbidden,
    }


def main():
    results = []

    for test in answer_tests:
        print(f"\nRunning {test['id']}...")
        results.append(evaluate_answer(test))

    print("\n" + "=" * 60)
    print("MEETBRAIN AI — ANSWER QUALITY EVALUATION")
    print("=" * 60)

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        print(f"\n[{status}] {result['id']}: {result['question']}")
        print(f"Answer: {result['answer']}")

        if result["missing"]:
            print(f"Missing expected terms: {result['missing']}")

        if result["forbidden"]:
            print(f"Potentially unsupported claims: {result['forbidden']}")

    passed_count = sum(result["passed"] for result in results)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"Result: {passed_count}/{total} tests passed")
    print(f"Pass rate: {passed_count / total:.0%}" if total else "No tests")

    if passed_count != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
