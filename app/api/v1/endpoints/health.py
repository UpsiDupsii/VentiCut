from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Health check")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }
