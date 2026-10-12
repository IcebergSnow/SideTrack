"""Live smoke test. No credentials or successful-response fixtures are used."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sidetrack.recommendations import RecommendationError, recommend, recording_key

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("url", nargs="?", default="https://www.youtube.com/watch?v=fJ9rUzIMcZQ")
args = parser.parse_args()
try:
    result = recommend(args.url)
except RecommendationError as exc:
    raise SystemExit(f"LIVE CHECK FAILED ({exc.status}): {exc}")
ids = [track["video_id"] for track in result["tracks"]]
keys = [recording_key(track) for track in result["tracks"]]
assert result["seed"]["video_id"] not in ids
assert len(ids) == len(set(ids)) == len(set(keys))
assert 1 <= len(ids) <= 20
print(json.dumps(result, indent=2, ensure_ascii=False))
print(f"LIVE CHECK PASSED: {len(ids)} unique recommendations")
