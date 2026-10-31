from meeting_service import generate_meeting_report

transcript = """
Meeting: API Release Planning

Priya will finish integration testing by Thursday.
Rahul will deploy the API on Friday if testing passes.
The team decided not to release until testing is complete.
We still need to confirm whether load testing has passed.
"""

report = generate_meeting_report(transcript)

print(report.model_dump_json(indent=2))
