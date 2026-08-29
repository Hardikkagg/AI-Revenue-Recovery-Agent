"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.agent import recovery_agent
from app.agent.detector import InvalidEventError, UnsupportedEventTypeError
from app.agent.schemas import AnalysisResult, RecoveryEventInput
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables on startup."""
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a simple health check response."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "message": "API is running",
    }


@app.post("/recovery/analyze", response_model=AnalysisResult)
def analyze_recovery(event: RecoveryEventInput) -> AnalysisResult:
    """Run detect → diagnose → score → choose strategy. Does not execute actions."""
    try:
        return recovery_agent.analyze(event)
    except UnsupportedEventTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidEventError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
