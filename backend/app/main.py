import os
import uuid
import json
import logging
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import config
from app.database import get_db, init_db, AnalysisSession, ScreenSpec, GeneratedFile
from app.schemas import AnswerQuestionsRequest, SessionResponse
from app.services.ai_service import AIService
from app.services.validator import SpecValidator
from app.services.docx_gen import DOCXGenerator

# Setup logs formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ba_agent.main")

app = FastAPI(
    title="Screen-to-Spec BA Agent MVP API",
    description="API for analyzing screen mockups and generating Word document specifications.",
    version="2.0.0"
)

# Enable CORS for Next.js and frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database tables on app startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing database schemas...")
    init_db()

    # Mount the uploads directory to serve files if needed
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    app.mount("/static", StaticFiles(directory=config.UPLOAD_DIR), name="static")
    logger.info(f"Database schemas successfully initialized. Uploads mounted at /static")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to Screen-to-Spec BA Agent API",
        "version": "2.0.0",
        "provider": config.AI_PROVIDER,
        "database": "SQLite (Local File)" if config.DATABASE_URL.startswith("sqlite") else "PostgreSQL Server"
    }


# ══════════════════════════════════════════════
# Helper: Build the full spec dict from session
# ══════════════════════════════════════════════

def _build_spec_from_session(session: AnalysisSession) -> dict:
    """Reconstructs the full spec dict from session fields."""
    return {
        "screen_name": session.screen_name or "",
        "screen_type": session.screen_type or "Unknown",
        "screen_summary": session.screen_summary or "",
        "ready_to_generate_docx": session.ready_to_generate_docx or False,
        "clarifying_questions": session.questions or [],
        "assumptions": session.assumptions or [],
        "rows": session.specification or [],
    }


def _save_spec_version(db: Session, session_id: str, spec: dict, version: int):
    """Saves a snapshot of the spec for versioning."""
    spec_record = ScreenSpec(
        session_id=session_id,
        spec_json=spec,
        version=version,
    )
    db.add(spec_record)


def _get_current_version(db: Session, session_id: str) -> int:
    """Gets the latest spec version number for a session."""
    latest = (
        db.query(ScreenSpec)
        .filter(ScreenSpec.session_id == session_id)
        .order_by(ScreenSpec.version.desc())
        .first()
    )
    return latest.version if latest else 0


# ══════════════════════════════════════════════
# 1. API: Upload image + context, AI first analysis
# ══════════════════════════════════════════════

