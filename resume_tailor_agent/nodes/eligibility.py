from resume_tailor_agent.prompts import ELIGIBILITY_SYSTEM, GLOBAL_SYSTEM
from resume_tailor_agent.schemas import EligibilityOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def eligibility_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Candidate Resume:
{state["resume_text"]}

Job Description:
{state["job_description_text"]}

Optional Context:
- Company Name: {state.get("company_name", "")}
- Role Title: {state.get("role_title", "")}
- Graduation Details: {state.get("graduation_details", "")}
- Work Authorization: {state.get("work_authorization", "")}
""".strip()

    result = invoke_structured(
        llm,
        EligibilityOutput,
        f"{GLOBAL_SYSTEM}\n\n{ELIGIBILITY_SYSTEM}",
        user_prompt,
    )
    return {"eligibility": result.model_dump()}
