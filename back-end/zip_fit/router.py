from fastapi import APIRouter, HTTPException
from typing import Dict, List
from models import ChatRequest, ChatResponse, ResetRequest
from chatting import chat_service
import traceback

router = APIRouter()

# 구조: { "user1": [대화내역], "user2": [대화내역] }
user_sessions: Dict[str, List[Dict]] = {}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG 챗봇 메인 엔드포인트
    - user_id: 사용자 식별자
    - query: 사용자 질문
    """
    try:
        user_id = request.user_id
        
        # 1. 해당 유저의 세션이 없으면 빈 리스트 생성
        if user_id not in user_sessions:
            user_sessions[user_id] = []
        
        # 2. 유저별 히스토리 가져오기
        current_history = user_sessions[user_id]
        
        # 3. 서비스 호출
        result = await chat_service(request.query, current_history)
        
        # 4. 결과 저장 (해당 유저의 히스토리에 append)
        user_sessions[user_id].append({
            'query': request.query,
            'answer': result.get('answer'),
            'sources': result.get('sources', [])
        })
        
        return ChatResponse(
            query=request.query,
            answer=result.get('answer', "응답을 생성할 수 없습니다."),
            sources=result.get('sources', []),
            metadata=result.get('metadata')
        )
        
    except Exception as e:
        print("====== [Server Error Log] ======")
        traceback.print_exc()
        print("================================")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 세션 초기화 엔드포인트
@router.post("/session/reset")
async def reset_session(request: ResetRequest):
    global user_sessions
    user_id = request.user_id
    
    if user_id in user_sessions:
        user_sessions[user_id] = [] # 해당 유저만 초기화
        msg = f"User '{user_id}'의 대화 내역이 초기화되었습니다."
    else:
        msg = f"User '{user_id}'의 세션을 찾을 수 없습니다."
        
    print(f"[System] {msg}")
    return {"status": "success", "message": msg}