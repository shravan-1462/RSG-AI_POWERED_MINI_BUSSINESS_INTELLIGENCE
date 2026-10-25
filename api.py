"""Small FastAPI wrapper around the same safe analytics service."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from db import ensure_db, answer_question, metrics

app = FastAPI(title="Mini AI BI Assistant API", version="1.0.0")

class Question(BaseModel):
    question: str = Field(min_length=1, max_length=500)

@app.on_event("startup")
def startup():
    # Respect whichever dataset is currently active in SQLite; don't overwrite uploads.
    ensure_db()

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/metrics")
def get_metrics():
    return metrics()

@app.post("/ask")
def ask(body: Question):
    result = answer_question(body.question)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result)
    return result
