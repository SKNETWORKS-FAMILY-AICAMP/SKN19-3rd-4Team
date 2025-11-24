import json
from typing import List, Dict, Any, AsyncGenerator
import config
from dependencies import get_openai_client

# 질문 재구성 (Query Rewriting)
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
사용자의 질문을 분석하여 검색 엔진이 이해하기 쉬운 JSON 포맷으로 변환하세요.
JSON 포맷: {"rewritten": "...", "expanded": "...", "keywords": [], "filters": {}}
"""
    user_prompt = f"""{context_str}\n\n[현재 질문]: {query}\n\n위 질문을 분석하여 JSON으로 반환해주세요."""

    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        result['original'] = query
        return result
        
    except Exception as e:
        print(f"[Error] 쿼리 재구성 실패: {e}")
        return {
            'original': query, 'rewritten': query, 'expanded': query, 
            'keywords': query.split(), 'filters': {}
        }

# 맥락 분석 (Context Analysis)
async def analyze_context(query: str, history: List[Dict]) -> Dict:
    if not history:
        return {'is_context_question': False}
    
    client = get_openai_client()
    history_str = "\n".join([f"Q: {h.get('query','')}\nA: {h.get('answer','')}..."[:200] for h in history[-2:]])
    
    system_prompt = """당신은 대화 흐름 분석가입니다. 
JSON 응답: {"is_context_question": true/false, "reason": "...", "referenced_announcement_indices": [0]}"""
    
    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"이전 대화:\n{history_str}\n\n현재 질문: {query}"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[Error] 맥락 분석 실패: {e}")
        return {'is_context_question': False}

# 답변 생성 (Answer Generation - 일반)
async def generate_answer(query: str, context: str, sources: List[Dict]) -> Dict:
    client = get_openai_client()
    
    system_prompt = """당신은 LH 공고 전문 AI 상담원입니다.
필수: 리스트 형식(1. 2. 3.)으로 답변하고 출처를 표기하세요."""

    user_prompt = f"""# [검색된 문서]\n{context}\n\n# [사용자 질문]\n{query}"""

    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=config.OPENAI_MAX_TOKENS
        )
        
        return {
            'answer': response.choices[0].message.content,
            'sources': sources,
            'metadata': {'model': config.OPENAI_MODEL, 'tokens': response.usage.total_tokens}
        }
    except Exception as e:
        return {'answer': f"오류: {str(e)}", 'sources': sources, 'metadata': {'error': str(e)}}

# 스트리밍 답변 생성 (Streaming Answer Generation)
async def generate_answer_stream(query: str, context: str) -> AsyncGenerator[str, None]:
    client = get_openai_client()
    
    system_prompt = """당신은 LH 공고 전문 AI 상담원입니다.
필수: 리스트 형식(1. 2. 3.)으로 답변하고 출처를 표기하세요."""

    user_prompt = f"""# [검색된 문서]\n{context}\n\n# [사용자 질문]\n{query}"""

    try:
        stream = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=config.OPENAI_MAX_TOKENS,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        yield f"\n[Error] 답변 생성 중 오류 발생: {str(e)}"