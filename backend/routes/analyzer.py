from fastapi import APIRouter, File, UploadFile

from models.schemas import ATSScoreInput, ATSScoreResponse, CompareInput, LearningPathInput, LearningPathResponse, RewriteResumeInput, RewriteResumeResponse, SuggestionsInput, TextInput, UpdateResumeInput
from services.ats_service import score_resume
from services.analyzer import compare_skills, extract_skills, interview_tips, make_suggestions, update_resume
from services.learning_path_service import generate_learning_paths
from services.rewrite_service import rewrite_resume
from services.resume_parser import extract_resume_text

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


@router.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    text = await extract_resume_text(file)
    return {"extracted_text": text, "skills": extract_skills(text)}


@router.post("/analyze_job")
async def analyze_job(payload: TextInput):
    return {"required_skills": extract_skills(payload.text)}


@router.post("/compare")
async def compare(payload: CompareInput):
    return compare_skills(payload.resume_skills, payload.job_skills)


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