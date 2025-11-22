from fastapi import FastAPI
from contextlib import asynccontextmanager
import router
from rag import RAGEngine
from dependencies import set_rag_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # [App Startup]
    print("System Startup: Initializing RAG Engine...")
    
    try:
        # 1. RAGEngine 인스턴스 생성
        # 내부적으로 OpenAI Client 연결, SearchEngine(DB 연결) 초기화가 수행됩니다.
        rag_instance = RAGEngine()
        
        # 2. 의존성 주입 (Dependency Injection)
        # 생성된 인스턴스를 전역 변수에 저장하여 router에서 사용할 수 있게 합니다.
        set_rag_engine(rag_instance)
        
        print("✅ RAG Engine Ready: System is fully operational.")
        
    except Exception as e:
        print(f"Critical Error during startup: {e}")
        # 심각한 오류 시 앱 실행을 중단할 수도 있습니다.
        raise e
    
    yield # 애플리케이션 실행 중...
    
    #[App Shutdown]
    print("System Shutdown: Cleaning up resources...")
    # 필요하다면 여기서 DB 연결 종료 등의 정리 작업을 수행합니다.
    # 현재 구조에서는 각 요청마다 DB 연결을 맺고 끊으므로 별도 작업은 필요 없습니다.


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="LH Housing RAG Chatbot",
    version="2.0.0",
    description="LH 임대/분양 공고 정보를 제공하는 RAG 기반 챗봇 API",
    lifespan=lifespan 
)

# 라우터 등록 (API 엔드포인트 연결)
app.include_router(router.router)


@app.get("/", tags=["Root"])
def read_root():
    """서버 상태 확인용 루트 엔드포인트"""
    return {
        "status": "online",
        "message": "LH Housing RAG Service is running.",
        "docs_url": "/docs" # Swagger UI 경로 안내
    }

# 실행 방법 안내 (주석)
# 터미널에서 다음 명령어로 실행하세요:
# uvicorn main:app --reload