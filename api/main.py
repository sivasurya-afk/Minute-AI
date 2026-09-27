import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes.auth_routes import router as auth_router
from api.routes.projects_routes import router as projects_router
from api.routes.transcripts_routes import router as transcripts_router
from api.routes.action_items_routes import router as action_items_router
from api.routes.dashboard_routes import router as dashboard_router
from api.routes.export_routes import router as export_router
from api.routes.settings_routes import router as settings_router

app = FastAPI(title="Minute AI API", version="2.0.0")

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(transcripts_router)
app.include_router(action_items_router)
app.include_router(dashboard_router)
app.include_router(export_router)
app.include_router(settings_router)

@app.get("/health")
def health():
    return {"status": "ok", "app": "Minute AI", "version": "2.0.0"}

# Serve frontend build if dist folder exists
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
