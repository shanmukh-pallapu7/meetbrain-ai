import logging

import logging_config
from llm_service import get_completion
from schemas import MeetingReport

logger = logging.getLogger(__name__)


def generate_meeting_report(transcript: str) -> MeetingReport:
    """Generate and validate a structured meeting report using Groq."""

    if not transcript or not transcript.strip():
        raise ValueError("Meeting transcript cannot be empty")

    logger.info("Meeting report generation started")

    prompt = f"""
You are an expert meeting intelligence assistant.

Analyze the meeting transcript and generate a structured report.

Requirements:
1. Give the meeting a short, meaningful title.
2. Summarize the main discussion points.
3. Identify important decisions explicitly mentioned.
4. Extract action items with task, owner, and deadline.
5. Identify unresolved questions.
6. Draft a professional follow-up email.

Rules:
- Use only information present in the transcript.
- Do not invent names, deadlines, decisions, or responsibilities.
- Use null for unknown action item owners or deadlines.
- If no decisions, action items, or open questions exist,
  return empty arrays.
- Return valid JSON only.
- Do not include Markdown code fences or additional explanations.

Required JSON structure:
{{
    "title": "Meeting title",
    "summary": "Meeting summary",
    "key_decisions": [],
    "action_items": [
        {{
            "task": "Action item",
            "owner": null,
            "deadline": null
        }}
    ],
    "open_questions": [],
    "follow_up_email": "Email content"
}}

Meeting transcript:
{transcript}
"""

    try:
        response = get_completion(prompt)

        if not response:
            raise ValueError("The LLM returned an empty response")

        report = MeetingReport.model_validate_json(response)

        logger.info("Meeting report generated and validated successfully")

        return report

    except Exception:
        logger.exception("Meeting report generation failed")
        raise
