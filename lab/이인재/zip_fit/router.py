from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from models import ChatRequest, ChatResponse
from dependencies import get_rag_engine
from rag import RAGEngine

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chatting"]
)
# ====================================================

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    # 의존성 주입
    rag_engine: RAGEngine = Depends(get_rag_engine)
):
    """
    RAG 챗봇 메인 엔드포인트
    """
    try:
        # RAG 엔진 호출
        result = await rag_engine.query(
            user_id=request.user_id,
            question=request.user_input,
            top_k=3,
            use_hybrid=request.use_hybrid,
            use_llm=request.use_llm
        )
        
        # 결과 반환
        return ChatResponse(
            answer=result.get('answer'),
            context=result.get('context', ""),
            results=result.get('results', []),
            metadata=result.get('metadata', {})
        )
        
    except Exception as e:
        print(f"Error in chat_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))