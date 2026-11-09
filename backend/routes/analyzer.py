"""HTTP routes for resume analysis, job intelligence, roadmaps and interviews.

Legacy endpoints and aliases are preserved. New endpoints are additive.
Business logic lives in the service layer; these handlers only validate input
and shape responses.
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from models.schemas import (
    AnalyzeInput,
    AnalyzeResponse,
    ATSScoreInput,
    ATSScoreResponse,
    CompareInput,
    InterviewEvaluateInput,
    InterviewEvaluateResponse,
    InterviewGenerateInput,
    InterviewGenerateResponse,
    JobMatchInput,
    JobMatchResponse,
    LearningPathInput,
    LearningPathResponse,
    ResumeEditInput,
    ResumeEditResponse,
    ResumeUploadResponse,
    RewriteResumeInput,
    RewriteResumeResponse,
    SuggestionsInput,
    TextInput,
    UpdateResumeInput,
)
from services.analyzer import (
    analyze_all,
    compare_skills,
    extract_skills,
    interview_tips,
    make_suggestions,
    update_resume,
)
from services.ats_service import score_resume
from services.interview_service import evaluate_answer, generate_interview_questions
from services.job_match_service import rank_jobs
from services.job_service import analyze_job_description
from services.learning_path_service import generate_learning_paths
from services.resume_edit_service import edit_resume
from services.resume_parser import extract_resume_text
from services.resume_structurer import extract_structured_resume
from services.rewrite_service import rewrite_resume

router = APIRouter()


@router.post("/ats_score", response_model=ATSScoreResponse, include_in_schema=False)
@router.post("/ats-score", response_model=ATSScoreResponse)
async def ats_score(payload: ATSScoreInput):
    return score_resume(payload.resume_text, payload.job_description)


@router.post("/learning_path", response_model=LearningPathResponse, include_in_schema=False)
@router.post("/learning-path", response_model=LearningPathResponse)
async def learning_path(payload: LearningPathInput):
    return {
        "paths": generate_learning_paths(
            payload.missing_skills,
            evidence=payload.evidence,
            requirements=payload.requirements,
        )
    }


@router.post("/rewrite_resume", response_model=RewriteResumeResponse, include_in_schema=False)
@router.post("/rewrite-resume", response_model=RewriteResumeResponse)
async def rewrite(payload: RewriteResumeInput):
    return rewrite_resume(
        payload.resume_text,
        payload.job_description,
        ai_consent=payload.ai_consent,
    )


@router.post("/edit-resume", response_model=ResumeEditResponse)
async def edit_resume_chat(payload: ResumeEditInput):
    return edit_resume(payload.resume_text, payload.instruction.strip())


@router.post("/upload_resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    text = await extract_resume_text(file)
    structured = extract_structured_resume(text)
    sections = [key for key, present in structured["section_presence"].items() if present]
    confidence = structured["confidence"]
    label = "low" if confidence < 45 else "medium" if confidence < 75 else "high"
    return {
        "extracted_text": text,
        "skills": structured["skills"]["all"],
        "extraction_confidence": label,
        "detected_sections": sections,
        "word_count": structured["word_count"],
        "structured_resume": structured,
        "confidence": confidence,
        "warnings": structured["warnings"],
    }


@router.post("/parse-resume")
async def parse_resume(payload: TextInput):
    """Structured extraction for pasted resume text (no upload)."""
    structured = extract_structured_resume(payload.text)
    return {
        "structured_resume": structured,
        "skills": structured["skills"]["all"],
        "confidence": structured["confidence"],
        "warnings": structured["warnings"],
    }


@router.post("/analyze_job")
async def analyze_job(payload: TextInput):
    return analyze_job_description(payload.text)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeInput):
    return analyze_all(
        payload.resume_text,
        payload.job_description,
        role=payload.role,
        include_interview=payload.include_interview,
        interview_limit=payload.interview_limit,
    )


@router.post("/compare")
async def compare(payload: CompareInput):
    return compare_skills(payload.resume_skills, payload.job_skills, payload.preferred_skills)


@router.post("/job-match", response_model=JobMatchResponse)
async def job_match(payload: JobMatchInput):
    return rank_jobs(
        payload.resume_text,
        [job.model_dump() for job in payload.jobs],
        weights=payload.weights,
    )


@router.post("/suggestions")
async def suggestions(payload: SuggestionsInput):
    return {"suggestions": make_suggestions(payload.missing_skills, payload.resume_text)}


@router.post("/update_resume")
async def update(payload: UpdateResumeInput):
    return {
        "updated_resume_text": update_resume(
            payload.resume_text,
            payload.accepted_suggestions,
            payload.accepted_skills,
        )
    }


@router.post("/interview/questions", response_model=InterviewGenerateResponse)
async def interview_questions(payload: InterviewGenerateInput):
    projects = []
    if payload.resume_text.strip():
        projects = extract_structured_resume(payload.resume_text)["projects"]
    return generate_interview_questions(
        payload.role,
        required_skills=payload.required_skills,
        missing_skills=payload.missing_skills,
        resume_skills=payload.resume_skills,
        projects=projects,
        limit=payload.limit,
    )


@router.post("/interview/evaluate", response_model=InterviewEvaluateResponse)
async def interview_evaluate(payload: InterviewEvaluateInput):
    return evaluate_answer(payload.question, payload.answer, payload.expected_concepts)


@router.get("/interview_tips")
async def get_interview_tips(role: str = ""):
    return interview_tips(role)
