from resume_tailor_agent.prompts import GLOBAL_SYSTEM, KEYWORD_GAP_SYSTEM
from resume_tailor_agent.schemas import KeywordGapOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def keyword_gap_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Resume:
{state["resume_text"]}

Job Description:
{state["job_description_text"]}

JD Terms:
{state.get("jd_terms", {})}

Under-signaled Areas:
{state.get("eligibility", {}).get("under_signaled_areas", [])}
""".strip()

    result = invoke_structured(
        llm,
        KeywordGapOutput,
        f"{GLOBAL_SYSTEM}\n\n{KEYWORD_GAP_SYSTEM}",
        user_prompt,
    )
    return {"missing_keywords": result.model_dump()}
