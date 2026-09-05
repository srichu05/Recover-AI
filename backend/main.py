from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.config import settings, DATA_DIR
from backend.api import router as api_router
from backend.storage import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure data directory exists and seed data is ready
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    print(f"Data directory: {DATA_DIR}")
    print(f"Deterministic seed: {settings.DEFAULT_RANDOM_SEED}")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title="RecoverAI API",
    description="Autonomous AI Revenue Recovery Engine for Track 03 (Razorpay Buildathon)",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router)

# Mount frontend build if available
frontend_dist = DATA_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "track": "Razorpay Buildathon Track 03 — AI Revenue Recovery",
            "documentation": "/docs",
            "api_health": "/api/health"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
