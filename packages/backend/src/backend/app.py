from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router as matches_router

app = FastAPI(
    title="WELS — Handball Analytics API",
    version="0.1.0",
    description="Backend API for handball match analysis, video ingestion, and action prediction.",
)

app.include_router(matches_router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
