import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_full_features():
    print("🚀 [통합 테스트] 세션 + 스트리밍 시작\n")

    # 1. 세션 생성
    try:
        resp = requests.post(f"{BASE_URL}/sessions")
        session_id = resp.json()['session_id']
        print(f"✅ 세션 생성 성공: {session_id}")
    except Exception as e:
        print("❌ 서버 연결 실패:", e)
        return

    # 2. 일반 대화 (Non-streaming)
    print("\n[Step 1] 일반 대화 테스트")
    query1 = "남양주시 국민임대주택 알려줘"
    print(f"👤 질문: {query1}")
    
    resp1 = requests.post(
        f"{BASE_URL}/sessions/{session_id}/chat",
        json={"query": query1}
    )
    if resp1.status_code == 200:
        print(f"🤖 답변: {resp1.json()['answer'][:50]}... (생략)")
    else:
        print("❌ 에러:", resp1.text)

    # 3. 스트리밍 대화 (Streaming) + 맥락 테스트
    print("\n[Step 2] 스트리밍 + 맥락 테스트")
    query2 = "거기 자격 조건은 어떻게 돼?"
    print(f"👤 질문: {query2}")
    print("🤖 답변(스트리밍): ", end="", flush=True)

    resp2 = requests.post(
        f"{BASE_URL}/sessions/{session_id}/stream",
        json={"query": query2},
        stream=True  # 필수
    )

    for line in resp2.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8'))
                if data['type'] == 'answer':
                    print(data['content'], end="", flush=True)
                elif data['type'] == 'error':
                    print(f"\n[Server Error] {data['content']}")
            except:
                pass
    print("\n\n✅ 테스트 완료")

if __name__ == "__main__":
    test_full_features()