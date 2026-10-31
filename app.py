from groq import APIConnectionError, APIStatusError, RateLimitError
from pydantic import ValidationError
import streamlit as st
import uuid
import json

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

st.set_page_config(
    page_title="MeetBrain AI",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 MeetBrain AI")
st.caption("Turn meeting transcripts into actionable intelligence.")

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

            with st.expander("Preview transcript"):
                st.text(transcript)

        except ValueError as exc:
            st.error(str(exc))
        except Exception:
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
                result = run_meeting_graph(transcript)

                if result["error"]:
                    st.error(f"Meeting workflow failed: {result['error']}")
                    st.stop()

                report_data = result["report"]

                # Generate one ID and use it for both collections.
                meeting_id = str(uuid.uuid4())

                # Save the complete meeting report.
                save_meeting(meeting_id, report_data)

                # Save searchable section chunks.
                saved_chunks = save_meeting_chunks(
                    chunk_collection,
                    embedding_model,
                    meeting_id,
                    report_data,
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

            except RateLimitError:
                st.error("Groq rate limit reached. Please wait and try again.")
            except APIConnectionError:
                st.error(
                    "Could not connect to Groq. "
                    "Check your internet connection and retry."
                )
            except APIStatusError as exc:
                st.error(
                    f"Groq returned an API error "
                    f"(HTTP {exc.status_code}). Please retry later."
                )
            except ValidationError:
                st.error(
                    "The generated report did not match "
                    "the expected format. Please try again."
                )
            except Exception as exc:
                st.error(f"Could not generate the report: {exc}")


st.divider()

st.header("Ask Your Meeting History")

meetings = list_meetings()

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
                answer = ask_meeting_history(
                    question,
                    meeting_id=selected_meeting_id,
                )

                st.markdown("### Answer")
                st.write(answer)

            except Exception as exc:
                st.error(f"Could not answer your question: {exc}")
