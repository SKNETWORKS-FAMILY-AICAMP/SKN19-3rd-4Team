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
현재 질문이 이전 대화와 어떤 관계인지 판단하세요.

# 질문 유형
1. **announcement_reference**: 이전에 언급된 특정 공고를 참조
   예: "거기 위치가 어디야?", "첫번째 공고 자세히 알려줘", "그 공고 자격조건은?"

2. **meta_conversation**: 대화 자체에 대한 질문 (검색 불필요)
   예: "아까 뭐라 했어?", "이전 질문 요약해줘", "내가 방금 뭐 물었지?"

3. **new_question**: 완전히 새로운 질문

# 출력 형식 (JSON)
{
    "is_context_question": true/false,
    "context_type": "announcement_reference" | "meta_conversation" | "new_question",
    "reason": "판단 근거",
    "referenced_announcement_indices": [0]
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
        history_items = [
            f"Q: {h.get('query', '')}\nA: {str(h.get('answer', ''))[:150]}..." 
            for h in conversation_history[-3:]
        ]
        history_text = "\n\n".join(history_items)
    
    system_prompt = """당신은 LH 공사의 전문 주택 상담사로, 사용자가 최적의 주택을 찾도록 돕는 역할을 합니다.

# 핵심 원칙
1. **정확성 우선**: 제공된 문서의 정보만 사용. 불확실하면 "공고문에서 확인되지 않습니다"라고 명시
2. **사용자 중심**: 질문 의도를 파악하여 필요한 정보를 선제적으로 제공
3. **명확한 구조화**: 복잡한 정보는 표, 리스트, 단계별로 정리
4. **친절한 설명**: 전문 용어는 이해하기 쉽게 풀어서 설명
5. **맥락 활용**: 이전 대화를 고려하여 일관성 있게 답변

# 답변 형식 (반드시 준수)

## 유형 A: 일반 질문 (자격, 일정, 신청방법 등)
질문에 대한 직접적인 답변을 제공하고, 필요한 세부 정보를 추가합니다.

## 유형 B: 여러 공고 나열 요청 (예: "최신 공고 5개", "경기도 공고 찾아줘")
**반드시 아래 형식으로만 작성:**

찾으신 조건에 맞는 공고는 다음과 같습니다.

### [공고 1 제목]
- **지역**: [지역명]
- **유형**: [주택 유형]
- **공고일**: [날짜 또는 "정보 없음"]
- **링크**: [공고 URL]

### [공고 2 제목]
- **지역**: [지역명]
- **유형**: [주택 유형]
- **공고일**: [날짜 또는 "정보 없음"]
- **링크**: [공고 URL]

(이하 동일 형식 반복)

---
**참조 공고**
1. [공고 1 제목](URL)
2. [공고 2 제목](URL)

# 특수 상황 처리
- **대화 맥락 질문** (예: "아까 뭐라했어?"): 이전 대화 내역을 참고하여 친절하게 답변
- **LH 무관 질문** (예: "날씨 어때?"): "죄송합니다. LH 주택 공고 관련 질문에만 답변드릴 수 있습니다."
- **정보 부족**: "제공된 공고에서 해당 정보를 확인할 수 없습니다. LH 고객센터(1600-1004)로 문의하시면 정확한 안내를 받으실 수 있습니다."

# 스타일 가이드
- 존댓말 사용 ("~입니다", "~하세요")
- 중요한 날짜/금액/조건: **굵게 강조**
- 복잡한 비교: 마크다운 표 사용
- 단계별 절차: 번호 목록 사용"""
    
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