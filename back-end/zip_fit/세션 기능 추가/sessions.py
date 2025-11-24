import uuid
from typing import List, Dict, Any
from collections import defaultdict
import time

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._last_access: Dict[str, float] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        self._last_access[session_id] = time.time()
        return session_id

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        self._last_access[session_id] = time.time()
        return self._sessions.get(session_id, [])

    def add_message(self, session_id: str, query: str, answer: str, sources: List[Any]):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        self._sessions[session_id].append({
            "query": query,
            "answer": answer,
            "sources": sources,
            "timestamp": time.time()
        })
        
        if len(self._sessions[session_id]) > 10:
            self._sessions[session_id].pop(0)
            
    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

session_store = SessionManager()