@app.post("/api/screen/analyze", response_model=SessionResponse)
async def analyze_screen(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    screen_name: Optional[str] = Form(None),
    module: Optional[str] = Form(None),
    screen_type: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    session_id = str(uuid.uuid4())
    logger.info(f"Received screen analyze request. Session ID: {session_id}")

    # Validate file type
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(
            status_code=400,
            detail="File type not supported. Please upload an image (.png, .jpg, .jpeg, .webp)."
        )

    # Save uploaded file
    file_path = os.path.join(config.UPLOAD_DIR, f"{session_id}{ext}")
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"Saved uploaded file to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded image.")

    # Call AI vision model for Stage 1 analysis
    try:
        analysis_result = AIService.analyze_screenshot(
            image_path=file_path,
            context=context or "",
            screen_name=screen_name or "",
            module=module or "",
            screen_type=screen_type or "",
            role=role or "",
        )
        logger.info(f"AI analysis result keys: {list(analysis_result.keys())}")
    except Exception as e:
        logger.error(f"AI service failed to analyze screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail="AI Vision Service failed to process screenshot.")

    # Validate and clean the full spec
    cleaned_spec, validation_warnings = SpecValidator.validate_full_spec(analysis_result)
    if validation_warnings:
        logger.info(f"Validation warnings: {validation_warnings}")

    # Extract structured fields from the cleaned spec
    ai_screen_name = cleaned_spec.get("screen_name", screen_name or "")
    ai_screen_type = cleaned_spec.get("screen_type", screen_type or "Unknown")
    ai_screen_summary = cleaned_spec.get("screen_summary", "")
    ai_ready = cleaned_spec.get("ready_to_generate_docx", False)
    ai_questions = cleaned_spec.get("clarifying_questions", [])
    ai_assumptions = cleaned_spec.get("assumptions", [])
    ai_rows = cleaned_spec.get("rows", [])

    # Determine status
    has_critical = any(q.get("priority") == "critical" and not q.get("answered") for q in ai_questions)
    has_any_questions = len(ai_questions) > 0

    if has_critical or has_any_questions:
        status = "waiting_user_answer"
    elif ai_ready:
        status = "ready_to_generate"
    else:
        status = "ready_to_generate"

    # Save session to Database
    new_session = AnalysisSession(
        id=session_id,
        screen_name=ai_screen_name or screen_name,
        module=module,
        screen_type=ai_screen_type,
        role=role,
        context=context,
        image_path=file_path,
        screen_summary=ai_screen_summary,
        ready_to_generate_docx=ai_ready,
        status=status,
        questions=ai_questions,
        assumptions=ai_assumptions,
        specification=ai_rows,
        docx_path=None,
    )

    db.add(new_session)

    # Save spec version 1
    _save_spec_version(db, session_id, cleaned_spec, version=1)

    db.commit()
    db.refresh(new_session)

    logger.info(f"Created session {session_id} | status={status} | controls={len(ai_rows)} | questions={len(ai_questions)}")
    return new_session


# ══════════════════════════════════════════════
# 2. API: User submits answers, AI refines spec (multi-turn)
# ══════════════════════════════════════════════

@app.post("/api/screen/answer-questions/{session_id}", response_model=SessionResponse)
def answer_questions(
    session_id: str,
    payload: AnswerQuestionsRequest,
    db: Session = Depends(get_db)
):
    logger.info(f"Received answers for session {session_id}. Auto-generate: {payload.auto_generate}")

    # Retrieve session from DB
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.status not in ("waiting_user_answer", "ready_to_generate"):
        raise HTTPException(
            status_code=400,
            detail=f"Session is in '{session.status}' status and cannot receive answers."
        )

    # Update answers in the questions list
    qna_list = session.questions or []
    answers_dict = {ans.id: ans.answer for ans in payload.answers}

    updated_qna = []
    provided_answers_for_ai = []

    for q in qna_list:
        q_copy = q.copy()
        qid = q_copy.get("id")

        if qid in answers_dict:
            q_copy["answer"] = answers_dict[qid]
            q_copy["answered"] = True
            provided_answers_for_ai.append({
                "id": qid,
                "question": q_copy.get("question"),
                "answer": answers_dict[qid]
            })
        elif payload.auto_generate:
            q_copy["answer"] = "(Tự động xác nhận theo giả định của AI)"
            q_copy["answered"] = True
            provided_answers_for_ai.append({
                "id": qid,
                "question": q_copy.get("question"),
                "answer": "Tự động xác nhận theo giả định / mặc định tối ưu nhất."
            })

        updated_qna.append(q_copy)

    # If not all questions answered and auto_generate is false, just save partial answers
    if not payload.auto_generate and any(not q.get("answered") for q in updated_qna):
        logger.info("Some questions remain unanswered. Saving partial answers only.")
        session.questions = updated_qna
        db.commit()
        db.refresh(session)
        return session

    # Build previous spec for AI refinement
    previous_spec = _build_spec_from_session(session)
    # Update questions with answers for the AI
    previous_spec["clarifying_questions"] = updated_qna

    # Call AI Stage 2 for refinement
    try:
        refined_result = AIService.refine_specification(
            image_path=session.image_path,
            previous_spec=previous_spec,
            user_answers=provided_answers_for_ai,
        )
    except Exception as e:
        logger.error(f"AI service failed to refine specification: {str(e)}")
        raise HTTPException(status_code=500, detail="AI Vision Service failed to refine specification.")

    # Validate the refined spec
    cleaned_spec, validation_warnings = SpecValidator.validate_full_spec(refined_result)
    if validation_warnings:
        logger.info(f"Refinement validation warnings: {validation_warnings}")

    # Extract updated fields
    new_questions = cleaned_spec.get("clarifying_questions", [])
    new_assumptions = cleaned_spec.get("assumptions", [])
    new_rows = cleaned_spec.get("rows", [])
    new_ready = cleaned_spec.get("ready_to_generate_docx", False)

    # Determine new status based on remaining critical questions
    has_critical_unanswered = any(
        q.get("priority") == "critical" and not q.get("answered", False)
        for q in new_questions
    )

    if has_critical_unanswered:
        new_status = "waiting_user_answer"
    elif new_ready:
        new_status = "ready_to_generate"
    else:
        new_status = "ready_to_generate"

    # Update session
    session.screen_name = cleaned_spec.get("screen_name", session.screen_name)
    session.screen_type = cleaned_spec.get("screen_type", session.screen_type)
    session.screen_summary = cleaned_spec.get("screen_summary", session.screen_summary)
    session.ready_to_generate_docx = new_ready
    session.questions = new_questions
    session.assumptions = new_assumptions
    session.specification = new_rows
    session.status = new_status

    # Save spec version
    current_version = _get_current_version(db, session_id)
    _save_spec_version(db, session_id, cleaned_spec, version=current_version + 1)

    db.commit()
    db.refresh(session)

    logger.info(
        f"Refined session {session_id} | status={new_status} | "
        f"controls={len(new_rows)} | new_questions={len(new_questions)} | ready={new_ready}"
    )
    return session


# ══════════════════════════════════════════════
# 3. API: View preview table
# ══════════════════════════════════════════════

@app.get("/api/screen/preview/{session_id}")
def preview_spec(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "rows": session.specification or [],
        "assumptions": session.assumptions or [],
        "screen_summary": session.screen_summary or "",
        "ready_to_generate_docx": session.ready_to_generate_docx,
    }


# ══════════════════════════════════════════════
# 4. API: Update specification inline (user edits)
# ══════════════════════════════════════════════

@app.put("/api/screen/update-spec/{session_id}", response_model=SessionResponse)
def update_spec_inline(
    session_id: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """Allows user to manually edit the specification rows inline."""
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    new_rows = payload.get("rows", [])
    if not new_rows:
        raise HTTPException(status_code=400, detail="No rows provided.")

    # Validate and clean the user-edited rows
    warnings_list = []
    cleaned_rows = SpecValidator.validate_and_clean_rows(new_rows, warnings_list)

    session.specification = cleaned_rows

    # Save new spec version
    spec = _build_spec_from_session(session)
    spec["rows"] = cleaned_rows
    current_version = _get_current_version(db, session_id)
    _save_spec_version(db, session_id, spec, version=current_version + 1)

    db.commit()
    db.refresh(session)

    logger.info(f"User edited spec for session {session_id}, {len(cleaned_rows)} rows saved.")
    return session


# ══════════════════════════════════════════════
# 5. API: Generate DOCX (with draft vs official)
# ══════════════════════════════════════════════

@app.post("/api/screen/generate-docx/{session_id}", response_model=SessionResponse)
def generate_docx(
    session_id: str,
    is_draft: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    logger.info(f"Generating DOCX for session {session_id} | draft={is_draft}")
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if not session.specification:
        raise HTTPException(status_code=400, detail="No specifications available. Please complete analysis first.")

    # Check if official DOCX is allowed
    if not is_draft:
        spec = _build_spec_from_session(session)
        can_generate, reason = SpecValidator.can_generate_official_docx(spec)
        if not can_generate:
            raise HTTPException(
                status_code=400,
                detail=f"Không thể tạo DOCX chính thức: {reason} Vui lòng dùng chế độ bản nháp."
            )

    # Optional: Run QA check (Stage 3) before generating
    if not is_draft:
        try:
            spec_for_qa = _build_spec_from_session(session)
            qa_result = AIService.qa_check_specification(
                image_path=session.image_path,
                spec=spec_for_qa,
            )
            # Re-validate QA result
            cleaned_qa, _ = SpecValidator.validate_full_spec(qa_result)
            qa_rows = cleaned_qa.get("rows", session.specification)

            # Update session with QA-corrected rows
            session.specification = qa_rows
            session.screen_summary = cleaned_qa.get("screen_summary", session.screen_summary)
        except Exception as e:
            logger.warning(f"QA check failed, proceeding with existing spec: {str(e)}")

    # Save to code/download (which is parent of backend folder + /download)
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    download_dir = os.path.join(root_dir, "download")
    os.makedirs(download_dir, exist_ok=True)

    try:
        docx_path = DOCXGenerator.generate_docx(
            session_id=session.id,
            screen_name=session.screen_name or "Chưa xác định",
            screen_type=session.screen_type or "Unknown",
            module=session.module,
            role=session.role,
            context=session.context,
            screen_summary=session.screen_summary,
            assumptions=session.assumptions or [],
            controls=session.specification,
            output_dir=download_dir,
            is_draft=is_draft,
            image_path=session.image_path,
        )
    except Exception as e:
        logger.error(f"DOCX generator service failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate DOCX document.")

    # Track generated file
    file_record = GeneratedFile(
        session_id=session.id,
        file_name=os.path.basename(docx_path),
        file_path=docx_path,
        file_type="docx",
        is_draft=is_draft,
    )
    db.add(file_record)

    # Update session
    session.docx_path = docx_path
    session.status = "docx_generated"
    db.commit()
    db.refresh(session)

    logger.info(f"Generated {'draft ' if is_draft else ''}DOCX for session {session_id}")
    return session


# ══════════════════════════════════════════════
# 6. API: Download DOCX file
# ══════════════════════════════════════════════

@app.get("/api/screen/download/{session_id}")
def download_docx(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if not session.docx_path or not os.path.exists(session.docx_path):
        raise HTTPException(status_code=404, detail="DOCX file not found. Please generate it first.")

    return FileResponse(
        path=session.docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(session.docx_path)
    )


# ══════════════════════════════════════════════
# 7. API: View single session
# ══════════════════════════════════════════════

@app.get("/api/screen/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


# ══════════════════════════════════════════════
# 8. API: List all sessions
# ══════════════════════════════════════════════

@app.get("/api/screen/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(AnalysisSession).order_by(AnalysisSession.created_at.desc()).all()
    return sessions
