from schemas import MeetingReport, ActionItem

report = MeetingReport(
    title="API Release Meeting",
    summary="The team discussed the upcoming API release.",
    key_decisions=["Release the API after testing"],
    action_items=[ActionItem(task="Deploy the API", owner="Rahul", deadline="Friday")],
    open_questions=["Has load testing been completed?"],
    follow_up_email="Hi team, here are the meeting updates.",
)

print(report.model_dump_json(indent=2))
