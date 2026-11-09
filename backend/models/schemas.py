"""Typed API contracts.

Legacy request/response shapes are retained. New fields are additive and
optional so older clients keep working. Nested analysis artefacts are typed
where the shape is stable and left as dictionaries where the service owns an
evolving report.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------
class TextInput(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict] | None = None
    request_id: str | None = None


# ---------------------------------------------------------------------------
# Legacy analysis endpoints
# ---------------------------------------------------------------------------
class CompareInput(BaseModel):
    resume_skills: list[str] = Field(default_factory=list, max_length=300)
    job_skills: list[str] = Field(default_factory=list, max_length=300)
    preferred_skills: list[str] = Field(default_factory=list, max_length=200)


class SuggestionsInput(BaseModel):
    missing_skills: list[str] = Field(default_factory=list, max_length=50)
    resume_text: str = Field(default="", max_length=100_000)


class UpdateResumeInput(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)
    accepted_suggestions: list[str] = Field(default_factory=list, max_length=50)
    accepted_skills: list[str] = Field(default_factory=list, max_length=20)


class ATSScoreInput(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)
    job_description: str = Field(min_length=1, max_length=100_000)


class ATSSectionScore(BaseModel):
    skills: int = Field(ge=0, le=100)
    experience: int = Field(ge=0, le=100)
    education: int = Field(ge=0, le=100)
    projects: int = Field(default=0, ge=0, le=100)
    certifications: int = Field(default=0, ge=0, le=100)
    contact: int = Field(default=0, ge=0, le=100)


class ATSBreakdownItem(BaseModel):
    component: str
    label: str
    weight: float
    score: int
    points: float
    max_points: float
    explanation: str


class ATSScoreResponse(BaseModel):
    ats_score: int = Field(ge=0, le=100)
    estimated_alignment_score: int = Field(default=0, ge=0, le=100)
    keyword_match: int = Field(ge=0, le=100)
    job_keywords: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    section_score: ATSSectionScore
    formatting_quality: int = Field(ge=0, le=100)
    feedback: list[str]
    breakdown: list[ATSBreakdownItem] = Field(default_factory=list)
    score_breakdown: dict[str, int] = Field(default_factory=dict)
    required_coverage: int = Field(default=0, ge=0, le=100)
    preferred_coverage: int = Field(default=0, ge=0, le=100)
    experience_alignment: int = Field(default=0, ge=0, le=100)
    education_relevance: int = Field(default=0, ge=0, le=100)
    project_relevance: int = Field(default=0, ge=0, le=100)
    score_caps: list[dict] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)
    disclaimer: str = ""


class LearningPathInput(BaseModel):
    missing_skills: list[str] = Field(min_length=1, max_length=20)
    evidence: dict[str, str] | None = None
    requirements: dict[str, str] | None = None


class LearningStage(BaseModel):
    order: int
    title: str
    status: str = "not_started"


class SkillLearningPath(BaseModel):
    skill: str
    roadmap: list[str] = Field(min_length=3, max_length=6)
    project: str
    duration: str
    display: str = ""
    category: str = ""
    level: str = "beginner"
    priority: str = "medium"
    requirement: str = "missing"
    current_evidence: str = "missing"
    objectives: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    exercises: list[str] = Field(default_factory=list)
    stages: list[LearningStage] = Field(default_factory=list)
    completion_status: str = "not_started"
    progress: int = Field(default=0, ge=0, le=100)
    note: str = ""


class LearningPathResponse(BaseModel):
    paths: list[SkillLearningPath]


class RewriteSuggestion(BaseModel):
    id: str
    kind: str
    original: str
    suggestion: str
    rationale: str
    requires_approval: bool = True


class RewriteResumeInput(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)
    job_description: str = Field(min_length=1, max_length=100_000)
    ai_consent: bool = False


class RewriteResumeResponse(BaseModel):
    original: str
    rewritten: str
    changes: list[str]
    method: str
    suggestions: list[RewriteSuggestion] = Field(default_factory=list)
    ai_available: bool = False
    ai_consent_required: bool = True
    fabrication_notice: str = ""


class ResumeEditInput(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)
    instruction: str = Field(min_length=1, max_length=2_000)


class ResumeEditResponse(BaseModel):
    updated_resume_text: str
    reply: str
    change_summary: str
    changed: bool
    method: str
    fit_to_one_page: bool | None = None


# ---------------------------------------------------------------------------
# Structured resume
# ---------------------------------------------------------------------------
class ContactInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class EducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    specialization: str = ""
    graduation_year: str = ""
    gpa: str = ""
    details: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: str = ""
    title: str = ""
    duration: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    title: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    contributions: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)


class CertificationEntry(BaseModel):
    name: str = ""
    issuer: str = ""
    date: str = ""


class SkillsSummary(BaseModel):
    all: list[str] = Field(default_factory=list)
    by_category: dict[str, list[str]] = Field(default_factory=dict)
    category_count: int = 0
    total: int = 0
    from_skills_section: list[str] = Field(default_factory=list)


class StructuredResume(BaseModel):
    contact: ContactInfo
    summary: str = ""
    skills: SkillsSummary
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    section_presence: dict[str, bool] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    word_count: int = 0
    confidence: int = Field(default=0, ge=0, le=100)
    warnings: list[str] = Field(default_factory=list)


class ResumeUploadResponse(BaseModel):
    extracted_text: str
    skills: list[str]
    extraction_confidence: str
    detected_sections: list[str]
    word_count: int
    structured_resume: StructuredResume | None = None
    confidence: int = Field(default=0, ge=0, le=100)
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Combined analysis
# ---------------------------------------------------------------------------
class AnalyzeInput(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)
    job_description: str = Field(min_length=1, max_length=100_000)
    role: str = Field(default="", max_length=200)
    include_interview: bool = True
    interview_limit: int = Field(default=12, ge=1, le=30)


class AnalyzeResponse(BaseModel):
    structured_resume: dict
    resume_skills: list[str]
    job: dict
    comparison: dict
    ats: dict
    suggestions: list[dict]
    learning_paths: list[dict]
    interview: dict
    meta: dict


# ---------------------------------------------------------------------------
# Multi-job matching
# ---------------------------------------------------------------------------
class JobMatchItem(BaseModel):
    id: str = Field(default="", max_length=64)
    title: str = Field(default="", max_length=200)
    company: str = Field(default="", max_length=200)
    text: str = Field(min_length=1, max_length=100_000)


class JobMatchInput(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)
    jobs: list[JobMatchItem] = Field(min_length=1, max_length=25)
    weights: dict[str, float] | None = None


class JobMatchResponse(BaseModel):
    jobs: list[dict]
    ranking: list[dict]
    ranking_explanations: list[dict]
    best_match: dict | None = None
    weights: dict[str, float]
    component_labels: dict[str, str]
    method: str
    disclaimer: str


# ---------------------------------------------------------------------------
# Interview preparation
# ---------------------------------------------------------------------------
class InterviewGenerateInput(BaseModel):
    role: str = Field(default="", max_length=200)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    missing_skills: list[str] = Field(default_factory=list, max_length=100)
    resume_skills: list[str] = Field(default_factory=list, max_length=200)
    resume_text: str = Field(default="", max_length=100_000)
    limit: int = Field(default=12, ge=1, le=30)


class InterviewQuestion(BaseModel):
    id: str
    category: str
    question: str
    difficulty: str = "intermediate"
    related_skill: str = ""
    source: str = ""
    why: str = ""
    answer_framework: str = ""
    expected_concepts: list[str] = Field(default_factory=list)
    project: str = ""
    technologies: list[str] = Field(default_factory=list)


class InterviewGenerateResponse(BaseModel):
    role: str
    questions: list[InterviewQuestion]
    tips: list[str]
    categories: list[str]
    method: str
    disclaimer: str


class InterviewEvaluateInput(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    answer: str = Field(min_length=1, max_length=10_000)
    expected_concepts: list[str] = Field(default_factory=list, max_length=30)
    category: str = Field(default="General", max_length=80)


class InterviewEvaluateResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    relevance: int = Field(ge=0, le=100)
    covered_concepts: list[str]
    missing_concepts: list[str]
    word_count: int
    strengths: list[str]
    improvements: list[str]
    feedback: str
    method: str
    disclaimer: str


# ---------------------------------------------------------------------------
# Authentication and accounts
# ---------------------------------------------------------------------------
class RegisterInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=160)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes.")
        if value.lower() in {"password", "12345678", "qwertyui"}:
            raise ValueError("Choose a less common password.")
        return value


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalise_email(cls, value: str) -> str:
        return value.strip().lower()


class RefreshInput(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=500)


class LogoutInput(BaseModel):
    refresh_token: str = Field(default="", max_length=500)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str = ""
    headline: str = ""
    created_at: datetime | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class UpdateProfileInput(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    headline: str | None = Field(default=None, max_length=200)


class ChangePasswordInput(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class DeleteAccountInput(BaseModel):
    password: str = Field(min_length=1, max_length=128)


# ---------------------------------------------------------------------------
# Persistence / history
# ---------------------------------------------------------------------------
class SaveResumeInput(BaseModel):
    filename: str = Field(default="resume", max_length=255)
    text: str = Field(min_length=1, max_length=100_000)
    structured: dict = Field(default_factory=dict)
    confidence: int = Field(default=0, ge=0, le=100)
    warnings: list[str] = Field(default_factory=list)


class ResumeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    confidence: int
    created_at: datetime


class ResumeDetail(ResumeSummary):
    text: str
    structured: dict
    warnings: list[str]


class SaveJobInput(BaseModel):
    title: str = Field(default="", max_length=200)
    company: str = Field(default="", max_length=200)
    text: str = Field(min_length=1, max_length=100_000)
    structured: dict = Field(default_factory=dict)


class JobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    company: str
    created_at: datetime


class JobDetail(JobSummary):
    text: str
    structured: dict


class SaveAnalysisInput(BaseModel):
    resume_id: str | None = Field(default=None, max_length=32)
    job_id: str | None = Field(default=None, max_length=32)
    role: str = Field(default="", max_length=200)
    comparison: dict = Field(default_factory=dict)
    ats: dict = Field(default_factory=dict)
    suggestions: list[dict] = Field(default_factory=list)
    learning_paths: list[dict] = Field(default_factory=list)


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    created_at: datetime
    resume_id: str | None = None
    job_id: str | None = None


class AnalysisDetail(AnalysisSummary):
    comparison: dict
    ats: dict
    suggestions: list[dict]
    learning_paths: list[dict]


class SaveInterviewInput(BaseModel):
    role: str = Field(default="", max_length=200)
    questions: list[dict] = Field(default_factory=list)


class InterviewAnswerInput(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    answer: str = Field(min_length=1, max_length=10_000)
    category: str = Field(default="General", max_length=80)
    expected_concepts: list[str] = Field(default_factory=list, max_length=30)


class InterviewAnswerResult(BaseModel):
    id: str
    question: str
    answer: str
    score: int
    feedback: dict


class InterviewSessionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    created_at: datetime
    completed: bool
    question_count: int = 0


class InterviewSessionDetail(InterviewSessionSummary):
    questions: list[dict]
    answers: list[InterviewAnswerResult]
    summary: dict
