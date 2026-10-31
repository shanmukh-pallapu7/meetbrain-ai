MEETING_ID = "0eb179c9-bfc1-4010-af4f-5a0aa77a915f"

evaluation_cases = [
    {
        "id": "eval-01",
        "question": "Who owns integration testing?",
        "expected_context_terms": ["Ananya", "integration testing"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-02",
        "question": "When is integration testing due?",
        "expected_context_terms": ["Wednesday", "integration testing"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-03",
        "question": "When will Rahul share regression testing results?",
        "expected_context_terms": ["Rahul", "Friday morning", "regression testing"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-04",
        "question": "Has the on-call responsibility been assigned?",
        "expected_context_terms": ["on call", "open"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-05",
        "question": "What post-deployment monitoring duration was decided?",
        "expected_context_terms": ["monitoring duration", "one hour"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-06",
        "question": "Who is responsible for verifying production alerts?",
        "expected_context_terms": ["Priya", "production alerts"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-07",
        "question": "When should the deployment readiness checklist be sent?",
        "expected_context_terms": ["Priya", "Thursday evening", "checklist"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-08",
        "question": "What must happen before the final go/no-go decision?",
        "expected_context_terms": ["test results", "readiness checklist", "Karthik"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-09",
        "question": "Can production deployment proceed before testing is complete?",
        "expected_context_terms": ["testing is complete", "rollback plan"],
        "meeting_id": MEETING_ID,
    },
    {
        "id": "eval-10",
        "question": "Has the production rollback procedure been confirmed?",
        "expected_context_terms": ["rollback procedure", "platform team"],
        "meeting_id": MEETING_ID,
    },
]
