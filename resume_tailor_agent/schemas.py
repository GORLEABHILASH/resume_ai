from pydantic import BaseModel, Field


class EligibilityOutput(BaseModel):
    verdict: str = Field(..., description="Overall eligibility verdict.")
    reasons: list[str] = Field(default_factory=list)
    top_role_priorities: list[str] = Field(default_factory=list)
    strong_matches: list[str] = Field(default_factory=list)
    under_signaled_areas: list[str] = Field(default_factory=list)
    tailoring_strategy: list[str] = Field(default_factory=list)
    hiring_manager_signals: list[str] = Field(default_factory=list)


class JDTermsOutput(BaseModel):
    languages: list[str] = Field(default_factory=list)
    backend_keywords: list[str] = Field(default_factory=list)
    systems_keywords: list[str] = Field(default_factory=list)
    cloud_keywords: list[str] = Field(default_factory=list)
    process_keywords: list[str] = Field(default_factory=list)
    ai_keywords: list[str] = Field(default_factory=list)


class KeywordGapOutput(BaseModel):
    high_impact_missing: list[str] = Field(default_factory=list)
    medium_impact_missing: list[str] = Field(default_factory=list)
    already_explicit: list[str] = Field(default_factory=list)
    implied_but_not_explicit: list[str] = Field(default_factory=list)
    must_add_explicitly: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: str
    role: str
    bullets: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str
    bullets: list[str] = Field(default_factory=list)


class BulletRewriteOutput(BaseModel):
    updated_experience: list[ExperienceEntry] = Field(default_factory=list)
    updated_projects: list[ProjectEntry] = Field(default_factory=list)


class SkillsSectionOutput(BaseModel):
    skills_section: str


class FinalOutput(BaseModel):
    tailored_summary: str = ""
    tailored_experience: list[ExperienceEntry] = Field(default_factory=list)
    tailored_projects: list[ProjectEntry] = Field(default_factory=list)
    tailored_skills_section: str
    covered_keywords: list[str] = Field(default_factory=list)
    top_strengths: list[str] = Field(default_factory=list)
    final_notes: list[str] = Field(default_factory=list)


class ValidationOutput(BaseModel):
    supported_only: bool = Field(..., description="Whether all claims appear supported by the provided inputs.")
    invented_experience_risk: list[str] = Field(default_factory=list)
    repetitive_phrasing_risk: list[str] = Field(default_factory=list)
    uncovered_high_impact_keywords: list[str] = Field(default_factory=list)
    validation_notes: list[str] = Field(default_factory=list)
