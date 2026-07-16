"""Export generated profile spans as NER examples."""

from __future__ import annotations

import json

from training.common import read_jsonl, write_jsonl


def main() -> None:
    rows = [
        {
            "document_id": row["document_id"],
            "text": row["text"],
            "entities": [*row.get("skills", []), *row.get("knowledge", [])],
            "synthetic": True,
        }
        for row in read_jsonl("data/synthetic/profiles.jsonl")
    ]
    write_jsonl("data/synthetic/ner_examples.jsonl", rows)
    print(json.dumps({"records": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
