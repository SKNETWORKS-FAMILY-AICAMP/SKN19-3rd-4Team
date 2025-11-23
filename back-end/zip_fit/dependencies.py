import os
from typing import Optional, Dict
from sentence_transformers import SentenceTransformer, CrossEncoder
from openai import OpenAI
import config


# 전역 변수 (Global Variables for Lazy Loading)
_embedding_model: Optional[SentenceTransformer] = None
_reranker_model: Optional[CrossEncoder] = None
_openai_client: Optional[OpenAI] = None

def get_openai_client() -> OpenAI:
    """
    OpenAI 클라이언트 싱글톤 반환
    """
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _openai_client

def load_models():
    """
    앱 시작 시(Lifespan) 호출되어 AI 모델을 메모리에 적재합니다.
    - 모델 파일은 config.MODEL_CACHE_DIR 경로에 저장/로드됩니다.
    - Reranker는 config.USE_RERANKER 스위치가 True일 때만 로드됩니다.
    """
    global _embedding_model, _reranker_model
    
    print(f"\n[System] 모델 저장 경로(Cache Dir): {os.path.abspath(config.MODEL_CACHE_DIR)}")
    
    # 임베딩 모델 로드
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

    # Reranker 모델 로드 (선택 - 스위치 확인)
    if config.USE_RERANKER:
        if _reranker_model is None:
            print(f"[System] Reranker 모델 로딩 중... ({config.RERANKER_MODEL_NAME})")
            try:
                # CrossEncoder는 내부적으로 HuggingFace Transformers를 사용하므로
                # automodel_args를 통해 cache_dir를 전달
                _reranker_model = CrossEncoder(
                    config.RERANKER_MODEL_NAME, 
                    device='cpu',
                    automodel_args={"cache_dir": config.MODEL_CACHE_DIR} 
                )
                print("[System] Reranker 모델 로딩 완료")
            except Exception as e:
                print(f"[System] Reranker 모델 로딩 실패: {e}")
                # Reranker 실패 시 전체 앱을 죽일지, 아니면 Reranker만 끌지 결정
                # 여기서는 에러 로그만 남기고 None 상태 유지 (기능만 작동 안 함)
                print("[System] Reranker 기능이 비활성화됩니다.")
    else:
        print("[System] Reranker 로딩 건너뜀 (config.USE_RERANKER = False)")

    print("[System] 모든 시스템 준비 완료\n")

def get_embedding_model() -> SentenceTransformer:
    """
    임베딩 모델 인스턴스 반환 (로드 안 됐으면 강제 로드)
    """
    if _embedding_model is None:
        load_models()
    return _embedding_model

def get_reranker() -> Optional[CrossEncoder]:
    """
    Reranker 모델 인스턴스 반환.
    스위치가 꺼져있거나 로드되지 않았으면 None 반환.
    """
    if not config.USE_RERANKER:
        return None
    
    if _reranker_model is None:
        load_models()
        
    return _reranker_model

def get_db_config() -> Dict:
    """
    DB 연결 설정 반환
    """
    return config.DB_CONFIG