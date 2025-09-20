"""
Development version of main application with mock services.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Import configuration
from src.config_dev import dev_settings

# Set environment variable for mock mode
os.environ["USE_MOCK_OPENAI"] = "true"
os.environ["DEBUG"] = "true"

# Import routes and middleware
from src.shared.middleware import LoggingMiddleware
from src.shared.routes import health_router
from src.auth.routes import auth_router
from src.tenants.routes import tenants_router
from src.requirements.routes import router as requirements_router
from src.ai.routes import router as ai_router
from src.web.routes import web_router

# Import enhanced routes
try:
    from src.requirements.advanced_routes import router as advanced_router
except ImportError:
    print("Advanced routes not available, skipping...")
    advanced_router = None

app = FastAPI(
    title="Requirements Management System (Development)",
    description="Enhanced requirements management with AI assistance - Development Mode",
    version="2.0.0-dev",
    debug=True
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(auth_router, prefix="/api", tags=["authentication"])
app.include_router(tenants_router, prefix="/api/tenants", tags=["tenants"])
app.include_router(requirements_router, prefix="/api/requirements", tags=["requirements"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(web_router, tags=["web"])

# Include enhanced routes if available
if advanced_router:
    app.include_router(advanced_router)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint serving the main dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Requirements Management System - Development",
            "debug_mode": True,
            "mock_ai": True
        }
    )


@app.get("/health/dev")
async def dev_health_check():
    """Development health check with enhanced information."""
    return {
        "status": "healthy",
        "environment": "development",
        "features": {
            "mock_openai": dev_settings.use_mock_openai,
            "debug": dev_settings.debug,
            "enhanced_features": advanced_router is not None
        },
        "services": {
            "database": "sqlite" if "sqlite" in str(dev_settings.database_url) else "postgresql",
            "redis": "disabled" if not dev_settings.redis_url else "enabled",
            "ai_service": "mock" if dev_settings.use_mock_openai else "openai"
        }
    }


@app.get("/mock/openai/status")
async def mock_openai_status():
    """Check mock OpenAI service status."""
    if dev_settings.use_mock_openai:
        from src.ai.mock_openai_service import get_mock_openai_service
        mock_service = get_mock_openai_service()
        return {
            "mock_enabled": True,
            "stats": mock_service.get_usage_stats()
        }
    else:
        return {"mock_enabled": False}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main_dev:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="debug"
    )