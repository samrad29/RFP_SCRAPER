"""
AI Utils
This module will contain the functions to use the AI models to help with the RFPs
General Structure is to send to llama on groq to classify if the text is an rfp or now. 
Then, if it is, we can use gpt-4o-mini to extract the data.
"""

import os
from dotenv import load_dotenv

from utils.ai_utils.req_resp_obj import LLMRequest, LLMMessage
from utils.ai_utils.llm_clients import LLMService

load_dotenv()
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")


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
    print(f"Context Tokens: {result.prompt_tokens}")
    print(f"Completion Tokens: {result.completion_tokens}")
    print(f"Total Tokens: {result.total_tokens}")
    print(f"Result content: {result.content}")
    is_rfp = "RFP" in result.content and "NOT_RFP" not in result.content
    return is_rfp

def ai_extract_rfp_data(text: str, llm: LLMService) -> dict:
    """
    Extract the data from the text
    """
    return None