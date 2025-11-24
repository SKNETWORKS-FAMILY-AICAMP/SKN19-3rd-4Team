from fastapi import APIRouter, HTTPException
from typing import Dict, List
from models import ChatRequest, ChatResponse, ResetRequest
from chatting import chat_service
import traceback
from info import user_sessions

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG 챗봇 메인 엔드포인트
    - user_id: 사용자 식별자
    - query: 사용자 질문
    """
    try:
        # 빈 입력 검증
        if not request.query or not request.query.strip():
            return ChatResponse(
                query="",
                answer="질문을 입력해주세요.",
                sources=[],
                metadata=None
            )

        user_id = request.user_id
        
        # [Debug] 터미널 로그 출력 (요청 수신 확인)
        print(f"\n[Debug] ▶ 요청 수신! User_ID: {user_id}")
        print(f"[Debug] ▶ 질문 내용: {request.query}")

        # 1. 세션 생성 또는 로드 (info.py의 user_sessions 사용)
        if user_id not in user_sessions:
            print(f"[Debug] ▷ 새로운 유저입니다. 세션을 생성합니다.")
            user_sessions[user_id] = []
        else:
            print(f"[Debug] ▷ 기존 유저입니다. 현재 대화 턴 수: {len(user_sessions[user_id])}개")

        current_history = user_sessions[user_id]

        # 2. 서비스 호출 (RAG 로직 수행)
        result = await chat_service(request.query, current_history)
        
        # 3. 결과 저장 (세션 업데이트)
        new_turn = {
            'query': request.query,
            'answer': result.get('answer'),
            'sources': result.get('sources', [])
        }
        user_sessions[user_id].append(new_turn)
        
        print(f"[Debug] ✅ 저장 완료. 현재 {user_id}의 누적 대화 개수: {len(user_sessions[user_id])}")
        
        # 4. 응답 반환 (프론트엔드 확인용 필드 포함)
        return ChatResponse(
            query=request.query,
            answer=result.get('answer', "응답을 생성할 수 없습니다."),
            sources=result.get('sources', []),
            metadata=result.get('metadata'),
            
            # 프론트엔드에서 전체 흐름을 볼 수 있게 데이터 주입
            session_history=user_sessions[user_id],
            process_info=result.get('query_analysis')
        )
        
    except Exception as e:
        print("====== [Server Error Log] ======")
        traceback.print_exc()
        print("================================")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 세션 초기화 엔드포인트
@router.post("/session/reset")
async def reset_session(request: ResetRequest):
    # info.py의 user_sessions를 직접 조작
    user_id = request.user_id
    
    print(f"\n[Debug] 🔄 세션 초기화 요청: {user_id}")
    
    if user_id in user_sessions:
        user_sessions[user_id] = [] # 해당 유저만 초기화
        msg = f"User '{user_id}'의 대화 내역이 초기화되었습니다."
    else:
        msg = f"User '{user_id}'의 세션을 찾을 수 없습니다."
        
    print(f"[System] {msg}")
    return {"status": "success", "message": msg}