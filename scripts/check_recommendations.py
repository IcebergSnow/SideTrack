"""Live smoke test. No credentials or successful-response fixtures are used."""

import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sidetrack.recommendations import POOL_TARGET, RecommendationError, recommend, recording_key

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("url", nargs="?", default="https://www.youtube.com/watch?v=fJ9rUzIMcZQ")
parser.add_argument("--base-url", help="Test a deployed SideTrack URL instead of calling the recommendation module locally")
parser.add_argument("--refill", action="store_true", help="Also fetch another pool excluding the first pool and check for repeats")
args = parser.parse_args()


def fetch(exclude=None):
    if args.base_url:
        response = requests.post(args.base_url.rstrip("/") + "/api/recommend", json={"url": args.url, "exclude": exclude or []}, timeout=70)
        response.raise_for_status()
        return response.json()
    return recommend(args.url, exclude=exclude)


try:
    result = fetch()
    if args.refill:
        extra = fetch(result["tracks"])
        tracks = result["tracks"] + extra["tracks"]
        combined = [recording_key(track) for track in tracks]
        assert len(combined) == len(set(combined))
        assert len(tracks) == len({track["video_id"] for track in tracks})
        known_ids = {track["video_id"] for track in tracks}
        assert not any(track.get("counterpart_id") in known_ids for track in tracks)
        assert extra["tracks"] or extra["exhausted"]
        assert len(extra["tracks"]) <= POOL_TARGET
        print(f"REFILL CHECK PASSED: {len(extra['tracks'])} new songs, no repeated IDs or recording keys")
except RecommendationError as exc:
    raise SystemExit(f"LIVE CHECK FAILED ({exc.status}): {exc}")
except (requests.RequestException, ValueError) as exc:
    raise SystemExit(f"LIVE HTTP CHECK FAILED: {exc}")
ids = [track["video_id"] for track in result["tracks"]]
keys = [recording_key(track) for track in result["tracks"]]
assert result["seed"]["video_id"] not in ids
assert len(ids) == len(set(ids)) == len(set(keys))
assert 1 <= len(ids) <= POOL_TARGET
print(json.dumps(result, indent=2, ensure_ascii=False))
print(f"LIVE CHECK PASSED: {len(ids)} unique recommendations")
