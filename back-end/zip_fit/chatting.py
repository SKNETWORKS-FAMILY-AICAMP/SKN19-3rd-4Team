from typing import List, Dict, AsyncGenerator
import json
import llm_handler
import gongo

# 1. 기본 RAG 프로세스 (일반 응답)
async def rag_process(query: str, history: List[Dict]) -> Dict:
    # 1. 질문 재구성
    query_analysis = await llm_handler.rewrite_query(query, history)
    
    # 2. [신규] 멀티 쿼리 생성
    multi_queries = await llm_handler.generate_multi_queries(query, query_analysis)
    
    # 3. [신규] 멀티 쿼리 검색
    search_results = await gongo.multi_query_hybrid_search(query_analysis, multi_queries)
    
    if not search_results:
        return {'answer': "검색 결과가 없습니다.", 'sources': []}
    
    # 4. 재순위화
    reranked = gongo.rerank_results(query_analysis['rewritten'], search_results)
    
    # 5. [신규] 청크 병합
    merged = await gongo.merge_chunks(reranked)
    
    # 6. 컨텍스트 구성
    context, sources = gongo.build_context(merged)
    
    # 7. 답변 생성
    result = await llm_handler.generate_answer(query_analysis['rewritten'], context, sources)
    return result

# 2. 통합 채팅 서비스 (라우터에서 호출)
async def chat_service(query: str, history: List[Dict]) -> Dict:
    # 맥락 분석 등은 기존과 동일하되, 내부에서 rag_process 호출
    # (맥락 질문 처리는 복잡하므로 여기서는 간단히 rag_process로 통일하거나, 
    # 기존 코드의 _context_aware_search 대신 multi_query_hybrid_search 사용)
    return await rag_process(query, history)

# 3. 스트리밍 서비스
async def chat_stream_service(query: str, history: List[Dict]) -> AsyncGenerator[str, None]:
    try:
        yield json.dumps({"type": "log", "content": "🔍 질문 분석 및 확장 중..."}) + "\n"
        query_analysis = await llm_handler.rewrite_query(query, history)
        multi_queries = await llm_handler.generate_multi_queries(query, query_analysis)
        
        yield json.dumps({"type": "log", "content": f"🚀 {len(multi_queries)}개의 질문으로 동시 검색..."}) + "\n"
        search_results = await gongo.multi_query_hybrid_search(query_analysis, multi_queries)
        
        if not search_results:
            yield json.dumps({"type": "answer", "content": "결과가 없습니다."}) + "\n"
            return

        reranked = gongo.rerank_results(query_analysis['rewritten'], search_results)
        merged = await gongo.merge_chunks(reranked) # 병합
        context, sources = gongo.build_context(merged)
        
        yield json.dumps({"type": "sources", "data": sources}) + "\n"
        yield json.dumps({"type": "log", "content": "✍️ 답변 작성 중..."}) + "\n"
        
        async for token in llm_handler.generate_answer_stream(query_analysis['rewritten'], context):
            yield json.dumps({"type": "answer", "content": token}) + "\n"
            
    except Exception as e:
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"