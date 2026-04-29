import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router as matches_router
from backend.routes.upload import router as upload_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="WELS — Handball Analytics API",
    version="0.1.0",
    description="Backend API for handball match analysis, video ingestion, and action prediction.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matches_router)
app.include_router(upload_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
