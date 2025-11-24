from typing import List, Dict, Any
import llm_handler
import gongo


# 1. 기본 RAG 프로세스 (Standard RAG)
async def rag_process(query: str, history: List[Dict], verbose: bool = True) -> Dict:
    """
    맥락과 관계없는 새로운 질문을 처리하는 표준 RAG 파이프라인
    순서: 재구성 -> 하이브리드 검색 -> 재순위화 -> 컨텍스트 -> 답변 생성
    """
    # 1. 질문 재구성
    query_analysis = await llm_handler.rewrite_query(query, history)
    if verbose:
        print(f"[Log] 재구성된 질문: {query_analysis.get('rewritten')}")
    
    # 2. 하이브리드 검색 (Vector + Keyword)
    search_results = await gongo.hybrid_search(query_analysis)
    
    if not search_results:
        return {
            'query': query,
            'answer': "죄송합니다. 요청하신 조건에 맞는 공고를 찾을 수 없습니다.",
            'sources': []
        }
    
    # 3. 재순위화 (Reranking)
    # query_analysis['rewritten']을 사용하여 검색 정확도 향상
    reranked = gongo.rerank_results(query_analysis.get('rewritten', query), search_results)
    
    # 4. 컨텍스트 구성
    context, sources = gongo.build_context(reranked)
    
    # 5. 답변 생성
    result = llm_handler.generate_answer(query_analysis.get('rewritten', query), context, sources)
    
    # 결과에 분석 정보 포함 (디버깅용)
    result['query_analysis'] = query_analysis
    return result


# 2. 통합 채팅 서비스 (Context-Aware Service)
async def chat_service(query: str, history: List[Dict]) -> Dict:
    """
    API에서 호출하는 메인 진입점.
    질문이 이전 대화와 이어지는지(맥락 질문) 판단하여 처리 방식을 결정합니다.
    """
    
    # 1. 맥락 분석
    context_analysis = await llm_handler.analyze_context(query, history)
    is_context = context_analysis.get('is_context_question', False)
    
    # 2. 맥락 질문인 경우
    if is_context and history:
        print(f"[Log] 맥락 질문 감지: {context_analysis.get('reason')}")
        
        # 이전 대화에서 언급된 공고 ID 추출
        prev_ids = []
        referenced_indices = context_analysis.get('referenced_announcement_indices', [0])
        
        # history 역순 탐색
        for idx in referenced_indices:
            if idx < len(history):
                # history는 {'query':.., 'answer':.., 'sources': [..]} 형태
                prev_turn = history[-(idx+1)]
                prev_sources = prev_turn.get('sources', [])
                
                # 상위 3개 공고만 참조 대상으로 설정
                for src in prev_sources[:3]:
                    # src가 딕셔너리인지 객체인지 확인 후 ID 추출
                    ann_id = src.get('announcement_id') if isinstance(src, dict) else getattr(src, 'announcement_id', None)
                    if ann_id and str(ann_id) not in prev_ids:
                        prev_ids.append(str(ann_id))
        
        if prev_ids:
            print(f"[Log] 참조 공고 ID: {prev_ids}")
            
            # 질문 재구성
            query_analysis = await llm_handler.rewrite_query(query, history)
            
            # 우선 검색 (이전 공고 ID 범위 내에서 검색)
            context_results = await gongo.vector_search(
                query_analysis.get('rewritten', query), 
                top_k=5, 
                filter_ids=prev_ids # 핵심: ID 필터링
            )
            
            # 일반 검색 (혹시 다른 공고일 수도 있으므로 넓게 검색)
            general_results = await gongo.hybrid_search(query_analysis)
            
            # 결과 병합 (중복 제거)
            seen = {r['chunk_id'] for r in context_results}
            combined = context_results + [r for r in general_results if r['chunk_id'] not in seen]
            
            # 재순위화 및 답변 생성
            reranked = gongo.rerank_results(query_analysis.get('rewritten', query), combined)
            context, sources = gongo.build_context(reranked)
            result = llm_handler.generate_answer(query_analysis.get('rewritten', query), context, sources)
            
            result['query_analysis'] = query_analysis
            return result

    # 3. 일반 질문인 경우
    print("[Log] 일반 질문으로 처리")
    return await rag_process(query, history)