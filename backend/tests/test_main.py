import pytest
import os
import sys
import io
import sqlite3
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import save_document, delete_document, init_db

client = TestClient(app)

# ─── Auth helper ──────────────────────────────────────────────────────────────

def get_token():
    """Get JWT token for testing"""
    form = {"username": "admin", "password": "secret"}
    response = client.post("/auth/login", data=form)
    return response.json()["access_token"]

def auth_headers():
    return {"Authorization": f"Bearer {get_token()}"}

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test"""
    init_db()
    conn = sqlite3.connect("veda.db")
    conn.execute("DELETE FROM chat_history")
    conn.execute("DELETE FROM timestamps")
    conn.execute("DELETE FROM documents")
    conn.commit()
    conn.close()
    yield
    # Cleanup after test
    conn = sqlite3.connect("veda.db")
    conn.execute("DELETE FROM chat_history")
    conn.execute("DELETE FROM timestamps")
    conn.execute("DELETE FROM documents")
    conn.commit()
    conn.close()


# ─── GET / ────────────────────────────────────────────────────────────────────

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


# ─── Auth ─────────────────────────────────────────────────────────────────────

def test_login_success():
    response = client.post("/auth/login", data={"username": "admin", "password": "secret"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password():
    response = client.post("/auth/login", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_login_wrong_username():
    response = client.post("/auth/login", data={"username": "nobody", "password": "secret"})
    assert response.status_code == 401


def test_me_endpoint():
    response = client.get("/auth/me", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_protected_route_without_token():
    response = client.get("/documents")
    assert response.status_code == 401


# ─── POST /upload ─────────────────────────────────────────────────────────────

def test_upload_pdf():
    with patch("controller.pdfplumber.open") as mock_pdf:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "This is test document content."
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

        pdf_bytes = io.BytesIO(b"%PDF-1.4 fake pdf content")
        response = client.post(
            "/upload",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
            headers=auth_headers()
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["file_type"] == "pdf"
    assert data["message"] == "File uploaded successfully"


def test_upload_audio():
    audio_bytes = io.BytesIO(b"fake audio content")
    with patch("controller.client.audio.transcriptions.create") as mock_transcribe:
        mock_seg = MagicMock()
        mock_seg.start = 0.0
        mock_seg.end = 2.0
        mock_seg.text = "Hello world"
        mock_transcribe.return_value.segments = [mock_seg]

        response = client.post(
            "/upload",
            files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
            headers=auth_headers()
        )

    assert response.status_code == 200
    assert response.json()["file_type"] in ["audio/video", "audio"]
    


def test_upload_video():
    video_bytes = io.BytesIO(b"fake video content")
    with patch("controller.client.audio.transcriptions.create") as mock_transcribe:
        mock_transcribe.return_value.segments = []
        response = client.post(
            "/upload",
            files={"file": ("video.mp4", video_bytes, "video/mp4")},
            headers=auth_headers()
        )

    assert response.status_code == 200
    assert response.json()["file_type"] in ["audio/video", "video"]


def test_upload_unsupported_file():
    txt_bytes = io.BytesIO(b"some text")
    response = client.post(
        "/upload",
        files={"file": ("file.txt", txt_bytes, "text/plain")},
        headers=auth_headers()
    )
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_upload_stores_in_database():
    with patch("controller.pdfplumber.open") as mock_pdf:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Stored content here."
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

        pdf_bytes = io.BytesIO(b"%PDF-1.4 fake pdf content")
        client.post(
            "/upload",
            files={"file": ("stored.pdf", pdf_bytes, "application/pdf")},
            headers=auth_headers()
        )

    # Verify it's in the database
    from database import get_document
    doc = get_document("stored.pdf")
    assert doc is not None
    assert "Stored content here." in doc["extracted_text"]


# ─── POST /chat ───────────────────────────────────────────────────────────────

def test_chat_success():
    save_document("test.pdf", "pdf", "The sky is blue. Water is wet.")

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "The sky is blue."

    with patch("controller.client.chat.completions.create", return_value=mock_response):
        response = client.post(
            "/chat",
            json={"filename": "test.pdf", "question": "What color is the sky?"},
            headers=auth_headers()
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "The sky is blue."


def test_chat_no_document():
    response = client.post(
        "/chat",
        json={"filename": "nonexistent.pdf", "question": "What is this?"},
        headers=auth_headers()
    )
    assert response.status_code == 404


def test_chat_returns_filename_and_question():
    save_document("doc.pdf", "pdf", "Some content.")

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Some answer."

    with patch("controller.client.chat.completions.create", return_value=mock_response):
        response = client.post(
            "/chat",
            json={"filename": "doc.pdf", "question": "Tell me something"},
            headers=auth_headers()
        )

    data = response.json()
    assert data["filename"] == "doc.pdf"
    assert data["question"] == "Tell me something"


def test_chat_saves_to_history():
    save_document("history.pdf", "pdf", "Some content about history.")

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Answer here."

    with patch("controller.client.chat.completions.create", return_value=mock_response):
        client.post(
            "/chat",
            json={"filename": "history.pdf", "question": "What is this?"},
            headers=auth_headers()
        )

    from database import get_chat_history
    history = get_chat_history("history.pdf")
    assert len(history) == 2  # user + assistant
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


# ─── POST /summarize ──────────────────────────────────────────────────────────

def test_summarize_success():
    save_document("report.pdf", "pdf", "Long document content about AI and ML.")

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "• AI is transforming industries"

    with patch("controller.client.chat.completions.create", return_value=mock_response):
        response = client.post(
            "/summarize",
            json={"filename": "report.pdf"},
            headers=auth_headers()
        )

    assert response.status_code == 200
    assert "AI" in response.json()["summary"]


def test_summarize_no_document():
    response = client.post(
        "/summarize",
        json={"filename": "missing.pdf"},
        headers=auth_headers()
    )
    assert response.status_code == 404


def test_summarize_returns_filename():
    save_document("summary_test.pdf", "pdf", "Content to summarize.")

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Summary here."

    with patch("controller.client.chat.completions.create", return_value=mock_response):
        response = client.post(
            "/summarize",
            json={"filename": "summary_test.pdf"},
            headers=auth_headers()
        )

    assert response.json()["filename"] == "summary_test.pdf"


# ─── GET /documents ───────────────────────────────────────────────────────────

def test_list_documents_empty():
    response = client.get("/documents", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["documents"] == []


def test_list_documents_with_files():
    save_document("file1.pdf", "pdf", "Content 1")
    save_document("file2.pdf", "pdf", "Content 2")

    response = client.get("/documents", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["count"] == 2
    filenames = [d["filename"] for d in response.json()["documents"]]
    assert "file1.pdf" in filenames
    assert "file2.pdf" in filenames


# ─── DELETE /documents/{filename} ────────────────────────────────────────────

def test_delete_document_success():
    save_document("delete_me.pdf", "pdf", "Some content")

    response = client.delete("/documents/delete_me.pdf", headers=auth_headers())
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    from database import get_document
    assert get_document("delete_me.pdf") is None


def test_delete_document_not_found():
    response = client.delete("/documents/nonexistent.pdf", headers=auth_headers())
    assert response.status_code == 404


# ─── GET /timestamps/{filename} ───────────────────────────────────────────────

def test_get_timestamps_success():
    save_document("audio.mp3", "audio/video", "Hello world", has_timestamps=True)
    from database import save_timestamps
    save_timestamps("audio.mp3", [
        {"start": 0.0, "end": 2.0, "text": "Hello"},
        {"start": 2.0, "end": 4.0, "text": "World"},
    ])

    response = client.get("/timestamps/audio.mp3", headers=auth_headers())
    assert response.status_code == 200
    assert len(response.json()["timestamps"]) == 2


def test_get_timestamps_not_found():
    response = client.get("/timestamps/nonexistent.mp3", headers=auth_headers())
    assert response.status_code == 404