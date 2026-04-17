import os
from typing import Optional

from langchain_openai import ChatOpenAI


def get_llm(model_name: Optional[str] = None) -> ChatOpenAI:
    model = model_name or os.getenv("OPENAI_MODEL", "gpt-4.1")
    return ChatOpenAI(model=model, temperature=0)


def invoke_structured(llm: ChatOpenAI, schema, system_prompt: str, user_prompt: str):
    structured_llm = llm.with_structured_output(schema)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return structured_llm.invoke(messages)
