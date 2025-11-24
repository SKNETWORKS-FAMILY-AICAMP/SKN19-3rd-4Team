import asyncpg
import json
from typing import List, Dict, Tuple, Any
import config
from dependencies import get_embedding_model, get_reranker, get_db_config


# 1. 벡터 검색 (Vector Search)
async def vector_search(query: str, top_k: int = 15, filters: dict = None, filter_ids: List[str] = None) -> List[Dict]:
    """
    임베딩 모델을 사용해 의미 기반 검색을 수행합니다.
    """
    # 임베딩 생성
    model = get_embedding_model()
    query_embedding = model.encode(query, normalize_embeddings=True)
    
    conn = await asyncpg.connect(**get_db_config())
    try:
        where_clauses, params = [], [str(query_embedding.tolist())]
        
        # 필터 적용
        if filters:
            if 'region' in filters:
                where_clauses.append(f"a.region LIKE ${len(params)+1}")
                params.append(f"%{filters['region']}%")
            if 'category' in filters:
                where_clauses.append(f"a.category = ${len(params)+1}")
                params.append(filters['category'])
            if 'notice_type' in filters:
                where_clauses.append(f"a.notice_type LIKE ${len(params)+1}")
                params.append(f"%{filters['notice_type']}%")
        
        # 특정 ID만 검색 (맥락 검색용)
        if filter_ids:
            where_clauses.append(f"a.id = ANY(${len(params)+1}::text[])")
            params.append(filter_ids)
        
        where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
        params.append(top_k)
        
        # pgvector 거리 계산 (<=> : 코사인 거리)
        sql = f"""
            SELECT dc.id as chunk_id, dc.announcement_id, a.title, a.category, a.region, a.notice_type,
                   dc.chunk_text, dc.metadata, (1 - (dc.embedding <=> $1::vector)) as similarity, 'vector' as search_type
            FROM document_chunks dc
            JOIN announcements a ON dc.announcement_id = a.id
            WHERE 1=1 {where_sql}
            ORDER BY dc.embedding <=> $1::vector
            LIMIT ${len(params)}
        """
        results = await conn.fetch(sql, *params)
        return [dict(r) for r in results]
    finally:
        await conn.close()


# 키워드 검색 (Keyword Search)
async def keyword_search(keywords: List[str], top_k: int = 10, filters: dict = None) -> List[Dict]:
    """
    정확한 단어 매칭을 위한 LIKE 검색을 수행합니다.
    """
    if not keywords:
        return []

    conn = await asyncpg.connect(**get_db_config())
    try:
        params, keyword_conditions = [], []
        for kw in keywords:
            keyword_conditions.append(f"dc.chunk_text LIKE ${len(params)+1}")
            params.append(f"%{kw}%")
        
        keyword_sql = " OR ".join(keyword_conditions)
        
        where_clauses = []
        if filters:
            if 'region' in filters:
                where_clauses.append(f"a.region LIKE ${len(params)+1}")
                params.append(f"%{filters['region']}%")
            if 'category' in filters:
                where_clauses.append(f"a.category = ${len(params)+1}")
                params.append(filters['category'])
            if 'notice_type' in filters:
                where_clauses.append(f"a.notice_type LIKE ${len(params)+1}")
                params.append(f"%{filters['notice_type']}%")
        
        where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
        params.append(top_k)
        
        sql = f"""
            SELECT DISTINCT ON (dc.id) dc.id as chunk_id, dc.announcement_id, a.title, a.category, a.region,
                   a.notice_type, dc.chunk_text, dc.metadata, 0.5 as similarity, 'keyword' as search_type
            FROM document_chunks dc
            JOIN announcements a ON dc.announcement_id = a.id
            WHERE ({keyword_sql}) {where_sql}
            LIMIT ${len(params)}
        """
        results = await conn.fetch(sql, *params)
        return [dict(r) for r in results]
    finally:
        await conn.close()


