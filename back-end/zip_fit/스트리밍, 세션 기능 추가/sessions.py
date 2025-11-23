import uuid
from typing import List, Dict, Any
from collections import defaultdict
import time
import json


class SessionManager:
    def __init__(self):
        # 메모리 저장소: { "session_id": [ {대화1}, {대화2} ... ] }
        self._sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._last_access: Dict[str, float] = {}

    def create_session(self) -> str:
        """새로운 세션 ID 생성"""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        self._last_access[session_id] = time.time()
        return session_id

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """세션의 대화 내역 반환"""
        self._last_access[session_id] = time.time()
        return self._sessions.get(session_id, [])

    def add_message(self, session_id: str, query: str, answer: str, sources: List[Any]):
        """대화 내용 저장"""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            
        self._sessions[session_id].append({
            "query": query,
            "answer": answer,
            "sources": sources,
            "timestamp": time.time()
        })
        self._last_access[session_id] = time.time()
        
        # 대화 내역이 너무 길어지면 자르기 (최근 10턴 유지)
        if len(self._sessions[session_id]) > 10:
            self._sessions[session_id].pop(0)

    def clear_session(self, session_id: str):
        """세션 삭제"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._last_access:
            del self._last_access[session_id]

# 전역 인스턴스 생성
session_store = SessionManager()