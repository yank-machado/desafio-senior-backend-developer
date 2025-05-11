from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from infrastucture.database.session import get_db

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}}
)

@router.get("/")
async def health_check():
    return {"status": "ok", "message": "API is running"}

@router.get("/db")
async def db_check(db: AsyncSession = Depends(get_db)):
    try:
        # Testar conexão com o banco de dados
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return {"status": "ok", "database": "connected"}
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "error", "database": "error"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "error", "message": f"Database error: {str(e)}"}
        ) 