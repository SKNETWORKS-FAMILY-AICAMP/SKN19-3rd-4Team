from fastapi import APIRouter, HTTPException, Path
from models import ChatRequest, ChatResponse, SessionInitResponse, SessionChatRequest
from chatting import chat_service
from sessions import session_store
import traceback

router = APIRouter()

# Stateless API
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        result = await chat_service(request.query, request.history)
        return ChatResponse(
            query=request.query,
            answer=result.get('answer', "Error"),
            sources=result.get('sources', []),
            metadata=result.get('metadata')
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# 세션 생성
@router.post("/sessions", response_model=SessionInitResponse)
async def create_session():
    session_id = session_store.create_session()
    return SessionInitResponse(
        session_id=session_id, 
        message="새로운 대화 세션이 생성되었습니다."
    )

# 세션 대화 (일반 응답)
@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def session_chat_endpoint(
    query_req: SessionChatRequest,
    session_id: str = Path(..., description="세션 ID")
):
    try:
        # 히스토리 로드
        history = session_store.get_history(session_id)
        
        # 답변 생성
        result = await chat_service(query_req.query, history)
        
        # 히스토리 저장
        session_store.add_message(
            session_id, 
            query_req.query, 
            result.get('answer', ""), 
            result.get('sources', [])
        )
        
        return ChatResponse(
            query=query_req.query,
            answer=result.get('answer', "응답 생성 실패"),
            sources=result.get('sources', []),
            metadata=result.get('metadata')
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))