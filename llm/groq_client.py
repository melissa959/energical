"""
groq_client.py

Phase 4B - LLM Module

Responsibilities
----------------
1. Receive the validated business result.
2. Build the final prompt using PromptBuilder.
3. Send the prompt to Groq.
4. Return the generated recommendation.
"""

import os

from dotenv import load_dotenv
from groq import Groq

from .prompt_builder import PromptBuilder

# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()

# ---------------------------------------------------------
# Initialize Groq client
# ---------------------------------------------------------

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ---------------------------------------------------------
# Initialize Prompt Builder
# ---------------------------------------------------------

prompt_builder = PromptBuilder()


# ---------------------------------------------------------
# Generate final answer
# ---------------------------------------------------------

def generate_answer(
    user_question,
    business_result
):
    """
    Generate the final answer using Groq.

    Parameters
    ----------
    user_question : str

    business_result : dict
        Output of BusinessRecommendationEngine

    Returns
    -------
    str
    """

    # =====================================================
    # Recommendation not allowed
    # =====================================================

    if not business_result["allow_recommendation"]:

        status = business_result["status"]

        if status == "NOT_ENOUGH_TURNS":

            return (
                "I still need a little more information before I can "
                "recommend the best product for you."
            )

        if status == "MISSING_INFORMATION":

            missing = ", ".join(
                business_result["missing_information"]
            )

            return (
                "Before I recommend a product, "
                "I still need the following information:\n\n"
                f"{missing}"
            )

        if status == "UNKNOWN_CATEGORY":

            return (
                "Sorry, I couldn't identify the requested "
                "product category."
            )

        if status == "NO_PRODUCTS_FOUND":

            return (
                "I couldn't find any matching products "
                "in the catalog."
            )

        if status == "NO_AVAILABLE_PRODUCTS":

            return (
                "I found matching products, but unfortunately "
                "they are currently unavailable and no replacement "
                "product exists."
            )

        return business_result["reason"]

    # =====================================================
    # Build prompt
    # =====================================================

    prompt = prompt_builder.build_prompt(

        user_question=user_question,

        business_result=business_result

    )

    # =====================================================
    # Call Groq
    # =====================================================

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        temperature=0.3,

        max_tokens=700,

        messages=[

            {
                "role": "system",
                "content":
                "You are Energical's professional AI sales assistant."
            },

            {
                "role": "user",
                "content": prompt
            }

        ]

    )

    # =====================================================
    # Return answer
    # =====================================================

    return response.choices[0].message.content.strip()