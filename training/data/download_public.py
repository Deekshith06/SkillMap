"""Download only registry-approved public datasets with immutable receipts."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from training.common import ROOT, resolve, sha256, write_json

REGISTRY = ROOT / "data/manifests/dataset_registry.yaml"
RECEIPTS = ROOT / "data/manifests/download_receipts.json"


def _safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as handle:
        for member in handle.infolist():
            target = (destination / member.filename).resolve()
            if destination.resolve() not in target.parents and target != destination.resolve():
                raise ValueError(f"unsafe archive path: {member.filename}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with handle.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def run(datasets: list[str] | None = None, *, dry_run: bool = False) -> dict[str, Any]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["datasets"]
    selected = [
        item
        for item in registry
        if item["approved_for_training"] and (not datasets or item["name"] in datasets)
    ]
    previous = json.loads(RECEIPTS.read_text(encoding="utf-8")) if RECEIPTS.exists() else {}
    receipts = dict(previous)
    actions = []
    for item in selected:
        if item["synthetic"] and str(item["source"]).startswith("training."):
            actions.append({"dataset": item["name"], "status": "generated_locally"})
            continue
        url = os.getenv("SKILLMAP_ESCO_URL") if item["name"] == "esco" else item["download_url"]
        if not url:
            actions.append({"dataset": item["name"], "status": "manual_url_required"})
            continue
        if urlparse(url).scheme != "https":
            raise ValueError(f"dataset URL must use HTTPS: {item['name']}")
        destination = resolve(item["local_path"])
        archive = destination.parent / f"{item['name']}-{item['version']}.zip"
        if dry_run:
            actions.append({"dataset": item["name"], "status": "planned", "url": url})
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            request = urllib.request.Request(
                url, headers={"User-Agent": "SkillMap-dataset-audit/1"}
            )
            with (
                urllib.request.urlopen(request, timeout=120) as response,  # nosec B310
                archive.open("wb") as out,
            ):
                shutil.copyfileobj(response, out)
        digest = sha256(archive)
        expected = item["sha256"] or previous.get(item["name"], {}).get("sha256")
        if expected and digest != expected:
            raise ValueError(f"hash changed for {item['name']}: expected {expected}, got {digest}")
        if not destination.exists():
            _safe_extract(archive, destination)
        receipts[item["name"]] = {
            "version": item["version"],
            "url": url,
            "archive": str(archive.relative_to(ROOT)),
            "sha256": digest,
        }
        actions.append({"dataset": item["name"], "status": "downloaded", "sha256": digest})
    if not dry_run:
        write_json(RECEIPTS, receipts)
    return {"actions": actions}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", action="append", dest="datasets")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.datasets, dry_run=args.dry_run), indent=2))


if __name__ == "__main__":
    main()
