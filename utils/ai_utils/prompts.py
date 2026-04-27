"""
AI Utils
This module will contain the functions to use the AI models to help with the RFPs
General Structure is to send to llama on groq to classify if the text is an rfp or now. 
Then, if it is, we can use gpt-4o-mini to extract the data.
"""

from operator import truediv
import os
import json
from dotenv import load_dotenv

from utils.ai_utils.req_resp_obj import LLMRequest, LLMMessage, LLMResponse
from utils.ai_utils.llm_clients import LLMService

from utils.text_utils import better_extraction_text

load_dotenv()
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")


def _extract_json_payload(content: str) -> str:
    """
    Normalize LLM output into a JSON string.
    Handles plain JSON and markdown fenced JSON blocks.
    """
    if not content:
        return ""

    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]

    return stripped


def ai_classify_rfp(text: str, llm: LLMService) -> bool:
    """
    Classify if the text is an rfp or not
    """
    system_content = (
                    "You are a strict classification system.\n"
                    "Your task is to determine whether a document is a Request for Proposal (RFP), "
                    "procurement notice, grant solicitation, or similar funding opportunity.\n\n"
                    "Return ONLY one of the following outputs:\n"
                    "- RFP\n"
                    "- NOT_RFP\n\n"
                    "Do not explain your answer. Do not add punctuation. Do not include any extra text."
                )
    user_content = f"Classify this document:\n\n--- DOCUMENT START ---\n{text[:8000]}\n--- DOCUMENT END ---"

    req = LLMRequest(
        model=GROQ_MODEL_NAME,
        provider="groq",
        messages=[
            LLMMessage(role="system", content=system_content),
            LLMMessage(role="user", content=user_content),
        ],
    )

    result = llm.generate(req)
    print(f"Context Tokens for RFP classification: {result.prompt_tokens}")
    print(f"Completion Tokens for RFP classification: {result.completion_tokens}")
    print(f"Total Tokens for RFP classification: {result.total_tokens}")
    print(f"Result content: {result.content}")
    result_content = result.content.lower()
    if result_content not in ["rfp", "rfq", "not_rfp"]:
        print(f"UNEXPECTED AI CLASSIFICATION RESULT: {result_content}")
        return False

    if ("rfp" in result_content or "rfq" in result_content) and "not_rfp" not in result_content:
        return True
    else:
        return False  


def ai_extract_rfp_data(text: str, llm: LLMService) -> dict:
    """
    Extract data and categorize the RFP from the text
    """
    better_text = better_extraction_text(text)

    system_content = (
        "You are a strict information extraction and categorization system.\n"
        "Extract structured data from an RFP document and determine the category of work this RFP is for.\n\n"
        "If you are not 99% sure about a field, return null.\nDo NOT guess or infer missing values.\n\n"
        "---\n\n"
        "Return JSON with EXACTLY these fields:\n"
        "- title: string or NULL\n"
        "- issueing_organization: string or NULL\n"
        "- description: string or NULL\n"
        "- deadline: string (YYYY-MM-DD) or NULL\n"
        "- deadline_description: string or NULL\n"
        "- link: string or NULL\n"
        "- attachments: array of strings or empty array,\n"
        "- categories: array of string (one or more of the following: Construction, Consulting, Auditing, Financial, Legal, Marketing, Human Resources, IT, Other)"
    )
    user_content = f"Extract data and categorize the RFP from this text and return it in a JSON object:\n\n{better_text}"
    req = LLMRequest(
        model=OPENAI_MODEL_NAME,
        provider="openai",
        messages=[
            LLMMessage(role="system", content=system_content),
            LLMMessage(role="user", content=user_content),
        ],
    )
    result = llm.generate(req)
    print(f"Context Tokens for RFP data extraction: {result.prompt_tokens}")
    print(f"Completion Tokens for RFP data extraction: {result.completion_tokens}")
    print(f"Total Tokens for RFP data extraction: {result.total_tokens}")
    print(f"Result content: {result.content}")
    try:
        parsed_content = _extract_json_payload(result.content)
        return json.loads(parsed_content)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Result content: {result.content}")
        return None