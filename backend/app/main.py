from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, cases, copilot, findings, reports, risk, traces
from app.config import settings
from app.services.auth.deps import require_auth

app = FastAPI(
    title="LedgerLens API",
    description="Blockchain intelligence workstation for cryptocurrency fraud investigation",
    version="0.4.0",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

_protected = [Depends(require_auth)]

app.include_router(auth.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1", dependencies=_protected)
app.include_router(traces.router, prefix="/api/v1", dependencies=_protected)
app.include_router(risk.router, prefix="/api/v1", dependencies=_protected)
app.include_router(copilot.router, prefix="/api/v1", dependencies=_protected)
app.include_router(findings.router, prefix="/api/v1", dependencies=_protected)
app.include_router(reports.router, prefix="/api/v1", dependencies=_protected)

@app.get("/")
async def root():
    return {
        "service": "LedgerLens API",
        "version": "0.4.0",
        "phase": "Phase 5 - AI Copilot",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
