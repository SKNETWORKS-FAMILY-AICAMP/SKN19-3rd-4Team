# 검색 엔진
import json
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, DEFAULT_TOP_K, SIMILARITY_THRESHOLD
from database import DatabaseManager


class SearchEngine:
    """벡터 및 하이브리드 검색을 수행하는 엔진"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        # 1. 임베딩 모델 로드
        self.model = SentenceTransformer(model_name)
        # 2. DB 매니저 초기화
        self.db = DatabaseManager()
    
    def extract_keywords(self, query: str) -> str:
        """
        하이브리드 검색용 키워드 추출
        - 조사(은/는/이/가 등)를 제거하여 검색 정확도 향상
        """
        stop_words = ['은', '는', '이', '가', '을', '를', '의', '에', '에서', '과', '와', '로', '으로']
        words = query.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        return ' '.join(keywords)
    
    def extract_filters(self, query: str) -> Dict[str, Any]:
        """
        사용자 질문에서 '지역'이나 '공고 유형'을 자동으로 감지하여 필터링 조건 생성
        예: "남양주 국민임대 알려줘" -> {'region': '남양주', 'category': 'lease'}
        """
        filters = {}
        
        # 1. 지역 추출 (주요 도시 목록)
        regions = ['서울', '경기', '인천', '남양주', '수원', '화성', '용인', '고양', '성남',
                  '부천', '안산', '안양', '평택', '시흥', '파주', '의정부', '김포', '광명', '광주']
        for region in regions:
            if region in query:
                filters['region'] = region
                break
        
        # 2. 카테고리 추출 (분양 vs 임대)
        if any(word in query for word in ['분양', '공공분양', '신혼희망타운']):
            filters['category'] = 'sale'
        elif any(word in query for word in ['임대', '국민임대', '영구임대', '행복주택', '전세']):
            filters['category'] = 'lease'
        
        return filters
    
    async def vector_search(self, query: str, top_k: int = DEFAULT_TOP_K, **filters) -> List[Dict[str, Any]]:
        """
        순수 벡터 유사도 검색
        """
        # 질문을 벡터로 변환
        query_embedding = self.model.encode(query, normalize_embeddings=True)
        embedding_list = query_embedding.tolist()
        
        # DB에서 유사한 청크 검색
        results = await self.db.search_chunks(
            query_embedding=embedding_list, top_k=top_k, **filters
        )
        
        # 유사도 임계값(Threshold) 필터링
        return [r for r in results if r['similarity'] >= SIMILARITY_THRESHOLD]
    
    async def hybrid_search(self, query: str, top_k: int = DEFAULT_TOP_K, vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (벡터 + 키워드 매칭)
        - vector_weight: 벡터 점수 비중 (기본 0.7), 키워드 점수 비중 (0.3)
        """
        query_embedding = self.model.encode(query, normalize_embeddings=True)
        embedding_list = query_embedding.tolist()
        
        # 불용어 제거된 키워드 추출
        keywords = self.extract_keywords(query)
        
        results = await self.db.hybrid_search(
            query_embedding=embedding_list,
            keywords=keywords,
            top_k=top_k,
            vector_weight=vector_weight
        )
        
        return results
    
    async def smart_search(self, query: str, top_k: int = DEFAULT_TOP_K, use_hybrid: bool = True) -> List[Dict[str, Any]]:
        """
        [스마트 검색 전략]
        1. 질문에서 필터(지역, 유형)가 발견되면 -> 필터를 적용한 정밀 벡터 검색 수행
        2. 필터가 없으면 -> 하이브리드 검색으로 넓게 탐색
        """
        filters = self.extract_filters(query)
        
        # 필터가 감지되면 해당 조건으로 벡터 검색 (정확도 우선)
        if filters:
            # 단, 필터가 있어도 하이브리드를 끄고 필터링된 벡터 검색을 수행
            return await self.vector_search(query, top_k, **filters)
        
        # 필터가 없으면 하이브리드 검색 (탐색 범위 우선)
        if use_hybrid:
            return await self.hybrid_search(query, top_k)
        else:
            return await self.vector_search(query, top_k)
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        검색 결과(Context)를 LLM에게 넘겨주기 좋게 문자열로 포맷팅
        """
        if not results:
            return "검색 결과 없음"
        
        output = []
        for idx, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            output.append(
                f"[{idx}] {result['title']}\n"
                f"    지역: {result['region']} | 카테고리: {result['category']} | "
                f"유사도: {result['similarity']:.2%}\n"
                f"    파일: {metadata.get('file_name', 'N/A')}\n"
                f"    내용: {result['chunk_text']}\n" # LLM은 전체 내용을 봐야 하므로 자르지 않음
            )
        
        return "\n".join(output)