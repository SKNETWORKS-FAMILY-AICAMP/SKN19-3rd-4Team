import json
from typing import List, Dict, Any
import config
from dependencies import get_openai_client


# 1. 질문 재구성 (Query Rewriting)
async def rewrite_query(query: str, conversation_history: List[Dict] = None) -> Dict:
    """
    사용자의 모호한 질문을 검색에 적합한 형태로 변환합니다.
    - conversation_history: 이전 대화 내역 (문맥 파악용)
    """
    client = get_openai_client()
    
    # 이전 대화가 있다면 프롬프트에 포함
    context_str = ""
    if conversation_history:
        recent = conversation_history[-3:] # 최근 3개만 참조
        context_str = "\n[이전 대화]\n" + "\n".join([
            f"User: {h.get('query','')}\nAI: {h.get('answer','')}..."[:200]
            for h in recent
        ])
    
    system_prompt = """당신은 LH 공고 검색 시스템의 쿼리 최적화 전문가입니다.
사용자의 질문을 분석하여 검색 엔진이 이해하기 쉬운 JSON 포맷으로 변환하세요.

# 출력 형식 (JSON)
{
    "rewritten": "문맥을 반영하여 명확하게 다시 쓴 질문 (완전한 문장)",
    "expanded": "검색 확률을 높이기 위한 확장 쿼리 (동의어, 관련어 나열)",
    "keywords": ["핵심키워드1", "핵심키워드2", "지역명"],
    "filters": {
        "region": "경기도" 또는 "서울특별시" 등 (광역시/도 단위만),
        "notice_type": "국민임대" 또는 "행복주택" 등,
        "category": "lease" (임대) 또는 "sale" (분양)
    }
}

# 주의사항
1. 사용자가 "거기", "그 공고"라고 하면 [이전 대화]를 참고하여 구체적인 명사로 바꾸세요.
2. 세부 지역명(예: 남양주, 수원)은 'keywords'에만 넣고, 'filters.region'에는 넣지 마세요.
"""

    user_prompt = f"""{context_str}\n\n[현재 질문]: {query}\n\n위 질문을 분석하여 JSON으로 반환해주세요."""

    try:
        response = client.chat.completions.create(
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
        # 실패 시 원본 쿼리 그대로 반환 (Fail-safe)
        return {
            'original': query, 
            'rewritten': query, 
            'expanded': query, 
            'keywords': query.split(), 
            'filters': {}
        }


# 2. 맥락 분석 (Context Analysis)
async def analyze_context(query: str, history: List[Dict]) -> Dict:
    """
    현재 질문이 이전 답변의 특정 공고를 지칭하는지(Follow-up question) 판단합니다.
    """
    if not history:
        return {'is_context_question': False}
    
    client = get_openai_client()
    
    # 최근 대화 요약
    history_str = "\n".join([f"Q: {h.get('query','')}\nA: {h.get('answer','')}..."[:200] for h in history[-2:]])
    
    system_prompt = """당신은 대화 흐름 분석가입니다. 
현재 질문이 이전 대화에서 언급된 특정 공고나 내용을 '참조'하고 있는지 판단하세요.
(예: "거기 위치가 어디야?", "자격 조건은?", "그 공고 언제 마감해?")

# 출력 형식 (JSON)
{
    "is_context_question": true 또는 false,
    "reason": "판단 근거 간략 서술",
    "referenced_announcement_indices": [0] (가장 최근 답변의 첫 번째 공고를 0으로 기준, 참조하는 공고 인덱스 리스트)
}
"""
    
    try:
        response = client.chat.completions.create(
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


# 3. 답변 생성 (Answer Generation)
def generate_answer(query: str, context: str, sources: List[Dict]) -> Dict:
    """
    검색된 문서(Context)를 바탕으로 사용자에게 최종 답변을 생성합니다.
    """
    client = get_openai_client()
    
    system_prompt = """당신은 LH(한국토지주택공사) 임대/분양 공고 전문 AI 상담원입니다.
제공된 [검색된 문서]의 내용에만 기반하여 사실대로 답변해야 합니다.

# 답변 가이드라인
1. **정확성**: 문서에 없는 내용은 절대 지어내지 말고 "공고문에서 확인할 수 없습니다"라고 하세요.
2. **구조화**: 가독성을 위해 불렛 포인트, 번호 매기기, 마크다운 표 등을 적극 활용하세요.
3. **출처 표기**: 답변의 근거가 되는 내용은 문장 끝이나 단락 끝에 [문서 1], [문서 2]와 같이 출처를 명시하세요.
4. **친절함**: 전문 용어는 쉽게 풀어서 설명하고, 정중한 어조를 사용하세요.
"""

    user_prompt = f"""# [검색된 문서]
{context}

# [사용자 질문]
{query}

위 문서를 바탕으로 질문에 대해 명확하고 도움이 되는 답변을 작성해주세요."""

    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.OPENAI_TEMPERATURE, # 창의성 조절 (보통 0.3~0.5)
            max_tokens=config.OPENAI_MAX_TOKENS
        )
        
        answer_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        return {
            'answer': answer_text,
            'sources': sources,
            'metadata': {
                'model': config.OPENAI_MODEL, 
                'tokens': tokens_used
            }
        }
        
    except Exception as e:
        return {
            'answer': f"죄송합니다. 답변을 생성하는 도중 오류가 발생했습니다.\n(오류 메시지: {str(e)})",
            'sources': sources,
            'metadata': {'error': str(e)}
        }