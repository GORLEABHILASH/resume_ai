from resume_tailor_agent.prompts import GLOBAL_SYSTEM, VALIDATION_SYSTEM
from resume_tailor_agent.schemas import ValidationOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def validate_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Source Resume:
{state["resume_text"]}

Job Description:
{state["job_description_text"]}

High-Impact Missing Keywords From Earlier Analysis:
{state.get("missing_keywords", {}).get("high_impact_missing", [])}

Final Output:
{state.get("final_output", {})}
""".strip()

    result = invoke_structured(
        llm,
        ValidationOutput,
        f"{GLOBAL_SYSTEM}\n\n{VALIDATION_SYSTEM}",
        user_prompt,
    )
    return {"validation": result.model_dump()}
