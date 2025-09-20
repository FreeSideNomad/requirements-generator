"""
Simplified FastAPI application for testing without database dependencies.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI(
    title="Requirements Generator",
    version="1.0.0",
    description="AI-powered requirements gathering platform"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Requirements Generator API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Simple health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/auth/status")
async def auth_status():
    """Auth status placeholder."""
    return {"message": "Authentication will be implemented in Stage 2"}


@app.get("/api/tenants/status")
async def tenants_status():
    """Tenants status placeholder."""
    return {"message": "Tenant management will be implemented in Stage 2"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)