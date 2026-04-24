import os
import shutil
import pdfplumber
from fastapi import UploadFile, HTTPException

from config import client, MODEL_NAME, ALLOWED_EXTENSIONS, UPLOAD_DIR
from models import ChatRequest, SummarizeRequest
from database import (
    save_document,
    get_document,
    get_document_text,
    get_all_documents,
    delete_document as db_delete_document,
    save_timestamps,
    get_timestamps as db_get_timestamps,
    save_chat_message,
)


def transcribe_file(file_path: str, filename: str, ext: str):
    """Transcribe audio/video file using Groq Whisper."""
    # For mp4, pass as mp4 video — Groq supports it
    # For audio files, pass with correct audio mime type
    mime_map = {
        ".mp3": ("audio.mp3", "audio/mpeg"),
        ".wav": ("audio.wav", "audio/wav"),
        ".m4a": ("audio.m4a", "audio/mp4"),
        ".mp4": ("video.mp4", "video/mp4"),
    }
    fname, mime = mime_map.get(ext, ("audio.mp3", "audio/mpeg"))

    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(fname, f, mime),
            response_format="verbose_json",
        )

    segments = []
    if hasattr(transcription, "segments") and transcription.segments:
        for seg in transcription.segments:
            # Handle both object attributes and dict keys
            if isinstance(seg, dict):
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                text = seg.get("text", "").strip()
            else:
                start = getattr(seg, "start", 0)
                end = getattr(seg, "end", 0)
                text = getattr(seg, "text", "").strip()
            if text:
                segments.append({"start": round(start, 2), "end": round(end, 2), "text": text})

    extracted_text = " ".join(seg["text"] for seg in segments)
    return extracted_text, segments


async def handle_upload(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {ALLOWED_EXTENSIONS}"
        )

    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    extracted_text = ""
    file_type = ""
    has_timestamps = False
    segments = []

    if ext == ".pdf":
        file_type = "pdf"
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

    elif ext in [".mp3", ".wav", ".m4a"]:
        file_type = "audio"
        try:
            extracted_text, segments = transcribe_file(file_path, file.filename, ext)
            has_timestamps = len(segments) > 0
        except Exception as e:
            extracted_text = f"Transcription failed: {str(e)}"
            has_timestamps = False

    elif ext == ".mp4":
        file_type = "video"
        try:
            extracted_text, segments = transcribe_file(file_path, file.filename, ext)
            has_timestamps = len(segments) > 0
        except Exception as e:
            extracted_text = f"Transcription failed: {str(e)}"
            has_timestamps = False

    save_document(
        filename=file.filename,
        file_type=file_type,
        extracted_text=extracted_text,
        file_size=file_size,
        has_timestamps=has_timestamps,
    )

    if segments:
        save_timestamps(file.filename, segments)

    return {
        "filename": file.filename,
        "file_type": file_type,
        "message": "File uploaded successfully",
        "has_timestamps": has_timestamps,
        "extracted_text_preview": extracted_text[:500],
    }


async def handle_chat(request: ChatRequest):
    doc_text = get_document_text(request.filename)

    if not doc_text:
        raise HTTPException(
            status_code=404,
            detail="Document not found. Please upload the file first."
        )

    save_chat_message(request.filename, "user", request.question)

    # Add timestamp context for audio/video
    timestamps = db_get_timestamps(request.filename)
    timestamp_context = ""
    if timestamps:
        segments_text = "\n".join(
            [f"[{seg['start']}s - {seg['end']}s]: {seg['text']}" for seg in timestamps[:60]]
        )
        timestamp_context = f"\n\nTimestamped segments:\n{segments_text}"

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Veda, a helpful AI assistant that answers questions "
                    "strictly based on the document provided. "
                    "If the answer is not in the document, say so clearly.\n\n"
                    f"Document:\n{doc_text[:4000]}"
                    f"{timestamp_context}"
                ),
            },
            {"role": "user", "content": request.question},
        ],
        temperature=0.3,
        max_tokens=1000,
    )

    answer = response.choices[0].message.content
    save_chat_message(request.filename, "assistant", answer)

    # Find relevant timestamp
    relevant_timestamp = None
    if timestamps:
        question_words = set(w for w in request.question.lower().split() if len(w) > 3)
        for seg in timestamps:
            seg_words = set(seg["text"].lower().split())
            if question_words & seg_words:
                relevant_timestamp = seg
                break

    result = {
        "filename": request.filename,
        "question": request.question,
        "answer": answer,
    }
    if relevant_timestamp:
        result["timestamp"] = relevant_timestamp

    return result


async def handle_summarize(request: SummarizeRequest):
    doc_text = get_document_text(request.filename)

    if not doc_text:
        raise HTTPException(
            status_code=404,
            detail="Document not found. Please upload the file first."
        )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are Veda, an intelligent AI assistant. "
                    "Summarize the following document in 5 clear bullet points. "
                    "Be concise and cover the most important points:\n\n"
                    f"{doc_text[:4000]}"
                ),
            }
        ],
        temperature=0.3,
        max_tokens=800,
    )

    return {
        "filename": request.filename,
        "summary": response.choices[0].message.content,
    }


def handle_list_documents():
    docs = get_all_documents()
    return {
        "documents": [
            {
                "filename": doc["filename"],
                "file_type": doc["file_type"],
                "has_timestamps": bool(doc["has_timestamps"]),
                "created_at": doc["created_at"],
            }
            for doc in docs
        ],
        "count": len(docs),
    }


def handle_delete_document(filename: str):
    doc = get_document(filename)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db_delete_document(filename)

    file_path = f"{UPLOAD_DIR}/{filename}"
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"message": f"{filename} deleted successfully"}


def handle_get_timestamps(filename: str):
    doc = get_document(filename)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    timestamps = db_get_timestamps(filename)
    return {"filename": filename, "timestamps": timestamps}
