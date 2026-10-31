from llm_service import get_completion
from schemas import MeetingReport


def generate_meeting_report(transcript: str) -> MeetingReport:
    prompt = f"""
You are MeetBrain AI, a meeting intelligence assistant.

Analyze the transcript below and return ONLY a valid JSON object
matching this structure:

{{
  "title": "Meeting title",
  "summary": "Concise summary",
  "key_decisions": [],
  "action_items": [
    {{
      "task": "Action to perform",
      "owner": null,
      "deadline": null
    }}
  ],
  "open_questions": [],
  "follow_up_email": "Draft email"
}}

Rules:
- Never invent facts, owners, or deadlines.
- Use null for unknown owners and deadlines.
- Include only decisions supported by the transcript.
- Identify unresolved decisions, pending choices, and missing information as open questions.
- If the transcript explicitly says a decision has not been made, add a question about that decision to open_questions.
- Do not list a resolved decision as an open question.
- Use double quotes for JSON strings.
- Do not assume that two related statements have a relationship unless the transcript explicitly establishes it.
- The follow-up email must contain only facts supported by the transcript.
- Preserve conditional statements exactly as stated.
- Do not assign responsibility to an unspecified person.
- The title must be a concise, meaningful title based on the transcript.
- The title must never be empty, null, or whitespace-only.

Transcript:
{transcript}
"""

    result = get_completion(prompt)
    print("LLM raw response:", result)

    return MeetingReport.model_validate_json(result)
