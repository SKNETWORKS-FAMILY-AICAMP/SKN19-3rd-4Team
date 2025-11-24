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
    announcement_url: Optional[str] = None
    announcement_status: Optional[str] = None
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
    
    # 프론트엔드 디버깅용 (세션 누적 기록 확인)
    session_history: Optional[List[Dict[str, Any]]] = Field(None, description="현재 세션의 전체 대화 기록")
    # 내부 처리 정보 확인 (질문 분석 결과 등)
    process_info: Optional[Dict[str, Any]] = Field(None, description="질문 재구성 및 분석 정보")

# info.py에 있던 통계 모델을 여기로 통합
class StatsResponse(BaseModel):
    CNT_ALL: int = Field(..., description="전체 공고 수")
    CNT_NOTE_ING: int = Field(..., description="공고중인 건수")
    CNT_APP_ING: int = Field(..., description="접수중인 건수")
    CNT_ELSE: int = Field(..., description="그 외(마감 등) 건수")