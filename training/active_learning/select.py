"""Select uncertain, rare, and textually diverse examples for review."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from typing import Any

from training.common import read_jsonl, stable_id, write_jsonl


def _fingerprint(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.]{3,}", text.lower()))


def run(input_path: str, output_path: str, count: int) -> list[dict[str, Any]]:
    rows = read_jsonl(input_path)
    occupations = Counter(str(row.get("occupation", "unknown")) for row in rows)
    ranked = []
    for row in rows:
        probability = float(row.get("probability", row.get("final_score", 50) / 100))
        uncertainty = 1 - abs(probability - 0.5) * 2
        rarity = 1 / max(occupations[str(row.get("occupation", "unknown"))], 1)
        ranked.append(
            (
                0.8 * uncertainty + 0.2 * rarity,
                row,
                _fingerprint(row.get("resume_text", "") + " " + row.get("job_text", "")),
            )
        )
    selected: list[dict[str, Any]] = []
    selected_fingerprints: list[set[str]] = []
    for score, row, fingerprint in sorted(ranked, key=lambda item: -item[0]):
        if len(selected) >= count:
            break
        similarity = max(
            (
                len(fingerprint & other) / max(len(fingerprint | other), 1)
                for other in selected_fingerprints
            ),
            default=0,
        )
        if similarity > 0.95 and len(ranked) > count:
            continue
        selected.append(
            {
                **row,
                "review_priority": round(score, 6),
                "annotation_id": row.get("pair_id") or stable_id(row),
            }
        )
        selected_fingerprints.append(fingerprint)
    write_jsonl(output_path, selected)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--count", type=int, default=500)
    args = parser.parse_args()
    print(json.dumps({"selected": len(run(args.input, args.output, args.count))}, indent=2))


if __name__ == "__main__":
    main()
