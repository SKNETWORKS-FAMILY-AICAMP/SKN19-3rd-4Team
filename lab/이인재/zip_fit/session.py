from typing import List, Dict, Any
import asyncio

# 메모리 저장소
_MEMORY_DB: Dict[str, List[Dict[str, str]]] = {}
_db_lock = asyncio.Lock()

# 대화 기억 갯수 제한 (너무 길어지면 토큰 비용 증가)
MAX_HISTORY_TURNS = 10 

async def get_history(user_id: int) -> List[Dict[str, str]]:
    """
    사용자 ID에 해당하는 대화 기록을 반환합니다.
    반환 형식: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    session_key = str(user_id)
    async with _db_lock:
        return _MEMORY_DB.get(session_key, []).copy()

async def add_turn(user_id: int, user_query: str, ai_response: str):
    """
    대화 한 턴(질문+답변)을 저장합니다.
    """
    session_key = str(user_id)
    async with _db_lock:
        if session_key not in _MEMORY_DB:
            _MEMORY_DB[session_key] = []
        
        # 기록 추가
        _MEMORY_DB[session_key].append({"role": "user", "content": user_query})
        _MEMORY_DB[session_key].append({"role": "assistant", "content": ai_response})
        
        # 오래된 기록 삭제 (Windowing)
        if len(_MEMORY_DB[session_key]) > MAX_HISTORY_TURNS:
            _MEMORY_DB[session_key] = _MEMORY_DB[session_key][-MAX_HISTORY_TURNS:]

async def clear_history(user_id: int):
    """
    대화 기록 초기화
    """
    session_key = str(user_id)
    async with _db_lock:
        if session_key in _MEMORY_DB:
            del _MEMORY_DB[session_key]