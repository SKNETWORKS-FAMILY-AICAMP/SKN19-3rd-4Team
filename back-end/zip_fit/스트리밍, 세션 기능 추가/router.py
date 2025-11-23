from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import StreamingResponse
from models import ChatRequest, ChatResponse, SessionInitResponse, SessionChatRequest
from chatting import chat_service
from sessions import session_store
import traceback
import json

router = APIRouter()


# 1. [기존] Stateless API (유지)
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


# 세션 생성
@router.post("/sessions", response_model=SessionInitResponse)
async def create_session():
    """
    새로운 대화 세션을 생성하고 session_id를 발급합니다.
    """
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
    """
    세션 ID를 기반으로 대화합니다. (history를 서버가 관리)
    """
    try:
        # 서버 메모리에서 과거 대화 내역 가져오기
        history = session_store.get_history(session_id)
        
        # 챗봇 서비스 호출
        result = await chat_service(query_req.query, history)
        
        # 결과(질문/답변)를 다시 메모리에 저장
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
        print(f"[Session Error] {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Session Error: {str(e)}")

# 세션 대화 (스트리밍 응답)
@router.post("/sessions/{session_id}/stream")
async def stream_chat_endpoint(
    query_req: SessionChatRequest,
    session_id: str = Path(..., description="세션 ID")
):
    """
    Server-Sent Events(SSE) 방식으로 실시간 답변을 스트리밍합니다.
    """
    async def generator():
        # 히스토리 가져오기
        history = session_store.get_history(session_id)
        
        # 데이터 수집용 변수 (세션 저장용)
        accumulated_answer = []
        final_sources = []
        
        # 스트리밍 서비스 호출
        # circular import 방지를 위해 함수 내부에서 import
        from chatting import chat_stream_service
        
        try:
            async for event_str in chat_stream_service(query_req.query, history):
                # 클라이언트로 즉시 전송
                yield event_str
                
                # 세션 저장을 위한 데이터 파싱 및 수집
                try:
                    event = json.loads(event_str)
                    if event['type'] == 'answer':
                        accumulated_answer.append(event['content'])
                    elif event['type'] == 'sources':
                        final_sources = event['data']
                except:
                    pass
            
            # 스트리밍 완료 후 세션 저장
            full_text = "".join(accumulated_answer)
            if full_text:
                session_store.add_message(
                    session_id,
                    query_req.query,
                    full_text,
                    final_sources
                )
        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    # application/x-ndjson: Newline Delimited JSON (한 줄에 하나의 JSON)
    return StreamingResponse(generator(), media_type="application/x-ndjson")