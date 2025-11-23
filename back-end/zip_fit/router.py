from fastapi import APIRouter, HTTPException
from models import ChatRequest, ChatResponse
from chatting import chat_service
import traceback

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG 챗봇 메인 엔드포인트
    - query: 사용자 질문
    - history: 이전 대화 내역 (선택)
    """
    try:
        result = await chat_service(request.query, request.history)
        
        # 응답 반환 (models.py의 ChatResponse 구조에 맞춤)
        return ChatResponse(
            query=request.query,
            answer=result.get('answer', "응답을 생성할 수 없습니다."),
            sources=result.get('sources', []),
            metadata=result.get('metadata')
        )
        
    except Exception as e:
        # 에러 발생 시 로그 출력 및 500 에러 반환
        print("====== [Server Error Log] ======")
        traceback.print_exc()
        print("================================")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")