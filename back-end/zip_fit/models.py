from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="사용자 식별 ID (예: 'user123')")
    query: str = Field(..., description="사용자 질문")

class ResetRequest(BaseModel):
    user_id: str

class SourceInfo(BaseModel):
    announcement_id: str
    announcement_title: str
    announcement_date: Optional[str] = None
    region: str
    notice_type: str
    category: str
    rerank_score: float
    num_chunks: int

class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceInfo]
    metadata: Optional[Dict[str, Any]] = None