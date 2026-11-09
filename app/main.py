from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure storage and assets directories exist
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    Path("assets").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Video RePurposing Pipeline - Transform long videos into viral shorts and reels.",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for frontend clients and dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset directory for logo and branding
if Path("assets").exists():
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Mount React bundled distribution assets
dist_assets = Path("app/static/dist/app-assets")
dist_assets.mkdir(parents=True, exist_ok=True)
app.mount("/app-assets", StaticFiles(directory=str(dist_assets)), name="app-assets")

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["UI"])
def serve_ui():
    dist_index = Path("app/static/dist/index.html")
    if dist_index.exists():
        return FileResponse(dist_index)
    index_file = Path("app/static/index.html")
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health",
    }


@app.get("/api", tags=["Root"])
def root_api():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
