import logging
import logging_config
import uuid
import json

import streamlit as st
from groq import APIConnectionError, APIStatusError, RateLimitError
from pydantic import ValidationError

from meeting_graph import run_meeting_graph
from meeting_store import (
    save_meeting,
    save_meeting_chunks,
    list_meetings,
    chunk_collection,
    embedding_model,
)
from meeting_qa import ask_meeting_history
from transcript_loader import extract_transcript

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="MeetBrain AI",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 MeetBrain AI")
st.caption("Turn meeting transcripts into actionable intelligence.")
st.warning(
    "Portfolio demo: Do not upload confidential, personal, or sensitive "
    "meeting transcripts. Meeting data is stored in this app's database."
)

st.header("Generate Meeting Report")

input_method = st.radio(
    "Choose how to provide your transcript",
    ["Paste transcript", "Upload file"],
    horizontal=True,
)

transcript = ""

if input_method == "Paste transcript":
    transcript = st.text_area(
        "Meeting transcript",
        placeholder="Paste your meeting transcript here...",
        height=250,
        key="pasted_transcript",
    )

else:
    uploaded_file = st.file_uploader(
        "Upload a meeting transcript",
        type=["txt", "pdf", "docx"],
        help="Supported formats: TXT, PDF, and DOCX.",
    )

    if uploaded_file is not None:
        try:
            transcript = extract_transcript(
                uploaded_file.name,
                uploaded_file.getvalue(),
            )

            st.success(f"Transcript loaded: {uploaded_file.name}")

            logger.info("Transcript file loaded successfully")

            with st.expander("Preview transcript"):
                st.text(transcript)

        except ValueError as exc:
            logger.warning("Transcript file validation failed: %s", exc)
            st.error(str(exc))

        except Exception:
            logger.exception("Unexpected error while loading transcript")
            st.error(
                "Could not read the uploaded file. "
                "Please check the file and try again."
            )


if st.button("Generate Report", type="primary"):

    if not transcript.strip():
        st.warning("Please provide a non-empty meeting transcript.")

    else:
        with st.spinner("Analyzing your meeting..."):

            try:
                logger.info("Meeting report generation started")

                result = run_meeting_graph(transcript)

                if result["error"]:
                    logger.error(
                        "Meeting workflow failed: %s",
                        result["error"],
                    )
                    st.error("Meeting analysis failed. " "Please try again.")
                    st.stop()

                report_data = result["report"]

                meeting_id = str(uuid.uuid4())

                # Save complete meeting report
                save_meeting(meeting_id, report_data)

                logger.info("Meeting report saved successfully")

                # Save searchable chunks
                saved_chunks = save_meeting_chunks(
                    chunk_collection,
                    embedding_model,
                    meeting_id,
                    report_data,
                )

                logger.info(
                    "Meeting chunks saved successfully. Count: %s",
                    saved_chunks,
                )

                st.success(
                    f"Meeting report saved successfully! "
                    f"{saved_chunks} searchable chunks created."
                )

                st.subheader(report_data["title"])
                st.write(report_data["summary"])

                st.subheader("Key Decisions")

                if report_data["key_decisions"]:
                    for decision in report_data["key_decisions"]:
                        st.markdown(f"- {decision}")
                else:
                    st.info("No decisions identified.")

                st.subheader("Action Items")

                if report_data["action_items"]:
                    st.dataframe(
                        report_data["action_items"],
                        width="stretch",
                    )
                else:
                    st.info("No action items identified.")

                st.subheader("Open Questions")

                if report_data["open_questions"]:
                    for question_item in report_data["open_questions"]:
                        st.markdown(f"- {question_item}")
                else:
                    st.info("No open questions identified.")

                st.subheader("Follow-up Email")

                email = report_data.get("follow_up_email", "")

                if email and email.strip():
                    st.text_area(
                        "Draft email",
                        value=email,
                        height=250,
                    )
                else:
                    st.warning("The model did not generate a follow-up email.")

                st.download_button(
                    "Download Report as JSON",
                    data=json.dumps(report_data, indent=2),
                    file_name="meeting_report.json",
                    mime="application/json",
                )

                logger.info("Meeting report generation completed")

            except RateLimitError:
                logger.exception("Groq API rate limit reached")
                st.error("Groq rate limit reached. " "Please wait and try again.")

            except APIConnectionError:
                logger.exception("Could not connect to Groq API")
                st.error(
                    "Could not connect to Groq. "
                    "Check your internet connection and retry."
                )

            except APIStatusError as exc:
                logger.exception("Groq API returned an error")
                st.error(
                    f"Groq returned an API error "
                    f"(HTTP {exc.status_code}). Please retry later."
                )

            except ValidationError:
                logger.exception("Meeting report validation failed")
                st.error(
                    "The generated report did not match "
                    "the expected format. Please try again."
                )

            except Exception:
                logger.exception("Unexpected error during meeting report generation")
                st.error("Could not generate the meeting report. " "Please try again.")


st.divider()

st.header("Ask Your Meeting History")

try:
    meetings = list_meetings()

except Exception:
    logger.exception("Failed to retrieve meeting history")
    meetings = []
    st.error("Could not load meeting history. Please try again.")

if meetings:

    selected_meeting = st.selectbox(
        "Choose a meeting",
        meetings,
        format_func=lambda meeting: meeting["title"],
    )

    selected_meeting_id = selected_meeting["id"]

else:
    selected_meeting_id = None
    st.info("Generate and save a meeting report first.")

st.caption("Ask questions about meetings you have previously processed.")

question = st.text_input(
    "Your question",
    placeholder="What decisions were made about deployment?",
    key="meeting_history_question",
)

if st.button("Ask MeetBrain AI", key="ask_history"):

    if not question.strip():
        st.warning("Please enter a question.")

    elif not selected_meeting_id:
        st.warning("Please generate a meeting report first.")

    else:
        with st.spinner("Searching meeting history..."):

            try:
                logger.info("Meeting history question submitted")

                answer = ask_meeting_history(
                    question,
                    meeting_id=selected_meeting_id,
                )

                st.markdown("### Answer")
                st.write(answer)

                logger.info("Meeting history question answered successfully")

            except Exception:
                logger.exception("Meeting history Q&A failed")
                st.error("Could not answer your question. " "Please try again.")
