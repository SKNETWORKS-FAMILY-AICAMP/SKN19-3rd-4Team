from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# 1. 사용자 요청 모델
class ChatRequest(BaseModel):
    user_input: str = Field(..., description="사용자의 질문")
    user_id: int = Field(default=0, description="사용자 ID (로그 등 추적용)")
    # RAG 엔진 옵션 추가
    use_hybrid: bool = Field(default=True, description="하이브리드 검색(키워드+벡터) 사용 여부")
    use_llm: bool = Field(default=True, description="LLM 답변 생성 여부 (False면 검색 결과만 반환)")

# 2. 서버 응답 모델
class ChatResponse(BaseModel):
    answer: Optional[str] = Field(None, description="LLM이 생성한 답변")
    context: str = Field("", description="LLM에게 제공된 근거 문서(Context) 전문")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="검색 통계 (문서 수, 유사도 등)")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="상세 검색 결과 리스트")