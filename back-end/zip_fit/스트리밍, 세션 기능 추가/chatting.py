from typing import List, Dict, Any, AsyncGenerator
import json
import llm_handler
import gongo


# 1. 기본 RAG 프로세스 (Standard RAG)
async def rag_process(query: str, history: List[Dict], verbose: bool = True) -> Dict:
    """
    맥락과 관계없는 새로운 질문을 처리하는 표준 RAG 파이프라인
    (비-스트리밍 응답용)
    """
    # 질문 재구성
    query_analysis = await llm_handler.rewrite_query(query, history)
    if verbose:
        print(f"[Log] 재구성된 질문: {query_analysis.get('rewritten')}")
    
    # 하이브리드 검색
    search_results = await gongo.hybrid_search(query_analysis)
    
    if not search_results:
        return {
            'query': query,
            'answer': "죄송합니다. 요청하신 조건에 맞는 공고를 찾을 수 없습니다.",
            'sources': []
        }
    
    # 재순위화
    reranked = gongo.rerank_results(query_analysis.get('rewritten', query), search_results)
    
    # 컨텍스트 구성
    context, sources = gongo.build_context(reranked)
    
    # 답변 생성
    result = await llm_handler.generate_answer(query_analysis.get('rewritten', query), context, sources)
    
    result['query_analysis'] = query_analysis
    return result


# 2. 통합 채팅 서비스 (Context-Aware Service - Non-Streaming)
async def chat_service(query: str, history: List[Dict]) -> Dict:
    """
    [일반 응답] API에서 호출하는 메인 진입점.
    맥락을 분석하여 검색 전략을 결정합니다.
    """
    # 맥락 분석
    context_analysis = await llm_handler.analyze_context(query, history)
    is_context = context_analysis.get('is_context_question', False)
    
    # 맥락 질문인 경우
    if is_context and history:
        print(f"[Log] 맥락 질문 감지: {context_analysis.get('reason')}")
        
        prev_ids = _extract_prev_ids(history, context_analysis)
        
        if prev_ids:
            print(f"[Log] 참조 공고 ID: {prev_ids}")
            
            # 질문 재구성
            query_analysis = await llm_handler.rewrite_query(query, history)
            
            # 우선 검색 + 일반 검색 병합
            combined_results = await _context_aware_search(query_analysis, prev_ids)
            
            # 재순위화 및 답변 생성
            reranked = gongo.rerank_results(query_analysis.get('rewritten', query), combined_results)
            context, sources = gongo.build_context(reranked)
            result = llm_handler.generate_answer(query_analysis.get('rewritten', query), context, sources)
            
            result = await llm_handler.generate_answer(query_analysis.get('rewritten', query), context, sources)
            return result

    # 일반 질문인 경우
    print("[Log] 일반 질문으로 처리")
    return await rag_process(query, history)


# 3. 스트리밍 채팅 서비스 (Context-Aware Service - Streaming)
async def chat_stream_service(query: str, history: List[Dict]) -> AsyncGenerator[str, None]:
    """
    [스트리밍 응답] RAG 과정을 단계별로 실시간 전송합니다.
    맥락 인식 로직이 포함되어 있습니다.
    """
    try:
        yield json.dumps({"type": "log", "content": "🔍 질문의 의도를 분석하고 있습니다..."}) + "\n"
        
        # 맥락 분석
        context_analysis = await llm_handler.analyze_context(query, history)
        is_context = context_analysis.get('is_context_question', False)
        
        search_results = []
        query_analysis = {}

        # 검색 전략 결정 (맥락 vs 일반)
        if is_context and history:
            prev_ids = _extract_prev_ids(history, context_analysis)
            
            if prev_ids:
                yield json.dumps({"type": "log", "content": "🔗 이전 대화의 공고를 참조하여 검색합니다..."}) + "\n"
                
                # 질문 재구성
                query_analysis = await llm_handler.rewrite_query(query, history)
                yield json.dumps({"type": "log", "content": f"🔄 최적화된 질문: {query_analysis.get('rewritten')}"}) + "\n"
                
                # 맥락 기반 검색 수행
                search_results = await _context_aware_search(query_analysis, prev_ids)
            else:
                # 맥락이라고 판단했으나 ID를 못 찾은 경우 일반 검색으로 전환
                is_context = False
        
        if not is_context or not search_results:
            # 일반 검색 수행
            yield json.dumps({"type": "log", "content": "📂 전체 공고 문서에서 검색 중입니다..."}) + "\n"
            
            query_analysis = await llm_handler.rewrite_query(query, history)
            yield json.dumps({"type": "log", "content": f"🔄 최적화된 질문: {query_analysis.get('rewritten')}"}) + "\n"
            
            search_results = await gongo.hybrid_search(query_analysis)

        # 검색 결과 없음 처리
        if not search_results:
            yield json.dumps({"type": "answer", "content": "죄송합니다. 관련 정보를 찾을 수 없습니다."}) + "\n"
            return

        # 재순위화
        reranked = gongo.rerank_results(query_analysis.get('rewritten', query), search_results)
        
        # 컨텍스트 및 출처 구성
        context, sources = gongo.build_context(reranked)
        
        # 출처 정보를 먼저 클라이언트에 전송
        yield json.dumps({"type": "sources", "data": [s for s in sources]}) + "\n"
        
        # 답변 생성 (스트리밍)
        yield json.dumps({"type": "log", "content": "✍️ 답변을 작성 중입니다..."}) + "\n"
        
        async for token in llm_handler.generate_answer_stream(query_analysis.get('rewritten', query), context):
            # 토큰 단위로 JSON 포장하여 전송
            yield json.dumps({"type": "answer", "content": token}) + "\n"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"


# [Helper Functions] 중복 로직 분리
def _extract_prev_ids(history: List[Dict], context_analysis: Dict) -> List[str]:
    """이전 대화에서 공고 ID 추출"""
    prev_ids = []
    referenced_indices = context_analysis.get('referenced_announcement_indices', [0])
    
    for idx in referenced_indices:
        if idx < len(history):
            prev_turn = history[-(idx+1)]
            prev_sources = prev_turn.get('sources', [])
            
            for src in prev_sources[:3]:
                ann_id = src.get('announcement_id') if isinstance(src, dict) else getattr(src, 'announcement_id', None)
                if ann_id and str(ann_id) not in prev_ids:
                    prev_ids.append(str(ann_id))
    return prev_ids

async def _context_aware_search(query_analysis: Dict, prev_ids: List[str]) -> List[Dict]:
    """맥락 기반 검색 (ID필터 검색 + 하이브리드 검색 병합)"""
    # 우선 검색 (이전 공고 ID 범위 내)
    context_results = await gongo.vector_search(
        query_analysis.get('rewritten'), 
        top_k=5, 
        filter_ids=prev_ids
    )
    
    # 일반 검색
    general_results = await gongo.hybrid_search(query_analysis)
    
    # 결과 병합
    seen = {r['chunk_id'] for r in context_results}
    combined = context_results + [r for r in general_results if r['chunk_id'] not in seen]
    return combined