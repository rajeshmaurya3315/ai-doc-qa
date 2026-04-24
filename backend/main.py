from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm

from models import ChatRequest, SummarizeRequest
from controller import (
    handle_upload,
    handle_chat,
    handle_summarize,
    handle_list_documents,
    handle_delete_document,
    handle_get_timestamps,
)
from auth import handle_login, get_current_user, User

app = FastAPI(title="Veda - AI Document & Multimedia Q&A")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth Routes (no protection needed) ──────────────────────────────────────

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await handle_login(form_data)


@app.get("/auth/me")
async def me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username}


# ─── Public Routes ────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "running", "message": "Veda AI API is live"}


# ─── Protected Routes (require JWT token) ─────────────────────────────────────

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    return await handle_upload(file)


@app.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    return await handle_chat(request)


@app.post("/summarize")
async def summarize(
    request: SummarizeRequest,
    current_user: User = Depends(get_current_user)
):
    return await handle_summarize(request)


@app.get("/documents")
def list_documents(current_user: User = Depends(get_current_user)):
    return handle_list_documents()


@app.delete("/documents/{filename}")
def delete_document(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    return handle_delete_document(filename)


@app.get("/timestamps/{filename}")
def get_timestamps(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    return handle_get_timestamps(filename)
