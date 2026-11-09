"""Saved resumes, job descriptions, analyses and interview sessions.

Every query is scoped to the authenticated user. A resource that does not exist
and a resource owned by somebody else both return 404 so IDs cannot be
enumerated.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from database import get_db
from models.db import Analysis, InterviewAnswer, InterviewSession, JobDescription, Resume, User
from models.schemas import (
    AnalysisDetail,
    AnalysisSummary,
    InterviewAnswerInput,
    InterviewAnswerResult,
    InterviewSessionDetail,
    InterviewSessionSummary,
    JobDetail,
    JobSummary,
    ResumeDetail,
    ResumeSummary,
    SaveAnalysisInput,
    SaveInterviewInput,
    SaveJobInput,
    SaveResumeInput,
)
from security import get_current_user
from services.interview_service import evaluate_answer, summarize_session

router = APIRouter(tags=["history"])


def _owned(db: Session, model, resource_id: str, user: User):
    record = db.scalar(select(model).where(model.id == resource_id, model.user_id == user.id))
    if record is None:
        raise HTTPException(status_code=404, detail="Resource not found.")
    return record


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------
@router.post("/resumes", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
def save_resume(
    payload: SaveResumeInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ResumeDetail:
    record = Resume(
        user_id=current.id,
        filename=payload.filename,
        text=payload.text,
        structured=payload.structured,
        confidence=payload.confidence,
        warnings=payload.warnings,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ResumeDetail.model_validate(record)


@router.get("/resumes", response_model=list[ResumeSummary])
def list_resumes(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[ResumeSummary]:
    records = db.scalars(
        select(Resume).where(Resume.user_id == current.id).order_by(Resume.created_at.desc())
    ).all()
    return [ResumeSummary.model_validate(record) for record in records]


@router.get("/resumes/{resume_id}", response_model=ResumeDetail)
def get_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ResumeDetail:
    return ResumeDetail.model_validate(_owned(db, Resume, resume_id, current))


@router.delete("/resumes/{resume_id}")
def delete_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    db.delete(_owned(db, Resume, resume_id, current))
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Job descriptions
# ---------------------------------------------------------------------------
@router.post("/jobs", response_model=JobDetail, status_code=status.HTTP_201_CREATED)
def save_job(
    payload: SaveJobInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> JobDetail:
    record = JobDescription(
        user_id=current.id,
        title=payload.title,
        company=payload.company,
        text=payload.text,
        structured=payload.structured,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return JobDetail.model_validate(record)


@router.get("/jobs", response_model=list[JobSummary])
def list_jobs(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[JobSummary]:
    records = db.scalars(
        select(JobDescription)
        .where(JobDescription.user_id == current.id)
        .order_by(JobDescription.created_at.desc())
    ).all()
    return [JobSummary.model_validate(record) for record in records]


@router.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> JobDetail:
    return JobDetail.model_validate(_owned(db, JobDescription, job_id, current))


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    db.delete(_owned(db, JobDescription, job_id, current))
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Analyses
# ---------------------------------------------------------------------------
@router.post("/analyses", response_model=AnalysisDetail, status_code=status.HTTP_201_CREATED)
def save_analysis(
    payload: SaveAnalysisInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> AnalysisDetail:
    if payload.resume_id:
        _owned(db, Resume, payload.resume_id, current)
    if payload.job_id:
        _owned(db, JobDescription, payload.job_id, current)
    record = Analysis(
        user_id=current.id,
        resume_id=payload.resume_id,
        job_id=payload.job_id,
        role=payload.role,
        comparison=payload.comparison,
        ats=payload.ats,
        suggestions=payload.suggestions,
        learning_paths=payload.learning_paths,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return AnalysisDetail.model_validate(record)


@router.get("/analyses", response_model=list[AnalysisSummary])
def list_analyses(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[AnalysisSummary]:
    records = db.scalars(
        select(Analysis).where(Analysis.user_id == current.id).order_by(Analysis.created_at.desc())
    ).all()
    return [AnalysisSummary.model_validate(record) for record in records]


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> AnalysisDetail:
    return AnalysisDetail.model_validate(_owned(db, Analysis, analysis_id, current))


@router.delete("/analyses/{analysis_id}")
def delete_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    db.delete(_owned(db, Analysis, analysis_id, current))
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Interview sessions
# ---------------------------------------------------------------------------
@router.post("/interviews", response_model=InterviewSessionDetail, status_code=status.HTTP_201_CREATED)
def save_interview(
    payload: SaveInterviewInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> InterviewSessionDetail:
    record = InterviewSession(user_id=current.id, role=payload.role, questions=payload.questions)
    db.add(record)
    db.commit()
    db.refresh(record)
    return _session_detail(record)


def _session_detail(record: InterviewSession) -> InterviewSessionDetail:
    answers = [
        InterviewAnswerResult(
            id=answer.id,
            question=answer.question,
            answer=answer.answer,
            score=answer.score,
            feedback=answer.feedback,
        )
        for answer in record.answers
    ]
    summary = summarize_session(
        [
            {"score": answer.score, "category": answer.feedback.get("category", "General")}
            for answer in record.answers
        ]
    )
    return InterviewSessionDetail(
        id=record.id,
        role=record.role,
        created_at=record.created_at,
        completed=record.completed,
        question_count=len(record.questions),
        questions=record.questions,
        answers=answers,
        summary=summary,
    )


@router.get("/interviews", response_model=list[InterviewSessionSummary])
def list_interviews(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[InterviewSessionSummary]:
    records = db.scalars(
        select(InterviewSession)
        .where(InterviewSession.user_id == current.id)
        .order_by(InterviewSession.created_at.desc())
    ).all()
    return [
        InterviewSessionSummary(
            id=record.id,
            role=record.role,
            created_at=record.created_at,
            completed=record.completed,
            question_count=len(record.questions),
        )
        for record in records
    ]


@router.get("/interviews/{session_id}", response_model=InterviewSessionDetail)
def get_interview(
    session_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> InterviewSessionDetail:
    return _session_detail(_owned(db, InterviewSession, session_id, current))


@router.post("/interviews/{session_id}/answers", response_model=InterviewAnswerResult)
def answer_interview(
    session_id: str,
    payload: InterviewAnswerInput,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> InterviewAnswerResult:
    session = _owned(db, InterviewSession, session_id, current)
    feedback = evaluate_answer(payload.question, payload.answer, payload.expected_concepts)
    feedback["category"] = payload.category
    record = InterviewAnswer(
        session_id=session.id,
        question=payload.question,
        answer=payload.answer,
        score=feedback["score"],
        feedback=feedback,
    )
    db.add(record)
    db.flush()
    count = len(db.scalars(select(InterviewAnswer).where(InterviewAnswer.session_id == session.id)).all())
    if session.questions and count >= len(session.questions):
        session.completed = True
    db.commit()
    db.refresh(record)
    return InterviewAnswerResult(
        id=record.id,
        question=record.question,
        answer=record.answer,
        score=record.score,
        feedback=record.feedback,
    )


@router.delete("/interviews/{session_id}")
def delete_interview(
    session_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    db.delete(_owned(db, InterviewSession, session_id, current))
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Privacy controls
# ---------------------------------------------------------------------------
@router.get("/history/export")
def export_history(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    resumes = db.scalars(select(Resume).where(Resume.user_id == current.id)).all()
    jobs = db.scalars(select(JobDescription).where(JobDescription.user_id == current.id)).all()
    analyses = db.scalars(select(Analysis).where(Analysis.user_id == current.id)).all()
    interviews = db.scalars(select(InterviewSession).where(InterviewSession.user_id == current.id)).all()
    return {
        "user": {"id": current.id, "email": current.email, "full_name": current.full_name},
        "resumes": [
            {
                "id": item.id,
                "filename": item.filename,
                "text": item.text,
                "structured": item.structured,
                "created_at": item.created_at.isoformat(),
            }
            for item in resumes
        ],
        "jobs": [
            {"id": item.id, "title": item.title, "company": item.company, "text": item.text}
            for item in jobs
        ],
        "analyses": [
            {
                "id": item.id,
                "role": item.role,
                "comparison": item.comparison,
                "ats": item.ats,
                "suggestions": item.suggestions,
                "learning_paths": item.learning_paths,
                "created_at": item.created_at.isoformat(),
            }
            for item in analyses
        ],
        "interviews": [
            {
                "id": item.id,
                "role": item.role,
                "questions": item.questions,
                "answers": [
                    {"question": answer.question, "answer": answer.answer, "score": answer.score}
                    for answer in item.answers
                ],
            }
            for item in interviews
        ],
        "note": "This export contains the data you saved while signed in.",
    }


@router.delete("/history")
def delete_history(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    for model in (InterviewSession, Analysis, JobDescription, Resume):
        db.execute(delete(model).where(model.user_id == current.id))
    db.commit()
    return {"status": "history_deleted"}
