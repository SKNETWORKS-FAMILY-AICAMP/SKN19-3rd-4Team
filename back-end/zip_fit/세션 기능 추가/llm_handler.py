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
    
    context_info = ""
    context_analysis = None
    
    if conversation_history:
        context_prompt = f"""대화 기록:
{conversation_history}

현재 질문: "{query}"

이 질문이 이전 대화를 참조하는지 판단하고, 참조한다면 어떤 공고를 언급하는지 분석해주세요.
JSON 형식으로만 답변:
{{
  "is_followup": true/false,
  "referenced_announcement_ids": ["공고ID1", "공고ID2"],
  "context_type": "specific_announcement/general_topic/new_question"
}}"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": context_prompt}],
            temperature=0
        )
        
        try:
            context_analysis = json.loads(response.choices[0].message.content)
            if context_analysis.get('is_followup') and context_analysis.get('referenced_announcement_ids'):
                context_info = f"이전 대화에서 언급된 공고: {', '.join(context_analysis['referenced_announcement_ids'])}"
        except json.JSONDecodeError:
            context_analysis = None
    
    rewrite_prompt = f"""질문을 분석하여 다음 정보를 추출:

질문: "{query}"
{context_info}

추출 규칙:
1. region: "경기도", "서울특별시", "서울특별시 외" 중 하나만 (수원시→검색키워드로)
2. notice_type: 국민임대/행복주택/영구임대 등 (명시되지 않으면 빈 문자열)
3. category: "lease"(임대) 또는 "sale"(분양) 또는 빈 문자열 (명시되지 않으면 빈 문자열)
4. rewritten_question: 검색용 자연어 질문
5. search_keywords: 핵심 검색어 (도시명, 지역명 포함)

중요: category는 반드시 "lease", "sale", "" 중 하나만 사용. "주택유형" 같은 값 금지

JSON 형식으로만 답변:
{{
  "region": "",
  "notice_type": "",
  "category": "",
  "rewritten_question": "",
  "search_keywords": []
}}"""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": rewrite_prompt}],
        temperature=0
    )
    
    try:
        result = json.loads(response.choices[0].message.content)
        
        # category 값 검증 및 정규화
        # category에 lease, sale, 빈문자열 아닌 경우 where절 결과로 아무것도 안나옴
        if result.get('category') and result['category'] not in ['lease', 'sale']:
            result['category'] = ''
            
    except json.JSONDecodeError:
        result = {
            "region": "",
            "notice_type": "",
            "category": "",
            "rewritten_question": query,
            "search_keywords": query.split()
        }
    
    if context_analysis:
        result['context_analysis'] = context_analysis
    return result

async def generate_multi_queries(query: str, base_query_analysis: Dict, num_queries: int = 2) -> List[str]:
    client = get_openai_client()
    base_question = base_query_analysis.get('rewritten_question', query)

    multi_query_prompt = f"""LH 주택 공고 검색을 위해 질문을 다양한 표현으로 변환하세요.

원본 질문: {base_question}

다음 {num_queries}개의 다른 버전을 생성하세요:
1. 동의어나 유사 표현을 사용한 버전
2. 더 구체적이거나 상세한 버전

규칙:
- 각 질문은 한 줄에 하나씩
- 번호나 기호 없이 질문만
- 원본 질문의 의도 유지
- LH, 임대주택, 분양주택 관련 용어 활용

변환된 질문들:"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": multi_query_prompt}],
        temperature=0.7
    )

    generated = [q.strip() for q in response.choices[0].message.content.strip().split('\n') if q.strip()]
    all_queries = [base_question] + generated[:num_queries]

    return all_queries

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
async def generate_answer(query: str, context: str, conversation_history: List[Dict] = None) -> str:
    client = get_openai_client()
    history_text = ""
    if conversation_history:
        history_items = [f"Q: {h['question']}\nA: {h['answer'][:150]}..." for h in conversation_history[-3:]]
        history_text = "\n\n".join(history_items)
    
    system_prompt = """LH 공사의 임대/분양 공고 전문 상담사입니다.

# 답변 원칙
1. **정확성**: 제공된 문서만을 근거로 답변. 문서에 없는 내용은 "제공된 공고에서 확인할 수 없습니다" 명시
2. **구체성**: 숫자, 날짜, 조건을 정확히 인용. 표가 있으면 마크다운 표로 정리
3. **완전성**: 질문과 관련된 모든 중요 정보(자격, 일정, 서류, 주의사항) 포함
4. **명확성**: 복잡한 조건은 단계별로 나누어 설명
5. **친절함**: 전문 용어는 쉽게 풀어 설명

# 답변 형식
- 공고 제목, 지역, 유형 명시
- 중요한 날짜/금액/조건은 **강조**
- 여러 항목은 번호 목록이나 표로 정리
- 답변 끝에 [공고 1, 2 참조] 형태로 출처 표시

# 질문 유형별 대응
- 자격/조건 질문: 구체적 기준(소득, 나이, 거주지 등)을 상세히 나열
- 일정 질문: 모든 날짜(공고일, 접수기간, 발표일, 계약일)를 시간순 정리
- 신청 방법: 단계별 절차와 필요 서류를 목록으로 정리
- 비용 질문: 정확한 금액을 표로 정리
- 비교 질문: 차이점을 표로 정리"""
    
    user_prompt = f"""# 제공된 문서

{context}

# 이전 대화
{history_text if history_text else '없음'}

# 사용자 질문
{query}

위 문서를 바탕으로 정확하게 답변해주세요. 문서에 없는 내용은 추측하지 마세요."""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=2000
    )
    
    return response.choices[0].message.content