import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_session_only():
    print("🚀 [세션 테스트] 맥락 기억 확인\n")

    # 1. 세션 생성
    resp = requests.post(f"{BASE_URL}/sessions")
    session_id = resp.json()['session_id']
    print(f"✅ 세션 ID: {session_id}")

    # 2. 첫 번째 질문
    query1 = "수원시 행복주택 공고 찾아줘"
    print(f"\n👤 질문 1: {query1}")
    resp1 = requests.post(
        f"{BASE_URL}/sessions/{session_id}/chat",
        json={"query": query1}
    )
    print(f"🤖 답변 1: {resp1.json()['answer']}")

    # 3. 두 번째 질문 (맥락)
    # '거기'가 '수원시 행복주택'을 의미하는지 확인
    query2 = "거기 임대료가 보통 얼마야?"
    print(f"\n👤 질문 2: {query2}")
    resp2 = requests.post(
        f"{BASE_URL}/sessions/{session_id}/chat",
        json={"query": query2}
    )
    print(f"🤖 답변 2: {resp2.json()['answer']}")

if __name__ == "__main__":
    test_session_only()