# 하이브리드 검색 (Hybrid Search)
async def hybrid_search(query_analysis: Dict, vector_top_k: int = 15, keyword_top_k: int = 10) -> List[Dict]:
    """
    Vector 검색 결과와 Keyword 검색 결과를 병합합니다.
    """
    # Vector Search
    vector_results = await vector_search(
        query_analysis.get('expanded', query_analysis.get('original')), 
        top_k=vector_top_k, 
        filters=query_analysis.get('filters', {})
    )
    
    # Keyword Search
    keyword_results = await keyword_search(
        query_analysis.get('keywords', []), 
        top_k=keyword_top_k, 
        filters=query_analysis.get('filters', {})
    )
    
    # 중복 제거 및 병합
    seen_chunks = set()
    combined = []
    
    # Vector 결과 우선 추가
    for r in vector_results:
        if r['chunk_id'] not in seen_chunks:
            seen_chunks.add(r['chunk_id'])
            combined.append(r)
            
    # Keyword 결과 추가
    for r in keyword_results:
        if r['chunk_id'] not in seen_chunks:
            seen_chunks.add(r['chunk_id'])
            combined.append(r)
            
    return combined


# 4. 재순위화 (Reranking)
def rerank_results(query: str, search_results: List[Dict], top_k: int = 8) -> List[Dict]:
    """
    Cross-Encoder를 사용하여 결과의 순위를 재조정합니다.
    config.USE_RERANKER가 False면 단순 유사도 정렬을 수행합니다.
    """
    if not search_results:
        return []
    
    reranker = get_reranker() # 스위치가 꺼져있으면 None 반환

    # Reranker OFF 또는 모델 로드 실패 시
    if reranker is None:
        # 기존 similarity 점수(Vector 검색 결과) 기준으로 정렬
        sorted_results = sorted(search_results, key=lambda x: x.get('similarity', 0), reverse=True)
        return sorted_results[:top_k]

    # Reranker ON
    try:
        pairs = [(query, r['chunk_text']) for r in search_results]
        scores = reranker.predict(pairs)
        
        for i, result in enumerate(search_results):
            result['rerank_score'] = float(scores[i])
        
        # Rerank 점수 기준 정렬
        reranked = sorted(search_results, key=lambda x: x['rerank_score'], reverse=True)
        return reranked[:top_k]
        
    except Exception as e:
        print(f"[Warning] Reranking 중 오류 발생: {e}")
        return search_results[:top_k]



# 컨텍스트 구성 (Context Builder)
def build_context(reranked_results: List[Dict]) -> Tuple[str, List[Dict]]:
    """
    LLM에 주입할 컨텍스트 텍스트를 생성합니다.
    같은 공고의 청크들을 그룹화하여 보여줍니다.
    """
    announcement_chunks = {}
    
    # 공고별로 청크 그룹화
    for r in reranked_results:
        ann_id = r['announcement_id']
        score = r.get('rerank_score', r.get('similarity', 0)) # Reranker OFF일 경우 similarity 사용
        
        if ann_id not in announcement_chunks:
            announcement_chunks[ann_id] = {
                'announcement_id': ann_id, 
                'title': r['title'], 
                'category': r['category'],
                'region': r['region'], 
                'notice_type': r['notice_type'], 
                'metadata': r['metadata'],
                'chunk_texts': [r['chunk_text']], 
                'max_score': score, 
                'chunk_count': 1
            }
        else:
            announcement_chunks[ann_id]['chunk_texts'].append(r['chunk_text'])
            announcement_chunks[ann_id]['chunk_count'] += 1
            announcement_chunks[ann_id]['max_score'] = max(announcement_chunks[ann_id]['max_score'], score)
    
    # 점수가 높은 공고 순으로 정렬
    merged = sorted(announcement_chunks.values(), key=lambda x: x['max_score'], reverse=True)
    
    context_parts, sources = [], []
    for idx, m in enumerate(merged, 1):
        # 메타데이터 파싱 (문자열인 경우)
        meta = m['metadata']
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except:
                pass
                
        category_name = "임대" if m['category'] == 'lease' else "분양"
        merged_text = '\n\n'.join(m['chunk_texts'])
        
        context_parts.append(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
문서 {idx}: {m['title']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[기본 정보]
- 분류: {category_name}
- 지역: {m['region']}
- 유형: {m['notice_type'] or 'N/A'}
- 관련도: {m['max_score']:.3f}

[문서 내용]
{merged_text}
        """.strip())
        
        sources.append({
            'announcement_id': str(m['announcement_id']), # ID를 문자열로 변환 (안전장치)
            'title': m['title'],
            'region': m['region'],
            'score': m['max_score'],
            'chunk_count': m['chunk_count']
        })
    
    return "\n\n".join(context_parts), sources