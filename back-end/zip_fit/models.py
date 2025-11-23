from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, Any]] = Field(default_factory=list, description="이전 대화 내역 ({'query':.., 'answer':..})")

class SourceInfo(BaseModel):
    # [수정됨] int -> str (DB에 'LH_lease_64' 같은 문자열 ID가 들어있기 때문)
    announcement_id: str 
    title: str
    region: str
    score: float
    chunk_count: int

class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceInfo]
    metadata: Optional[Dict[str, Any]] = None