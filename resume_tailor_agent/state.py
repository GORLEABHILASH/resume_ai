from typing import Any

from typing_extensions import TypedDict


class ResumeTailorState(TypedDict, total=False):
    resume_text: str
    job_description_text: str
    company_name: str
    role_title: str
    current_skills_section: str
    existing_experience_bullets: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    graduation_details: str
    work_authorization: str
    model_name: str

    jd_terms: dict[str, list[str]]
    eligibility: dict[str, Any]
    missing_keywords: dict[str, list[str]]
    updated_experience: list[dict[str, Any]]
    updated_projects: list[dict[str, Any]]
    updated_skills_section: str
    final_output: dict[str, Any]
    validation: dict[str, Any]
    errors: list[str]
