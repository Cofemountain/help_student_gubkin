import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.endpoints import router as api_router
from app.core.config import settings
from scripts.seed_oge_topics import seed_topics
from scripts.seed_bank_tasks import seed_bank_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения инициализируем БД и наполняем кодификатор тем ОГЭ и банк задач
    await seed_topics()
    await seed_bank_tasks()
    yield


app = FastAPI(
    title="ОГЭ Физика (9 класс) — API Взаимопомощи",
    description="Backend API и Mini App для российского мессенджера МАКС",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роуты
app.include_router(api_router)

# Раздача загруженных медиа (фото задач и решений)
uploads_dir = Path(__file__).resolve().parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}

# Раздача фронтенда (blobs-front/dist)
dist_dir = Path(__file__).resolve().parent / "blobs-front" / "dist"
if dist_dir.exists():
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", summary="Главная страница Mini App")
    async def serve_root():
        return FileResponse(dist_dir / "index.html", headers=NO_CACHE_HEADERS)

    @app.get("/favicon.svg")
    async def favicon():
        fav = dist_dir / "favicon.svg"
        if fav.exists():
            return FileResponse(fav)
        raise HTTPException(status_code=404)

    # SPA fallback для всех клиентских маршрутов Vue Router (/bank, /achievements, /login, /requests)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if (
            full_path.startswith("api")
            or full_path.startswith("docs")
            or full_path.startswith("openapi.json")
            or full_path.startswith("redoc")
        ):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = dist_dir / full_path
        if full_path and target_file.is_file():
            if target_file.suffix == ".html":
                return FileResponse(target_file, headers=NO_CACHE_HEADERS)
            return FileResponse(target_file)
        return FileResponse(dist_dir / "index.html", headers=NO_CACHE_HEADERS)
else:
    @app.get("/", summary="Healthcheck")
    async def root():
        return {
            "status": "ok",
            "service": "OGE Physics 9th Grade API",
            "docs": "/docs",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
