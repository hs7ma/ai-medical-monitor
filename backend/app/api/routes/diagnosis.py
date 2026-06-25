import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.chat import ChatSession, ChatMessage
from app.models.medical_file import MedicalFile
from app.services.diagnosis_engine import diagnosis_engine
from app.services.openai_service import chat_with_ai, chat_with_ai_stream
from app.schemas.chat import (
    ChatSessionOut,
    ChatMessageOut,
    StartSessionRequest,
    SendMessageRequest,
)

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])
logger = logging.getLogger(__name__)


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
def start_session(
    payload: StartSessionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    session = ChatSession(
        patient_id=payload.patient_id,
        user_id=user.id,
        title=payload.title or f"تشخيص - {patient.name}",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=List[ChatSessionOut])
def list_sessions(
    patient_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    query = db.query(ChatSession)
    if patient_id:
        query = query.filter(ChatSession.patient_id == patient_id)
    return query.order_by(ChatSession.updated_at.desc()).all()


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    has_files = bool(payload.file_ids)
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=payload.message,
        has_files=has_files,
    )
    db.add(user_msg)
    db.commit()

    context = diagnosis_engine.gather_context(session.patient_id, db)
    context_msg = diagnosis_engine.build_context_message(context)

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    conversation = [{"role": m.role, "content": m.content} for m in history]

    result = await chat_with_ai(
        context=context_msg,
        conversation=conversation,
        file_images=context["file_images"],
    )

    ai_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=result["reply"],
    )
    db.add(ai_msg)

    if result["diagnosis"]:
        session.diagnosis_result = result["diagnosis"]
        session.status = "completed"

    db.commit()
    db.refresh(ai_msg)

    return {
        "message": ChatMessageOut.model_validate(ai_msg).model_dump(),
        "diagnosis": result["diagnosis"],
        "session_status": session.status,
        "extracted_indicators": result.get("extracted_indicators"),
    }


@router.post("/sessions/{session_id}/stream")
async def stream_message(
    session_id: int,
    payload: SendMessageRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    has_files = bool(payload.file_ids)
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=payload.message,
        has_files=has_files,
    )
    db.add(user_msg)
    db.commit()

    context = diagnosis_engine.gather_context(session.patient_id, db)
    context_msg = diagnosis_engine.build_context_message(context)

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    conversation = [{"role": m.role, "content": m.content} for m in history]

    session_id_final = session_id
    patient_id_final = session.patient_id

    async def event_stream():
        full_reply = ""
        diagnosis_data = None
        indicator_data = None

        async for chunk in chat_with_ai_stream(
            context=context_msg,
            conversation=conversation,
            file_images=context["file_images"],
        ):
            if chunk["type"] == "content":
                full_reply += chunk["text"]
                yield f"data: {json.dumps({'type': 'content', 'text': chunk['text']}, ensure_ascii=False)}\n\n"
            elif chunk["type"] == "tool_call":
                msg = chunk["message"]
                if msg.get("message", {}).get("tool_calls"):
                    for tc in msg["message"]["tool_calls"]:
                        if tc["function"]["name"] == "provide_diagnosis":
                            try:
                                diagnosis_data = json.loads(tc["function"]["arguments"])
                            except json.JSONDecodeError:
                                pass
                        elif tc["function"]["name"] == "update_clinical_indicators":
                            try:
                                indicator_data = json.loads(tc["function"]["arguments"])
                                yield f"data: {json.dumps({'type': 'extracted_indicators', 'indicators': indicator_data}, ensure_ascii=False)}\n\n"
                            except json.JSONDecodeError:
                                pass

        db2 = SessionLocal()
        try:
            ai_msg = ChatMessage(
                session_id=session_id_final,
                role="assistant",
                content=full_reply or "تم التحليل.",
            )
            db2.add(ai_msg)

            if diagnosis_data:
                sess = db2.query(ChatSession).filter(ChatSession.id == session_id_final).first()
                if sess:
                    sess.diagnosis_result = diagnosis_data
                    sess.status = "completed"
            db2.commit()
        finally:
            db2.close()

        yield f"data: {json.dumps({'type': 'done', 'diagnosis': diagnosis_data, 'indicators': indicator_data}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/sessions/{session_id}/diagnosis")
def get_diagnosis(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.nurse, UserRole.admin)),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.id,
        "status": session.status,
        "diagnosis": session.diagnosis_result,
    }


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()


from app.db.session import SessionLocal
from pydantic import BaseModel

class ExtractIndicatorsRequest(BaseModel):
    file_ids: List[int]

@router.post("/patients/{patient_id}/extract-file-indicators")
async def extract_file_indicators(
    patient_id: int,
    payload: ExtractIndicatorsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.doctor, UserRole.admin)),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    files = (
        db.query(MedicalFile)
        .filter(MedicalFile.patient_id == patient_id, MedicalFile.id.in_(payload.file_ids))
        .all()
    )

    if not files:
        return {}

    text_content_parts = []
    for f in files:
        category_map = {
            "lab": "تحاليل مخبرية",
            "imaging": "صور طبية/أشعة",
            "report": "تقرير طبي",
            "other": "أخرى",
        }
        category_name = category_map.get(f.category, f.category)
        text_content_parts.append(f"--- ملف #{f.id}: {f.file_name} ({category_name}) ---")
        if f.extracted_text:
            text_content_parts.append(f.extracted_text)
        else:
            text_content_parts.append("(لا يوجد نص مستخرج)")

    text_content = "\n\n".join(text_content_parts)

    from app.services.storage import storage_service
    from app.services.file_processor import file_processor
    file_images = []
    for f in files:
        if f.file_type != "image":
            continue
        data = storage_service.download_file(f.storage_key)
        if data is None:
            continue
        prepared = file_processor.prepare_image_for_vision(data)
        if prepared:
            file_images.append({
                "data": file_processor.encode_image_for_vision(prepared),
                "mime_type": "image/png",
                "file_name": f.file_name,
            })

    from app.services.openai_service import extract_indicators_from_text_and_images
    extracted = await extract_indicators_from_text_and_images(text_content, file_images)
    return extracted
