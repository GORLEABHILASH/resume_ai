from resume_tailor_agent.prompts import GLOBAL_SYSTEM, SERVICES_SYSTEM
from resume_tailor_agent.schemas import BulletRewriteOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def add_services_node(state):
    llm = get_llm(state.get("model_name"))
    cloud_keywords = state.get("jd_terms", {}).get("cloud_keywords", [])
    user_prompt = f"""
Job Description:
{state["job_description_text"]}

JD Cloud/Platform Keywords:
{cloud_keywords}

Current Experience Bullets:
{state.get("updated_experience", [])}

Current Project Bullets:
{state.get("updated_projects", [])}

Add these explicitly only where they are supported by the candidate's actual experience.
""".strip()

    result = invoke_structured(
        llm,
        BulletRewriteOutput,
        f"{GLOBAL_SYSTEM}\n\n{SERVICES_SYSTEM}",
        user_prompt,
    )
    return {
        "updated_experience": [entry.model_dump() for entry in result.updated_experience],
        "updated_projects": [entry.model_dump() for entry in result.updated_projects],
    }
