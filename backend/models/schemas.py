from pydantic import BaseModel, Field


class TextInput(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


class CompareInput(BaseModel):
    resume_skills: list[str]
    job_skills: list[str]


class SuggestionsInput(BaseModel):
    missing_skills: list[str]
    resume_text: str = ""


class UpdateResumeInput(BaseModel):
    resume_text: str
    accepted_suggestions: list[str] = Field(default_factory=list)
    accepted_skills: list[str] = Field(default_factory=list, max_length=20)


class ATSScoreInput(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)
    job_description: str = Field(min_length=1, max_length=100_000)


class ATSSectionScore(BaseModel):
    skills: int = Field(ge=0, le=100)
    experience: int = Field(ge=0, le=100)
    education: int = Field(ge=0, le=100)


class ATSScoreResponse(BaseModel):
    ats_score: int = Field(ge=0, le=100)
    keyword_match: int = Field(ge=0, le=100)
    job_keywords: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    section_score: ATSSectionScore
    formatting_quality: int = Field(ge=0, le=100)
    feedback: list[str]


class LearningPathInput(BaseModel):
    missing_skills: list[str] = Field(min_length=1, max_length=20)


class SkillLearningPath(BaseModel):
    skill: str
    roadmap: list[str] = Field(min_length=3, max_length=5)
    project: str
    duration: str


class LearningPathResponse(BaseModel):
    paths: list[SkillLearningPath]


class RewriteResumeInput(BaseModel):
    resume_text: str = Field(min_length=1, max_length=100_000)
    job_description: str = Field(min_length=1, max_length=100_000)


class RewriteResumeResponse(BaseModel):
    original: str
    rewritten: str
    changes: list[str]
    method: str