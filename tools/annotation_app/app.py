"""Local-only annotation queue API with explicit annotator IDs and adjudication."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from training.common import ROOT, read_jsonl, write_jsonl

DATA_ROOT = (ROOT / "data/annotations").resolve()
DATA_ROOT.mkdir(parents=True, exist_ok=True)


class Annotation(BaseModel):
    annotation_id: str = Field(pattern=r"^[A-Za-z0-9_.:-]{1,100}$")
    annotator_id: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,50}$")
    label: Literal["STRONG_MATCH", "POTENTIAL_MATCH", "WEAK_MATCH", "NOT_MATCH"]
    evidence: list[str] = Field(min_length=1, max_length=20)
    notes: str = Field(default="", max_length=2000)


app = FastAPI(title="SkillMap local annotation tool", docs_url="/docs")


def _file(name: str) -> Path:
    target = (DATA_ROOT / name).resolve()
    if DATA_ROOT not in target.parents or target.suffix != ".jsonl":
        raise HTTPException(400, "invalid annotation file")
    return target


@app.get("/queue")
def queue() -> list[dict]:
    return read_jsonl(_file("review_queue.jsonl"))[:1000]


@app.post("/annotations")
def save(annotation: Annotation) -> dict[str, bool]:
    path = _file(f"annotations-{annotation.annotator_id}.jsonl")
    rows = {row["annotation_id"]: row for row in read_jsonl(path)}
    rows[annotation.annotation_id] = annotation.model_dump(mode="json")
    write_jsonl(path, rows.values())
    return {"saved": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "localhost"])
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
