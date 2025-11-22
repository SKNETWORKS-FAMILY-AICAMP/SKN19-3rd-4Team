from typing import Optional
from rag import RAGEngine

# 전역 변수로 엔진 인스턴스 저장 (싱글톤 패턴)
_RAG_ENGINE: Optional[RAGEngine] = None

def set_rag_engine(instance: RAGEngine):
    """
    서버 시작 시(main.py lifespan), 초기화된 RAGEngine을 저장합니다.
    """
    global _RAG_ENGINE
    _RAG_ENGINE = instance
    print("Dependencies: RAGEngine 의존성 주입 준비 완료")

def get_rag_engine() -> RAGEngine:
    """
    Router에서 Depends()를 통해 호출할 함수입니다.
    초기화된 RAGEngine 인스턴스를 반환합니다.
    """
    if _RAG_ENGINE is None:
        raise RuntimeError("RAGEngine이 초기화되지 않았습니다. main.py 설정을 확인하세요.")
    return _RAG_ENGINE