from resume_tailor_agent.prompts import ADD_KEYWORDS_SYSTEM, GLOBAL_SYSTEM
from resume_tailor_agent.schemas import BulletRewriteOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def add_keywords_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Resume:
{state["resume_text"]}

Existing Experience Bullets:
{state.get("existing_experience_bullets", [])}

Existing Project Bullets:
{state.get("projects", [])}

Job Description:
{state["job_description_text"]}

Keywords That Must Be Added Explicitly:
{state.get("missing_keywords", {}).get("must_add_explicitly", [])}
""".strip()

    result = invoke_structured(
        llm,
        BulletRewriteOutput,
        f"{GLOBAL_SYSTEM}\n\n{ADD_KEYWORDS_SYSTEM}",
        user_prompt,
    )
    return {
        "updated_experience": [entry.model_dump() for entry in result.updated_experience],
        "updated_projects": [entry.model_dump() for entry in result.updated_projects],
    }
