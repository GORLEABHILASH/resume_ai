from resume_tailor_agent.prompts import GLOBAL_SYSTEM, JD_TERMS_SYSTEM
from resume_tailor_agent.schemas import JDTermsOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def jd_terms_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Job Description:
{state["job_description_text"]}
""".strip()

    result = invoke_structured(
        llm,
        JDTermsOutput,
        f"{GLOBAL_SYSTEM}\n\n{JD_TERMS_SYSTEM}",
        user_prompt,
    )
    return {"jd_terms": result.model_dump()}
