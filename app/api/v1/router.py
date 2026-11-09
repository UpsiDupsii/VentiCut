from fastapi import APIRouter

from app.api.v1.endpoints import admin, clips, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(clips.router, prefix="/clips", tags=["Clips"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
