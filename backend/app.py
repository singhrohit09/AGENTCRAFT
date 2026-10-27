"""
AgentCraft Backend FastAPI Application
Serves the autonomous AI agent API, WebSocket/REST endpoints,
benchmark evaluation suite, and CORS-enabled microservices.
"""

import os
import sys
import time
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Load environment configuration
load_dotenv(dotenv_path=REPO_ROOT / ".env")

from backend.routes.agent_routes import router as agent_router
from backend.routes.rakshagrid_routes import router as rakshagrid_router
from backend.routes.incident_routes import router as incident_router
from backend.routes.coordination_routes import router as coordination_router
from backend.routes.intelligence_routes import router as intelligence_router
from backend.routes.alert_routes import router as alert_router
from backend.services.agent_service import agent_service

app = FastAPI(
    title="AgentCraft & RakshaGrid API",
    description="Unified API for AgentCraft AI Engine and RakshaGrid Disaster Intelligence & Response Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Register route modules
app.include_router(agent_router)
app.include_router(rakshagrid_router)
app.include_router(incident_router)
app.include_router(coordination_router)
app.include_router(intelligence_router)
app.include_router(alert_router)

APP_START_TIME = time.time()

# Serve built frontend if dist exists
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/", tags=["Root"])
def root_status():
    """AgentCraft & RakshaGrid API Root Information."""
    return {
        "project": "AgentCraft",
        "subsystem": "RakshaGrid",
        "competition": "AGENTCRAFT 2026 National AI Agent Challenge",
        "status": "online",
        "version": "2.0.0",
        "docs": "/docs",
        "agentcraft_health": "/api/health",
        "rakshagrid_health": "/api/rakshagrid/health",
        "rakshagrid_overview": "/api/rakshagrid/overview",
        "incidents_v1": "/api/v1/incidents",
        "teams_v1": "/api/v1/teams",
        "tasks_v1": "/api/v1/tasks",
        "shelters_v1": "/api/v1/shelters",
        "resources_v1": "/api/v1/resources",
        "intelligence_v1": "/api/v1/intelligence",
        "alerts_v1": "/api/v1/alerts",
    }


@app.get("/api/health", tags=["System"])
def health_check():
    """System health check and diagnostic telemetry."""
    uptime_seconds = time.time() - APP_START_TIME
    tools = agent_service.get_registered_tools()
    sessions = agent_service.list_sessions()

    return {
        "status": "healthy",
        "service": "AgentCraft",
        "uptime_seconds": round(uptime_seconds, 2),
        "python_version": sys.version.split()[0],
        "registered_tools_count": len(tools),
        "active_sessions_count": len(sessions),
        "environment": os.getenv("AGENTCRAFT_ENV", "development"),
        "execution_mode": os.getenv("AGENTCRAFT_EXECUTION_MODE", "hybrid"),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global structured JSON error handler for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": str(exc),
            "path": str(request.url.path),
        },
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("AGENTCRAFT_HOST", "127.0.0.1")
    port = int(os.getenv("AGENTCRAFT_PORT", "8000"))
    reload = os.getenv("AGENTCRAFT_DEBUG", "true").lower() == "true"
    print(f"Starting AgentCraft API server on http://{host}:{port} ...")
    uvicorn.run("backend.app:app", host=host, port=port, reload=reload)
