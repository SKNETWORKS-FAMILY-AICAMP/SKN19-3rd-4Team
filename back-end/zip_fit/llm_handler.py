import json
from typing import List, Dict, Any, AsyncGenerator
import config
from dependencies import get_openai_client

# 1. 질문 재구성 (Query Rewriting) - [업그레이드됨]
async def rewrite_query(query: str, conversation_history: List[Dict] = None) -> Dict:
    client = get_openai_client()
    
    context_str = ""
    if conversation_history:
        recent = conversation_history[-3:]
        context_str = "\n[이전 대화]\n" + "\n".join([
            f"User: {h.get('query','')}\nAI: {h.get('answer','')}..."[:200]
            for h in recent
        ])
    
    system_prompt = """당신은 LH 공고 검색 시스템의 쿼리 최적화 전문가입니다.
사용자의 질문을 분석하여 다음 정보를 추출하세요.

# 추출 규칙
1. region: "경기도", "서울특별시" 등 광역시/도 단위 (세부 지역은 search_keywords로)
2. notice_type: "국민임대", "행복주택" 등 (없으면 빈 문자열)
3. category: "lease"(임대) 또는 "sale"(분양) (없으면 빈 문자열)
4. rewritten_question: 검색용 자연어 질문
5. search_keywords: 핵심 검색어 리스트

# 출력 형식 (JSON)
{
  "region": "",
  "notice_type": "",
  "category": "",
  "rewritten_question": "",
  "search_keywords": []
}
"""
    user_prompt = f"""{context_str}\n\n[현재 질문]: {query}\n\n위 질문을 분석하여 JSON으로 반환해주세요."""

    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        
        # 필터 딕셔너리 구조 맞추기 (gongo.py 호환용)
        result['filters'] = {
            'region': result.get('region', ''),
            'notice_type': result.get('notice_type', ''),
            'category': result.get('category', '')
        }
        result['rewritten'] = result.get('rewritten_question', query)
        result['keywords'] = result.get('search_keywords', [])
        result['original'] = query
        return result
    except Exception as e:
        print(f"[Error] 쿼리 재구성 실패: {e}")
        return {'original': query, 'rewritten': query, 'keywords': query.split(), 'filters': {}}

# [신규 추가] 멀티 쿼리 생성
async def generate_multi_queries(query: str, base_query_analysis: Dict, num_queries: int = 2) -> List[str]:
    """원본 질문을 바탕으로 유사한 질문 N개를 추가 생성합니다."""
    client = get_openai_client()
    base_question = base_query_analysis.get('rewritten', query)

    prompt = f"""LH 주택 공고 검색을 위해 질문을 다양한 표현으로 변환하세요.
원본: {base_question}

다음 {num_queries}개의 다른 버전을 생성하세요:
1. 동의어나 유사 표현 사용
2. 더 구체적이거나 상세한 버전
규칙: 번호 없이 한 줄에 질문 하나씩만 작성.

변환된 질문들:"""

    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        generated = [q.strip() for q in response.choices[0].message.content.strip().split('\n') if q.strip()]
        # 원본 질문 + 생성된 질문
        return [base_question] + generated[:num_queries]
    except Exception as e:
        print(f"[Error] 멀티 쿼리 생성 실패: {e}")
        return [base_question]

# 2. 맥락 분석 (기존 유지)
async def analyze_context(query: str, history: List[Dict]) -> Dict:
    if not history: return {'is_context_question': False}
    client = get_openai_client()
    history_str = "\n".join([f"Q: {h.get('query','')}\nA: {h.get('answer','')}..."[:200] for h in history[-2:]])
    system_prompt = """당신은 대화 흐름 분석가입니다. 
JSON 응답: {"is_context_question": true/false, "reason": "...", "referenced_announcement_indices": [0]}"""
    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"이전 대화:\n{history_str}\n\n현재 질문: {query}"}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except: return {'is_context_question': False}

# 3. 답변 생성 (기존 유지 - async)
async def generate_answer(query: str, context: str, sources: List[Dict]) -> Dict:
    client = get_openai_client()
    system_prompt = """당신은 LH 공고 전문 AI 상담원입니다.
필수: 리스트 형식(1. 2. 3.)으로 답변하고 출처를 표기하세요."""
    user_prompt = f"""# [검색된 문서]\n{context}\n\n# [사용자 질문]\n{query}\n\n위 문서를 바탕으로 답변해주세요."""
    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=config.OPENAI_TEMPERATURE
        )
        return {'answer': response.choices[0].message.content, 'sources': sources, 'metadata': {'tokens': response.usage.total_tokens}}
    except Exception as e:
        return {'answer': str(e), 'sources': sources}

# 4. 스트리밍 답변 생성 (기존 유지)
async def generate_answer_stream(query: str, context: str) -> AsyncGenerator[str, None]:
    client = get_openai_client()
    system_prompt = "당신은 LH 공고 전문 AI 상담원입니다. 필수: 리스트 형식으로 답변하세요."
    user_prompt = f"# [검색된 문서]\n{context}\n\n# [사용자 질문]\n{query}"
    try:
        stream = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content: yield chunk.choices[0].delta.content
    except Exception as e: yield str(e)