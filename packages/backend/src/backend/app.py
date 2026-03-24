from fastapi import FastAPI

from backend.routes import router as matches_router

app = FastAPI(
    title="WELS — Handball Analytics API",
    version="0.1.0",
    description="Backend API for handball match analysis, video ingestion, and action prediction.",
)

app.include_router(matches_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
