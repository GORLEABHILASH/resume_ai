from resume_tailor_agent.prompts import FINAL_ASSEMBLER_SYSTEM, GLOBAL_SYSTEM
from resume_tailor_agent.schemas import FinalOutput
from resume_tailor_agent.utils.llm import get_llm, invoke_structured


def final_assembler_node(state):
    llm = get_llm(state.get("model_name"))
    user_prompt = f"""
Eligibility:
{state.get("eligibility", {})}

JD Terms:
{state.get("jd_terms", {})}

Missing Keywords:
{state.get("missing_keywords", {})}

Final Experience Bullets:
{state.get("updated_experience", [])}

Final Project Bullets:
{state.get("updated_projects", [])}

Final Skills Section:
{state.get("updated_skills_section", "")}
""".strip()

    result = invoke_structured(
        llm,
        FinalOutput,
        f"{GLOBAL_SYSTEM}\n\n{FINAL_ASSEMBLER_SYSTEM}",
        user_prompt,
    )
    return {"final_output": result.model_dump()}
