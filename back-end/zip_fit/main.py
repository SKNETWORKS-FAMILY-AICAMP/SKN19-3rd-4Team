import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 1. 라우터 모듈 임포트
# router.py: 채팅 기능 (/chat, /session/reset)
from router import router as chat_router
# info.py: 통계/대시보드 기능 (/stats)
from info import router as info_router

from dependencies import load_models
import config

# 앱 생명주기 관리 (시작과 종료 시점 정의)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # [시작] 앱 구동 시 실행
    print("\n" + "="*40)
    print(f"[System] {config.PROJECT_ROOT} RAG 서버 시작")
    print(f"Reranker 상태: {'ON' if config.USE_RERANKER else 'OFF'}")
    print("="*40 + "\n")
    
    try:
        # AI 모델 로드 (dependencies.py)
        load_models()
    except Exception as e:
        print(f"[Critical] 모델 로딩 중 오류 발생: {e}")
    
    yield  # 앱 실행 중...
    
    # [종료] 앱 종료 시 실행
    print("\n[System] 서버 종료 및 리소스 해제")

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="LH Gonggo RAG Chatbot",
    description="LH 임대/분양 공고 검색을 위한 RAG 챗봇 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 기본 포트
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # React 기본 포트
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
# 1. 채팅 라우터 등록 -> /api/v1/chat, /api/v1/session/reset
app.include_router(chat_router, prefix="/api/v1")

# 2. 통계 라우터 등록 -> /api/v1/stats
app.include_router(info_router, prefix="/api/v1")


# 헬스 체크 엔드포인트
@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "LH RAG Chatbot",
        "config": {
            "use_reranker": config.USE_RERANKER,
            "embedding_model": config.EMBEDDING_MODEL_NAME
        }
    }

if __name__ == "__main__":
    # uvicorn.run 명령어 없이 파이썬 파일 직접 실행 가능
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)