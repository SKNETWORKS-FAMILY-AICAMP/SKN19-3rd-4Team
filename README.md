# ZIPFIT (집핏) - 나에게 딱 맞는 집

**SK네트웍스 Family AI 캠프 19기 3차 프로젝트**

---

## 1. 팀 소개

**팀명**: A.J.C

**팀원**:
- 김범섭 ([@WhatSupYap](https://github.com/WhatSupYap))
- 김종민 ([@jongminkim-KR1](https://github.com/jongminkim-KR1))
- 이상혁 ([@sangpiri](https://github.com/sangpiri))
- 이인재 ([@distecter](https://github.com/distecter))
- 오흥재 ([@vfxpedia](https://github.com/vfxpedia))

---

## 2. 프로젝트 개요

### 프로젝트 명
ZIPFIT (집핏) - 나에게 딱 맞는 집

### 프로젝트 소개
ZIPFIT은 LH(한국토지주택공사), SH(서울주택도시공사), GH(경기주택도시공사) 등 공공주택 공고를 통합하여, LLM과 RAG 기술을 활용해 사용자 맞춤형 주거 정보를 제공하는 AI 에이전트 서비스입니다.

복잡하고 이해하기 어려운 공공주택 공고문을 분석하여, 사용자의 조건에 맞는 공고를 추천하고, 공고 정보를 쉽게 이해할 수 있도록 안내합니다.

**현재 프로토타입 범위**:
- **데이터 범위**: LH 공고 중 서울/경기 지역 공고만 대상
- **핵심 서비스 흐름**: AI 상담 → 공고 비교/추천 → 신청 안내
- **제외된 기능** (향후 확장 예정): 자격 진단, 계약 지원, 대출 정보 제공

**최종 목표 서비스 흐름**: AI 상담 → 자격 진단 → 공고 비교/추천 → 신청 안내 → 계약 지원 → 대출 정보 제공

### 프로젝트 필요성 (배경)

공공주택(LH, SH, GH)은 청년, 신혼부부, 저소득층 등 주거 취약계층에게 매우 중요한 주거 안정 수단입니다. 그러나 현재 공공주택 공고는 다음과 같은 문제점이 있습니다:

1. **복잡한 공고 구조**: 각 기관(LH, SH, GH)마다 공고 형식과 용어가 달라, 통합적으로 비교하기 어렵습니다.

2. **전문 용어의 범람**: "선계약후검증", "묵시적갱신", "계약보증금" 등 일반인이 이해하기 어려운 전문 용어가 많습니다.

3. **산재된 정보**: 자격 요건, 신청 방법, 대출 정보 등이 각각 다른 문서와 웹사이트에 흩어져 있어 정보 수집에 많은 시간이 소요됩니다.

4. **자격 판단의 어려움**: 본인이 해당 공고에 신청할 자격이 되는지 판단하기 위해서는 복잡한 소득 기준, 거주 요건 등을 일일이 확인해야 합니다.

이러한 문제로 인해 많은 국민들이 자신에게 적합한 공공주택 기회를 놓치거나, 부적격 신청으로 시간을 낭비하는 경우가 발생하고 있습니다.

### 프로젝트 목표

1. **LLM 기반 비정형 문서 이해**: 공공주택 공고문의 맥락을 이해하고, 사용자의 질문에 맞춰 필요한 정보를 추출하여 쉽게 설명합니다.

2. **사용자 맞춤형 정보 제공**: 사용자의 나이, 소득, 가족 구성 등을 고려하여 맞춤형 공고를 추천하고, 자격 요건을 자동으로 확인합니다.

3. **원스톱 서비스 제공**: 공고 검색부터 신청, 계약, 대출까지 여러 단계를 하나의 대화 창에서 처리할 수 있도록 지원합니다.

4. **사회적 가치 실현**: 모든 국민이 공평하게 공공주택 정보에 접근하고, 자신에게 맞는 주거 기회를 찾을 수 있도록 지원함으로써 주거 불평등 해소에 기여합니다.

---

## 3. 기술 스택 & 사용한 모델

| 구분 | 기술/도구 | 버전/모델명 | 용도 |
|------|----------|------------|------|
| **Backend** | | | |
| | FastAPI | - | RESTful API 프레임워크 |
| | Python | 3.12 | 백엔드 개발 언어 |
| | asyncio | - | 비동기 처리 |
| | asyncpg | - | PostgreSQL 비동기 연결 |
| | OpenAI Python SDK | - | OpenAI API 클라이언트 |
| **Frontend** | | | |
| | Vue | 3 | 프론트엔드 프레임워크 |
| | Vite | - | 빌드 도구 |
| | TypeScript | - | 타입 안전성 보장 |
| | Pinia | - | 상태 관리 |
| | Vue Router | - | 라우팅 |
| **데이터베이스** | | | |
| | PostgreSQL | - | 관계형 데이터베이스 |
| | pgvector | - | 벡터 확장 |
| | asyncpg | - | 비동기 DB 연결 라이브러리 |
| **AI 모델** | | | |
| 임베딩 | BAAI/bge-m3 | - | 문서 및 질문 임베딩 생성 (1024차원) |
| Reranker | Dongjin-kr/ko-reranker | - | 검색 결과 재순위화 (Cross-Encoder) |
| LLM | GPT-4o-mini | OpenAI | 질문 재구성, 답변 생성, 맥락 분석 |
| **데이터 처리** | | | |
| | pymupdf4llm | - | PDF 텍스트 추출 |
| | langchain-text-splitters | - | 텍스트 청킹 |
| | requests | - | HTTP 요청 |
| | BeautifulSoup4 | - | HTML 파싱 |
| | pandas | - | 데이터 분석 및 처리 |
| **개발 환경** | | | |
| | Docker | - | 컨테이너화 및 배포 |
| | pip/conda | - | 패키지 관리 |
| | uvicorn | - | ASGI 서버 |
| | python-dotenv | - | 환경 변수 관리 |

---

## 4. 시스템 아키텍처

(추후 Miro를 활용하여 별도 작성 예정)

---

## 5. WBS

(팀 GitHub Project Kanban 보드 활용 예정)

---

## 6. 요구사항 명세서

(팀 논의 후 작성 예정)

---

## 7. 수집한 데이터 및 전처리 요약

### 데이터 수집

#### LH (한국토지주택공사) 공고 데이터
- **수집 기간**: 2024년 11월 1일 이후 공고
- **수집 방법**: 웹 크롤링 (POST 방식)
- **프로토타입 범위**: 서울/경기 지역 공고만 대상
- **수집 항목**: 공고번호, 유형, 공고명, 지역, 게시일, 마감일, 상태, 조회수, 상세 URL
- **유형 분류**:
  - 임대: 통합공공임대, 통합공공임대(신혼희망), 국민임대, 공공임대, 영구임대, 행복주택, 행복주택(신혼희망), 장기전세, 신축다세대매입임대, 가정어린이집, 매입임대, 전세임대, 집주인임대, 6년 공공임대주택
  - 분양: 분양주택, 공공분양(신혼희망)
- **저장 형식**: CSV (lh_lease_notices_F.csv, lh_sale_notices_F.csv)

#### GH (경기주택도시공사) 공고 데이터
- **수집 상태**: 크롤링 완료 (프로토타입에서는 미사용)

#### SH (서울주택도시공사) 공고 데이터
- **수집 상태**: 크롤링 완료 (프로토타입에서는 미사용)

### 데이터 전처리

#### PDF 문서 처리
- 공고 상세 페이지에서 PDF 문서 다운로드
- PDF 텍스트 추출 및 구조화

#### 텍스트 청킹 (Chunking)
- **기반 문서**: PDF에서 추출한 텍스트를 마크다운 형식으로 변환한 문서
- **최소 청크 크기**: 100자
- **최적 청크 크기**: 600자
- **최대 청크 크기**: 1200자
- **최대 테이블 크기**: 3000자
- **청크 오버랩**: 150자
- **방법**: RecursiveCharacterTextSplitter 활용, 섹션 헤더 및 테이블 구조 보존
- **특징**: 
  - 문맥 보존을 위한 스마트 청킹
  - 섹션 헤더 자동 감지 및 보존
  - 테이블 구조 유지
  - 의미 있는 청크만 필터링

#### 임베딩 생성
- BAAI/bge-m3 모델을 사용하여 각 청크를 1024차원 벡터로 변환
- 정규화된 임베딩 벡터 생성
- PostgreSQL pgvector 확장을 사용하여 벡터 저장

#### 용어집 (Glossary) 구축
- 공공주택 관련 전문 용어 1,000개 이상 수집 및 정리
- 용어별 쉬운 설명, 상세 설명, 사용 예시, 관련 용어 포함
- RAG 시스템에서 용어 설명 제공에 활용

---

## 8. DB 연동 구현 코드

### 데이터베이스 스키마

PostgreSQL에서 총 3개의 테이블을 사용합니다.

#### announcements 테이블
웹 크롤링을 통해 수집한 공고 메타데이터를 저장하는 테이블입니다.

**주요 컬럼**:
- `id`: 공고 고유 ID
- `notice_type`: 공고 유형 (국민임대, 행복주택 등)
- `category`: 카테고리 (lease/sale)
- `title`: 공고 제목
- `region`: 지역
- `posted_date`: 게시일
- `deadline_date`: 마감일
- `status`: 상태
- `view_count`: 조회수
- `url`: 공고 URL
- `is_vectorized`: 벡터화 완료 여부
- `vectorized_at`: 벡터화 완료 시각
- `created_at`, `updated_at`: 생성/수정 시각

#### announcement_files 테이블
각 공고에 해당하는 PDF 문서 다운로드 정보를 저장하는 테이블입니다.

**주요 컬럼**:
- `id`: 파일 고유 ID
- `announcement_id`: 공고 ID (외래키)
- `file_name`: 파일명
- `file_path`: 파일 경로
- `is_vectorized`: 벡터화 완료 여부
- `vectorized_at`: 벡터화 완료 시각
- `created_at`: 생성 시각

#### document_chunks 테이블
공고 PDF 문서를 청킹하고 임베딩한 벡터를 저장하는 테이블입니다. RDB와 VectorDB의 역할을 동시에 수행합니다.

**주요 컬럼**:
- `id`: 청크 고유 ID
- `announcement_id`: 공고 ID (외래키)
- `file_id`: 파일 ID (외래키)
- `chunk_text`: 청크 텍스트
- `chunk_index`: 청크 인덱스
- `page_number`: 페이지 번호 (NULL 가능)
- `embedding`: 임베딩 벡터 (pgvector 타입, 1024차원)
- `metadata`: 메타데이터 (JSONB)
  - `section`: 섹션 정보
  - `file_name`: 파일명
  - `has_table`: 테이블 포함 여부
  - `chunk_length`: 청크 길이

### 주요 구현 파일

#### Backend
- `back-end/zip_fit/gongo.py`: 벡터 검색, 키워드 검색, 하이브리드 검색, 재순위화 구현
- `back-end/zip_fit/config.py`: 데이터베이스 연결 설정 및 RAG 파라미터 설정
- `back-end/zip_fit/dependencies.py`: 데이터베이스 연결 및 모델 로딩 관리

#### 데이터베이스 관리
- `lab/이인재/규격/database.py`: 데이터베이스 관리 클래스 (벡터화 진행 상황 추적, 청크 저장 등)

### 벡터 검색 구현
- **벡터 유사도 검색**: pgvector의 cosine distance 연산자 (`<=>`) 활용
- **하이브리드 검색**: 벡터 검색과 키워드 검색 결과 병합
- **재순위화**: Cross-Encoder 기반 Reranker로 검색 결과 재정렬
- **필터링**: 지역, 유형, 카테고리별 필터링 지원

---

## 9. 테스트 계획 및 결과 보고서

### 테스트 계획

#### 기능 테스트
- [ ] RAG 파이프라인 테스트
- [ ] 벡터 검색 정확도 테스트
- [ ] 세션 관리 테스트
- [ ] API 엔드포인트 테스트

#### 성능 테스트
- [ ] 응답 시간 측정
- [ ] 동시 접속자 처리 테스트
- [ ] 벡터 검색 성능 테스트

#### 사용자 테스트
- [ ] 실제 사용자 시나리오 테스트
- [ ] 답변 정확도 평가

### 테스트 결과
(추후 작성 예정)

---

## 10. 진행 과정 중 프로그램 개선 노력

### 개선 사항
(추후 작성 예정)

### 기술적 도전과 해결
(추후 작성 예정)

### 성능 최적화
(추후 작성 예정)

---

## 11. 수행 결과 (테스트/시연 페이지)

### 시연 페이지
(추후 작성 예정)

### 주요 기능 시연
(추후 작성 예정)

---

## 12. 한 줄 회고

| 팀원 | 역할 | 한 줄 회고 |
|------|------|-----------|
| 김범섭 | 시스템 아키텍처 설계, 프로젝트 총괄, 프론트엔드 개발 | (작성 예정) |
| 김종민 | LLM 파이프라인 구성 (RAG, 임베딩, 청킹 등) | (작성 예정) |
| 이상혁 | 데이터 수집 및 크롤링, 프롬프팅 설계 | (작성 예정) |
| 이인재 | 백엔드 아키텍처 구성 및 데이터베이스 관리 | (작성 예정) |
| 오흥재 | 공공주택 용어집(Glossary) 구축 및 프로젝트 지원 | (작성 예정) |

---

## 개발 환경 설정

### Backend 설정

#### 필수 요구사항
- Python 3.12
- PostgreSQL (pgvector 확장 설치 필요)
- OpenAI API Key

#### 설치 방법

```bash
# Conda 환경 생성
conda create -n zf_back python=3.12
conda activate zf_back

# 필수 패키지 설치
pip install fastapi uvicorn "pydantic[email]"
pip install mysql-connector-python aiomysql langchain openai
pip install sentence-transformers dotenv asyncpg
pip install pymupdf4llm langchain-text-splitters pandas torch
```

#### 환경 변수 설정 (.env 파일)
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_DATABASE=your_database
OPENAI_API_KEY=your_openai_api_key
GOV_API_KEY=your_gov_api_key
MODEL_CACHE_DIR=./model_cache
USE_RERANKER=true
```

#### 서버 실행
```bash
cd back-end/zip_fit
uvicorn main:app --reload
```

### Frontend 설정

#### 필수 요구사항
- Node.js (^20.19.0 || >=22.12.0)

#### 설치 방법
```bash
cd front-end/zf_front
npm install
```

#### 개발 서버 실행
```bash
npm run dev
```

### 데이터베이스 설정

#### Docker를 사용한 데이터베이스 설정 (권장)
프로젝트에서 Docker를 사용하여 데이터베이스를 설정할 수 있습니다. `docker-compose.yml` 파일이 있는 경우 다음 명령어로 실행합니다:

```bash
docker-compose up -d
```

#### PostgreSQL pgvector 확장 설치
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 테이블 생성
(스키마 파일 참조)

#### 버전 확인 방법
PostgreSQL 및 pgvector 버전은 다음 SQL 명령어로 확인할 수 있습니다:
```sql
-- PostgreSQL 버전 확인
SELECT version();

-- pgvector 확장 확인
SELECT * FROM pg_extension WHERE extname = 'vector';

-- pgvector 버전 확인
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

또는 psql 명령어로 확인:
```bash
psql -U your_username -d your_database -c "SELECT version();"
psql -U your_username -d your_database -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"

---

## 프로젝트 구조

```
zip-fit-main/
├── back-end/              # Backend 서버 코드
│   └── zip_fit/          # FastAPI 애플리케이션
│       ├── main.py       # FastAPI 앱 진입점
│       ├── router.py     # API 라우터
│       ├── chatting.py   # RAG 챗봇 서비스 로직
│       ├── llm_handler.py # LLM 처리 (질문 재구성, 답변 생성)
│       ├── gongo.py      # 벡터 검색 및 DB 연동
│       ├── config.py     # 설정 파일
│       └── dependencies.py # 의존성 주입
├── front-end/            # Frontend 클라이언트 코드
│   └── zf_front/        # Vue 3 애플리케이션
│       ├── src/
│       │   ├── views/    # 페이지 컴포넌트
│       │   ├── components/ # 재사용 컴포넌트
│       │   └── router/   # 라우팅 설정
│       └── package.json
├── crawler/              # 크롤러 코드
├── lab/                  # 팀원별 실험 및 개발 코드
│   ├── 김범섭/          # 시스템 아키텍처 설계, 프로젝트 총괄, 프론트엔드 개발
│   ├── 김종민/          # LLM 파이프라인 구성 (RAG, 임베딩, 청킹 등)
│   ├── 이상혁/          # 데이터 수집 및 크롤링, 프롬프팅 설계
│   ├── 이인재/          # 백엔드 아키텍처 구성 및 데이터베이스 관리
│   └── 오흥재/          # 공공주택 용어집(Glossary) 구축 및 프로젝트 지원
└── docs/                 # 프로젝트 문서
```

---

## 라이선스

(추후 결정 예정)

---

## 참고 자료

- [LH 공고 API](https://www.data.go.kr/data/15058530/openapi.do)
- [GH 공고 API](https://www.data.go.kr/data/15119414/fileData.do)
- [OpenAI API 문서](https://platform.openai.com/docs)
- [pgvector 문서](https://github.com/pgvector/pgvector)
