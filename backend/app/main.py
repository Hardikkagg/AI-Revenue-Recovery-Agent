"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.agent import recovery_agent
from app.agent.detector import InvalidEventError, UnsupportedEventTypeError
from app.agent.schemas import AnalysisResult, RecoveryEventInput
from app.config import settings
from app.database import get_db, init_db
from app.simulation import RecoverySimulationResponse, simulation_engine


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


@app.post("/recovery/simulate", response_model=RecoverySimulationResponse)
def simulate_recovery(
    event: RecoveryEventInput,
    db: Session = Depends(get_db),
) -> RecoverySimulationResponse:
    """Run complete pipeline: detect → diagnose → score → choose strategy → simulate execution → observe outcome."""
    try:
        analysis = recovery_agent.analyze(event)
        simulation_res = simulation_engine.execute(analysis, db=db)
        return RecoverySimulationResponse(
            analysis=analysis,
            simulation=simulation_res,
        )
    except UnsupportedEventTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidEventError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

