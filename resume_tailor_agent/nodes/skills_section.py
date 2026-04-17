from resume_tailor_agent.prompts import GLOBAL_SYSTEM, SKILLS_SYSTEM
from resume_tailor_agent.schemas import SkillsSectionOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def skills_section_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Resume:
{state["resume_text"]}

Existing Skills Section:
{state.get("current_skills_section", "")}

Job Description:
{state["job_description_text"]}

Updated Experience Bullets:
{state.get("updated_experience", [])}

Updated Project Bullets:
{state.get("updated_projects", [])}

Extracted JD Terms:
{state.get("jd_terms", {})}
""".strip()

    result = invoke_structured(
        llm,
        SkillsSectionOutput,
        f"{GLOBAL_SYSTEM}\n\n{SKILLS_SYSTEM}",
        user_prompt,
    )
    return {"updated_skills_section": result.skills_section}
