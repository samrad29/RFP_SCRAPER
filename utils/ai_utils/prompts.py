"""
AI Utils
This module will contain the functions to use the AI models to help with the RFPs
General Structure is to send to llama on groq to classify if the text is an rfp or now. 
Then, if it is, we can use gpt-4o-mini to extract the data.
"""

import os
from dotenv import load_dotenv
import groq
import openai

def get_groq_client(groq_api_key: str) -> groq.Client:
    """
    Get the Groq client
    """
    return groq.Client(api_key=groq_api_key)

def get_openai_client(openai_api_key: str) -> openai.OpenAI:
    """
    Get the OpenAI client
    """
    return openai.OpenAI(api_key=openai_api_key)


def ai_classify_rfp(text: str, groq_client, groq_model_name: str) -> bool:
    """
    Classify if the text is an rfp or not
    """
    response = groq_client.chat.completions.create(
        model=groq_model_name,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict classification system.\n"
                    "Your task is to determine whether a document is a Request for Proposal (RFP), "
                    "procurement notice, grant solicitation, or similar funding opportunity.\n\n"
                    "Return ONLY one of the following outputs:\n"
                    "- RFP\n"
                    "- NOT_RFP\n\n"
                    "Do not explain your answer. Do not add punctuation. Do not include any extra text."
                )
            },
            {
                "role": "user",
                "content": f"Classify this document:\n\n--- DOCUMENT START ---\n{text[:12000]}\n--- DOCUMENT END ---"
            }
        ]
    )

    return response.choices[0].message.content.strip() == "RFP"

def ai_extract_rfp_data(text: str, openai_client: openai.OpenAI, openai_model_name: str) -> dict:
    """
    Extract the data from the text
    """
    return None