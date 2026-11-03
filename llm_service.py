import os
import logging
import time

import logging_config
import streamlit as st

from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIConnectionError, APIStatusError

logger = logging.getLogger(__name__)

load_dotenv()


def get_api_key():
    """Read the API key from environment variables or Streamlit secrets."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            api_key = None

    if not api_key:
        logger.critical("GROQ_API_KEY is missing from configuration")
        raise ValueError(
            "GROQ_API_KEY is missing. Configure it in your .env "
            "file or Streamlit secrets."
        )

    return api_key


client = Groq(api_key=get_api_key())


def get_completion(prompt, model="openai/gpt-oss-120b"):
    """Send a prompt to Groq and return the generated response."""

    start_time = time.perf_counter()

    logger.info("LLM request started | Model: %s", model)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        content = response.choices[0].message.content

        duration = time.perf_counter() - start_time

        logger.info(
            "LLM request completed | Model: %s | Duration: %.2f seconds",
            model,
            duration,
        )

        return content

    except RateLimitError:
        logger.error("Groq rate limit exceeded")
        raise

    except APIConnectionError:
        logger.error("Could not connect to Groq API")
        raise

    except APIStatusError as exc:
        logger.error(
            "Groq API returned an error | HTTP Status: %s",
            exc.status_code,
        )
        raise

    except Exception:
        logger.exception("Unexpected error during LLM request")
        raise
