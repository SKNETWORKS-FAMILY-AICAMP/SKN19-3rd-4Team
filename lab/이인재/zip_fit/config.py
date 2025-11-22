import os
from pathlib import Path
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

# 2. 경로 설정
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent
PDF_BASE_PATH = PROJECT_ROOT

# 3. DB & API 설정 (기본값 제거, .env 필수)
HOST = os.getenv('HOST')
PORT = int(os.getenv('PORT'))
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
DATABASE = os.getenv('DATABASE')

# API 키
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOV_API_KEY = os.getenv('GOV_API_KEY')

# (호환성용) DB 연결 딕셔너리
DB_CONFIG = {
    'host': HOST,
    'port': PORT,
    'user': USER,
    'password': PASSWORD,
    'database': DATABASE
}


# 4. RAG 챗봇 어플리케이션 설정
# 임베딩 모델
EMBEDDING_MODEL = 'BAAI/bge-m3'
EMBEDDING_DIMENSION = 1024

# 청킹 설정
MIN_CHUNK_SIZE = 100
OPTIMAL_CHUNK_SIZE = 600
MAX_CHUNK_SIZE = 1200
MAX_TABLE_SIZE = 3000
CHUNK_OVERLAP = 150

# 검색 설정
DEFAULT_TOP_K = 5
SIMILARITY_THRESHOLD = 0.6

# OpenAI 모델 설정
OPENAI_MODEL = 'gpt-4o-mini'
OPENAI_TEMPERATURE = 0.3
OPENAI_MAX_TOKENS = 1500

# 처리 설정
BATCH_SIZE = 10
MAX_WORKERS = 4