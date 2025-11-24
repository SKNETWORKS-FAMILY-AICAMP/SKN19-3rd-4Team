from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import asyncpg
from dependencies import get_db_config

# 라우터 객체 생성
router = APIRouter()

# 1. 응답 데이터 모델 (Schema) 정의
class StatsResponse(BaseModel):
    CNT_ALL: int = Field(..., description="전체 공고 수")
    CNT_NOTE_ING: int = Field(..., description="공고중인 건수")
    CNT_APP_ING: int = Field(..., description="접수중인 건수")
    CNT_ELSE: int = Field(..., description="그 외(마감 등) 건수")

# 2. 통계 정보 조회 API 엔드포인트
@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats():
    """
    공고 상태별 통계 정보를 반환합니다.
    (전체, 공고중, 접수중, 그 외)
    """
    # DB 설정 가져오기
    db_config = get_db_config()
    
    # DB 연결
    conn = await asyncpg.connect(**db_config)
    try:
        # 요청하신 SQL 쿼리 실행
        sql = """
            SELECT
                count(*) as "CNT_ALL",
                sum(CASE WHEN status = '공고중' THEN 1 ELSE 0 END) AS "CNT_NOTE_ING",
                sum(CASE WHEN status = '접수중' THEN 1 ELSE 0 END) AS "CNT_APP_ING",
                sum(CASE WHEN status NOT IN ('공고중','접수중') THEN 1 ELSE 0 END) as "CNT_ELSE"
            FROM public.announcements
        """
        
        row = await conn.fetchrow(sql)
        
        # 데이터가 없을 경우(테이블이 비어있을 때) 0으로 초기화하여 반환
        if not row:
            return {
                "CNT_ALL": 0,
                "CNT_NOTE_ING": 0, 
                "CNT_APP_ING": 0, 
                "CNT_ELSE": 0
            }
            
        # 결과를 딕셔너리로 변환하여 반환 (asyncpg.Record -> dict)
        return dict(row)

    except Exception as e:
        print(f"[Error] 통계 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
        
    finally:
        # 연결 종료
        await conn.close()