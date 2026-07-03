from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    PROJECT_ROOT,
    get_model_name,
    get_search_model_name,
    has_openai_api_key,
    save_openai_api_key,
)
from .orchestrator import process_research_question
from .schemas import ApiKeyRequest, ConfigStatus, ResearchRequest, ResearchRun


app = FastAPI(title="Multi-agentni vyzkumny asistent")
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "static" / "index.html")


@app.get("/api/config", response_model=ConfigStatus)
def config_status() -> ConfigStatus:
    return ConfigStatus(
        has_openai_api_key=has_openai_api_key(),
        model=get_model_name(),
        search_model=get_search_model_name(),
    )


@app.post("/api/config/openai-key")
def save_key(payload: ApiKeyRequest) -> dict[str, bool]:
    try:
        save_openai_api_key(payload.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"saved": True}


@app.post("/api/research", response_model=ResearchRun)
def run_research(payload: ResearchRequest) -> ResearchRun:
    if not has_openai_api_key():
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is missing.")
    try:
        return process_research_question(payload.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

