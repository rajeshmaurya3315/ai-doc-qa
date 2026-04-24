from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    filename: str
    question: str


class SummarizeRequest(BaseModel):
    filename: str


class TimestampSegment(BaseModel):
    start: float
    end: float
    text: str


class DeleteResponse(BaseModel):
    message: str


class DocumentListResponse(BaseModel):
    documents: list
    count: int
