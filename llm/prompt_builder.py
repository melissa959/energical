"""
prompt_builder.py

This module builds the complete prompt sent to the LLM.

It combines:

1. System prompt
2. Few-shot examples
3. Business guardrails
4. Validated RAG products
5. Customer question

The goal is to keep groq_client.py responsible only for
calling the LLM.
"""

import os


class PromptBuilder:

    def __init__(self):

        current_dir = os.path.dirname(os.path.abspath(__file__))

        prompts_folder = os.path.join(
            current_dir,
            "prompts"
        )

        self.system_prompt_path = os.path.join(
            prompts_folder,
            "system_prompt.txt"
        )

        self.examples_path = os.path.join(
            prompts_folder,
            "few_shot_examples.txt"
        )

  

    def load_system_prompt(self):

        if not os.path.exists(self.system_prompt_path):
            return ""

        with open(
            self.system_prompt_path,
            "r",
            encoding="utf-8"
        ) as f:

            return f.read()

    

    def load_examples(self):

        if not os.path.exists(self.examples_path):
            return ""

        with open(
            self.examples_path,
            "r",
            encoding="utf-8"
        ) as f:

            return f.read()

 

    def build_product_context(self, products):

        if len(products) == 0:

            return "No validated products."

        context = ""

        for i, product in enumerate(products, start=1):

            metadata = product["metadata"]

            context += f"""
==================================================
PRODUCT {i}
==================================================

Product ID:
{product["id"]}

Name:
{metadata.get("nom", "Unknown")}

Category:
{metadata.get("categorie", "Unknown")}

Price:
{metadata.get("prix", "Unknown")} DA

Stock:
{metadata.get("statut_stock", "Unknown")}

Description:
{product["document_text"]}

--------------------------------------------------

"""

        return context

 

    def build_prompt(
        self,
        user_question,
        business_result
    ):

        system_prompt = self.load_system_prompt()

        examples = self.load_examples()

        guardrails = business_result["system_prompt"]

        products = self.build_product_context(
            business_result["products"]
        )

        prompt = f"""
==================================================
SYSTEM PROMPT
==================================================

{system_prompt}

==================================================
FEW SHOT EXAMPLES
==================================================

{examples}

==================================================
BUSINESS GUARDRAILS
==================================================

{guardrails}

==================================================
VALIDATED PRODUCTS FROM RAG
==================================================

{products}

==================================================
CUSTOMER QUESTION
==================================================

{user_question}

==================================================
YOUR TASK
==================================================

Carefully read the customer's request.

Use ONLY the validated products above.

Follow ALL business guardrails.

If several products are available:

• Compare them mentally.
• Select the SINGLE BEST product.
• Explain clearly why it is the best choice.

Always include:

• Product name

• Product ID

• Price

• Important characteristics

If a replacement product is provided,
recommend the replacement.

If no validated product exists,
politely explain why.

Never invent:

• products

• IDs

• prices

• specifications

• stock status

Respond in the customer's language
(French, Darija, Arabic or English).

Keep the answer natural,
professional and concise.
"""

        return prompt