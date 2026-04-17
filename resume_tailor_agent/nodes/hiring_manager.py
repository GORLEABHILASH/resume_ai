from resume_tailor_agent.prompts import GLOBAL_SYSTEM, HIRING_MANAGER_SYSTEM
from resume_tailor_agent.schemas import BulletRewriteOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def hiring_manager_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Job Description:
{state["job_description_text"]}

Current Updated Experience Bullets:
{state.get("updated_experience", [])}

Current Updated Project Bullets:
{state.get("updated_projects", [])}

Hiring Manager Signals:
{state.get("eligibility", {}).get("hiring_manager_signals", [])}
""".strip()

    result = invoke_structured(
        llm,
        BulletRewriteOutput,
        f"{GLOBAL_SYSTEM}\n\n{HIRING_MANAGER_SYSTEM}",
        user_prompt,
    )
    return {
        "updated_experience": [entry.model_dump() for entry in result.updated_experience],
        "updated_projects": [entry.model_dump() for entry in result.updated_projects],
    }
