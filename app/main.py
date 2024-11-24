# app/main.py
import signal
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .config import settings
from .api.endpoints import auth, users, words, learning
from .database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"]
)

app.include_router(
    words.router,
    prefix=f"{settings.API_V1_STR}/words",
    tags=["words"]
)

app.include_router(
    learning.router,
    prefix=f"{settings.API_V1_STR}/learning",
    tags=["learning"]
)
def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}
@app.get("/routes")
async def get_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods
        })
    return routes
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_includes=["*.py", "*.html"],
        log_level="info"
    )