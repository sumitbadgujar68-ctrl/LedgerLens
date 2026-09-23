from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import cases

app = FastAPI(
    title="LedgerLens API",
    description="Blockchain intelligence workstation for cryptocurrency fraud investigation",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "LedgerLens API",
        "version": "0.1.0",
        "phase": "Phase 1 - Case Foundation",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
