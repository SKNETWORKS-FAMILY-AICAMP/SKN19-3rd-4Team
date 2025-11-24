import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_stateless():
    print("🚀 [기본 테스트] History 수동 관리\n")

    history = []

    # 1. 첫 번째 질문
    query1 = "경기도 영구임대주택 리스트 줘"
    print(f"👤 질문 1: {query1}")
    
    resp1 = requests.post(
        f"{BASE_URL}/chat",
        json={"query": query1, "history": history} # 빈 history 전송
    )
    result1 = resp1.json()
    print(f"🤖 답변 1: {result1['answer'][:50]}...")

    # [중요] 응답을 History에 수동으로 추가
    history.append({"query": query1, "answer": result1['answer'], "sources": result1['sources']})

    # 2. 두 번째 질문
    query2 = "가장 최근 공고 하나만 자세히 알려줘"
    print(f"\n👤 질문 2: {query2}")
    
    resp2 = requests.post(
        f"{BASE_URL}/chat",
        json={"query": query2, "history": history} # 업데이트된 history 전송
    )
    print(f"🤖 답변 2: {resp2.json()['answer']}")

if __name__ == "__main__":
    test_stateless()