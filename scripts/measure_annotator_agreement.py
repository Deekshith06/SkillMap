from __future__ import annotations

import argparse
import json

from training.annotations import agreement

parser = argparse.ArgumentParser()
parser.add_argument("left")
parser.add_argument("right")
args = parser.parse_args()
print(json.dumps(agreement(args.left, args.right), indent=2))
