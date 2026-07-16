from __future__ import annotations

import argparse
import json

from training.annotations import merge

parser = argparse.ArgumentParser()
parser.add_argument("left")
parser.add_argument("right")
parser.add_argument("output")
parser.add_argument("--adjudicated")
args = parser.parse_args()
print(
    json.dumps(
        {"merged": len(merge(args.left, args.right, args.adjudicated, args.output))}, indent=2
    )
)
