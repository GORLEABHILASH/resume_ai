from resume_tailor_agent.prompts import GLOBAL_SYSTEM, TECH_STACK_SYSTEM
from resume_tailor_agent.schemas import BulletRewriteOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def add_tech_stack_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Job Description:
{state["job_description_text"]}

Extracted JD Terms:
{state.get("jd_terms", {})}

Current Experience Bullets:
{state.get("updated_experience", [])}

Current Project Bullets:
{state.get("updated_projects", [])}
""".strip()

    result = invoke_structured(
        llm,
        BulletRewriteOutput,
        f"{GLOBAL_SYSTEM}\n\n{TECH_STACK_SYSTEM}",
        user_prompt,
    )
    return {
        "updated_experience": [entry.model_dump() for entry in result.updated_experience],
        "updated_projects": [entry.model_dump() for entry in result.updated_projects],
    }
