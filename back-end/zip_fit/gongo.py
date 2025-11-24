import asyncpg
import json
import asyncio
from typing import List, Dict, Tuple
import config
from dependencies import get_embedding_model, get_reranker, get_db_config

# 1. 벡터 검색 (기존 유지)
async def vector_search(query: str, top_k: int = 15, filters: dict = None, filter_ids: List[str] = None) -> List[Dict]:
    # ... (기존 vector_search 코드와 100% 동일, 그대로 두세요) ...
    # (지면상 생략, 기존 코드 사용)
    model = get_embedding_model()
    query_embedding = model.encode(query, normalize_embeddings=True)
    conn = await asyncpg.connect(**get_db_config())
    try:
        where_clauses, params = [], [str(query_embedding.tolist())]
        if filters:
            if filters.get('region'):
                where_clauses.append(f"a.region LIKE ${len(params)+1}")
                params.append(f"%{filters['region']}%")
            if filters.get('category'):
                where_clauses.append(f"a.category = ${len(params)+1}")
                params.append(filters['category'])
            if filters.get('notice_type'):
                where_clauses.append(f"a.notice_type LIKE ${len(params)+1}")
                params.append(f"%{filters['notice_type']}%")
        if filter_ids:
            where_clauses.append(f"a.id = ANY(${len(params)+1}::text[])")
            params.append(filter_ids)
        where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
        params.append(top_k)
        sql = f"""
            SELECT dc.id as chunk_id, dc.announcement_id, a.title, a.category, a.region, a.notice_type,
                   dc.chunk_text, dc.metadata, (1 - (dc.embedding <=> $1::vector)) as similarity
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

# 2. 키워드 검색 (기존 유지)
async def keyword_search(keywords: List[str], top_k: int = 10, filters: dict = None, filter_ids: List[str] = None) -> List[Dict]:
    # ... (기존 keyword_search 코드와 100% 동일, 그대로 두세요) ...
    if not keywords: return []
    conn = await asyncpg.connect(**get_db_config())
    try:
        params, keyword_conditions = [], []
        for kw in keywords:
            keyword_conditions.append(f"dc.chunk_text LIKE ${len(params)+1}")
            params.append(f"%{kw}%")
        keyword_sql = " OR ".join(keyword_conditions)
        where_clauses = []
        if filters:
            if filters.get('region'):
                where_clauses.append(f"a.region LIKE ${len(params)+1}")
                params.append(f"%{filters['region']}%")
            if filters.get('category'):
                where_clauses.append(f"a.category = ${len(params)+1}")
                params.append(filters['category'])
            if filters.get('notice_type'):
                where_clauses.append(f"a.notice_type LIKE ${len(params)+1}")
                params.append(f"%{filters['notice_type']}%")
        if filter_ids:
            where_clauses.append(f"a.id = ANY(${len(params)+1}::text[])")
            params.append(filter_ids)
        where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
        params.append(top_k)
        sql = f"""
            SELECT DISTINCT ON (dc.id) dc.id as chunk_id, dc.announcement_id, a.title, a.category, a.region,
                   a.notice_type, dc.chunk_text, dc.metadata, 0.5 as similarity
            FROM document_chunks dc
            JOIN announcements a ON dc.announcement_id = a.id
            WHERE ({keyword_sql}) {where_sql}
            LIMIT ${len(params)}
        """
        results = await conn.fetch(sql, *params)
        return [dict(r) for r in results]
    finally:
        await conn.close()

# 3. [신규 추가] 멀티 쿼리 하이브리드 검색
async def multi_query_hybrid_search(query_analysis: Dict, multi_queries: List[str]) -> List[Dict]:
    """여러 쿼리를 동시에 실행하여 검색 결과를 병합합니다."""
    filters = query_analysis.get('filters', {})
    
    tasks = []
    # 모든 쿼리에 대해 검색 실행
    for q in multi_queries:
        tasks.append(vector_search(q, top_k=10, filters=filters))
        # 키워드는 한 번만 검색해도 충분 (공통이므로)
    
    # 키워드 검색은 별도로 1회 추가
    tasks.append(keyword_search(query_analysis.get('keywords', []), top_k=5, filters=filters))
    
    results_list = await asyncio.gather(*tasks)
    
    # 중복 제거 및 병합
    all_results = {}
    for results in results_list:
        for r in results:
            if r['chunk_id'] not in all_results:
                all_results[r['chunk_id']] = r
    
    return list(all_results.values())

# 4. 재순위화 (기존 유지)
def rerank_results(query: str, search_results: List[Dict], top_k: int = 15) -> List[Dict]:
    if not search_results: return []
    reranker = get_reranker()
    if reranker is None:
        return sorted(search_results, key=lambda x: x.get('similarity', 0), reverse=True)[:top_k]
    try:
        pairs = [(query, r['chunk_text']) for r in search_results]
        scores = reranker.predict(pairs)
        for i, result in enumerate(search_results): result['rerank_score'] = float(scores[i])
        return sorted(search_results, key=lambda x: x['rerank_score'], reverse=True)[:top_k]
    except: return search_results[:top_k]

# 5. [신규 추가] 청크 병합 (같은 공고끼리 묶기)
async def merge_chunks(chunks: List[Dict]) -> List[Dict]:
    if not chunks: return []
    
    announcement_chunks = {}
    for chunk in chunks:
        ann_id = chunk['announcement_id']
        if ann_id not in announcement_chunks:
            announcement_chunks[ann_id] = []
        announcement_chunks[ann_id].append(chunk)
    
    merged_results = []
    for ann_id, ann_chunks in announcement_chunks.items():
        # 점수가 가장 높은 청크의 점수를 대표 점수로 사용
        max_score = max(ann_chunks, key=lambda x: x.get('rerank_score', 0)).get('rerank_score', 0)
        
        # 텍스트 합치기
        merged_text = "\n\n".join([c['chunk_text'] for c in ann_chunks])
        
        merged_results.append({
            'announcement_id': ann_id,
            'title': ann_chunks[0]['title'],
            'region': ann_chunks[0]['region'],
            'category': ann_chunks[0]['category'],
            'notice_type': ann_chunks[0]['notice_type'],
            'merged_content': merged_text,
            'rerank_score': max_score,
            'chunk_count': len(ann_chunks)
        })
    
    # 점수순 정렬
    merged_results.sort(key=lambda x: x['rerank_score'], reverse=True)
    return merged_results

# 6. 컨텍스트 구성 (수정됨 - 병합된 데이터 처리)
def build_context(merged_results: List[Dict]) -> Tuple[str, List[Dict]]:
    if not merged_results: return "검색 결과 없음", []
    
    context_parts, sources = [], []
    for idx, m in enumerate(merged_results, 1):
        context_parts.append(f"""
문서 {idx}: {m['title']}
- 지역: {m['region']} / 유형: {m['notice_type']}
{m['merged_content']}
""".strip())
        
        sources.append({
            'announcement_id': str(m['announcement_id']),
            'title': m['title'],
            'region': m['region'],
            'score': m['rerank_score'],
            'chunk_count': m['chunk_count']
        })
    
    return "\n\n".join(context_parts), sources