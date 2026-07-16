"""Small shared utilities for offline pipeline commands."""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: str | Path) -> dict[str, Any]:
    """Load JSON-compatible YAML without adding a YAML runtime dependency."""

    config_path = (ROOT / path).resolve() if not Path(path).is_absolute() else Path(path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["_path"] = str(config_path)
    return config


def resolve(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(*parts: object) -> str:
    value = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(value.encode()).hexdigest()[:20]


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    source = resolve(path)
    if not source.exists():
        return []
    rows = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {source}:{line_number}") from exc
    return rows


def write_json(path: str | Path, value: Any) -> Path:
    target = resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> Path:
    target = resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )
    return target


def seed_everything(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass


def git_commit() -> str:
    git_dir = ROOT / ".git"
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref: "):
            return head
        ref = head.removeprefix("ref: ")
        loose = git_dir / ref
        if loose.exists():
            return loose.read_text(encoding="utf-8").strip()
        for line in (git_dir / "packed-refs").read_text(encoding="utf-8").splitlines():
            if line and not line.startswith(("#", "^")) and line.endswith(f" {ref}"):
                return line.split()[0]
    except OSError:
        pass
    return "unknown"


def run_metadata(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "config": str(config.get("_path", "")),
        "config_sha256": hashlib.sha256(
            json.dumps({k: v for k, v in config.items() if k != "_path"}, sort_keys=True).encode()
        ).hexdigest(),
        "git_commit": git_commit(),
        "python": sys.version,
        "seed": config.get("seed", 42),
    }
