import re

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import ATSScoreInput, ATSScoreResponse, CompareInput, LearningPathInput, LearningPathResponse, ResumeEditInput, ResumeEditResponse, RewriteResumeInput, RewriteResumeResponse, SuggestionsInput, TextInput, UpdateResumeInput
from services.ats_service import score_resume
from services.analyzer import analyze_job_description, compare_skills, extract_skills, interview_tips, make_suggestions, update_resume
from services.learning_path_service import generate_learning_paths
from services.rewrite_service import rewrite_resume
from services.resume_parser import extract_resume_text
from services.resume_edit_service import edit_resume

router = APIRouter()


@router.post("/ats_score", response_model=ATSScoreResponse, include_in_schema=False)
@router.post("/ats-score", response_model=ATSScoreResponse)
async def ats_score(payload: ATSScoreInput):
    return score_resume(payload.resume_text, payload.job_description)


@router.post("/learning_path", response_model=LearningPathResponse, include_in_schema=False)
@router.post("/learning-path", response_model=LearningPathResponse)
async def learning_path(payload: LearningPathInput):
    return {"paths": generate_learning_paths(payload.missing_skills)}


@router.post("/rewrite_resume", response_model=RewriteResumeResponse, include_in_schema=False)
@router.post("/rewrite-resume", response_model=RewriteResumeResponse)
async def rewrite(payload: RewriteResumeInput):
    return rewrite_resume(payload.resume_text, payload.job_description)


@router.post("/edit-resume", response_model=ResumeEditResponse)
async def edit_resume_chat(payload: ResumeEditInput):
    try:
        return edit_resume(payload.resume_text, payload.instruction.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    text = await extract_resume_text(file)
    words = len(text.split())
    sections = [name for name, pattern in {
        "experience": r"\b(experience|employment history|work history)\b",
        "education": r"\b(education|university|college|degree)\b",
        "skills": r"\b(skills|technical skills|competencies)\b",
        "projects": r"\bprojects?\b",
        "certifications": r"\bcertifications?\b",
    }.items() if re.search(pattern, text, re.I)]
    confidence = "low" if words < 35 else "medium" if words < 90 or len(sections) < 2 else "high"
    return {"extracted_text": text, "skills": extract_skills(text), "extraction_confidence": confidence,
            "detected_sections": sections, "word_count": words}


@router.post("/analyze_job")
async def analyze_job(payload: TextInput):
    return analyze_job_description(payload.text)


@router.post("/compare")
async def compare(payload: CompareInput):
    return compare_skills(payload.resume_skills, payload.job_skills, payload.preferred_skills)


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


@router.get("/interview_tips")
async def get_interview_tips(role: str = ""):
    return interview_tips(role)
