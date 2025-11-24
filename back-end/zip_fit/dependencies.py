import os
from typing import Optional, Dict
from sentence_transformers import SentenceTransformer, CrossEncoder
from openai import AsyncOpenAI  # [중요] AsyncOpenAI 사용
import config

# ==========================================
# 전역 변수
# ==========================================
_embedding_model: Optional[SentenceTransformer] = None
_reranker_model: Optional[CrossEncoder] = None
_openai_client: Optional[AsyncOpenAI] = None  # [중요] 타입 힌트 변경

def get_openai_client() -> AsyncOpenAI:
    """
    OpenAI 비동기 클라이언트 싱글톤 반환
    """
    global _openai_client
    if _openai_client is None:
        # [중요] AsyncOpenAI 인스턴스 생성
        _openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    return _openai_client

def load_models():
    """
    앱 시작 시 AI 모델을 메모리에 적재합니다.
    """
    global _embedding_model, _reranker_model
    
    print(f"\n[System] 모델 저장 경로(Cache Dir): {os.path.abspath(config.MODEL_CACHE_DIR)}")
    os.environ['HF_HOME'] = os.path.abspath(config.MODEL_CACHE_DIR)
    
    # 1. 임베딩 모델 로드
    if _embedding_model is None:
        print(f"[System] 임베딩 모델 로딩 중... ({config.EMBEDDING_MODEL_NAME})")
        try:
            _embedding_model = SentenceTransformer(
                config.EMBEDDING_MODEL_NAME, 
                cache_folder=config.MODEL_CACHE_DIR
            )
            print("[System] 임베딩 모델 로딩 완료")
        except Exception as e:
            print(f"[System] 임베딩 모델 로딩 실패: {e}")
            raise e

    # 2. Reranker 모델 로드
    if config.USE_RERANKER:
        if _reranker_model is None:
            print(f"[System] Reranker 모델 로딩 중... ({config.RERANKER_MODEL_NAME})")
            try:
                _reranker_model = CrossEncoder(
                    config.RERANKER_MODEL_NAME, 
                    device='cpu'
                )
                print("[System] Reranker 모델 로딩 완료")
            except Exception as e:
                print(f"[System] Reranker 모델 로딩 실패: {e}")
                print("[System] Reranker 기능이 비활성화됩니다.")
    else:
        print("[System] Reranker 로딩 건너뜀 (config.USE_RERANKER = False)")

    print("[System] 모든 시스템 준비 완료\n")

def get_embedding_model() -> SentenceTransformer:
    if _embedding_model is None: load_models()
    return _embedding_model

def get_reranker() -> Optional[CrossEncoder]:
    if not config.USE_RERANKER: return None
    if _reranker_model is None: load_models()
    return _reranker_model

def get_db_config() -> Dict:
    return config.DB_CONFIG