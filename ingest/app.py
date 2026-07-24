"""FastAPI service exposing the ask flow over HTTP."""

from __future__ import annotations

from contextlib import asynccontextmanager

import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .claude_client import AnthropicClaudeClient
from .embedder import OllamaEmbedder
from .service import answer_question

CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "anchor"

clients: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    clients["embedder"] = OllamaEmbedder()
    clients["collection"] = chroma.get_or_create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )
    clients["claude"] = AnthropicClaudeClient()
    yield
    clients.clear()


app = FastAPI(title="Anchor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    detailed: bool = False


class AskResponse(BaseModel):
    answer: str
    is_refusal: bool
    sources: list[str]
    is_confident: bool
    best_distance: float | None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        result = answer_question(
            request.question,
            clients["embedder"],
            clients["collection"],
            clients["claude"],
            detailed=request.detailed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AskResponse(
        answer=result.answer,
        is_refusal=result.is_refusal,
        sources=result.sources,
        is_confident=result.is_confident,
        best_distance=result.best_distance,
    )