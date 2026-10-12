"""Experimental, unauthenticated recommendations from YouTube Music."""

from functools import partial
import re
import unicodedata
from urllib.parse import parse_qs, urlparse

import requests
from ytmusicapi import YTMusic

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
TARGET = 20


class RecommendationError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


def extract_video_id(url: str) -> str:
    value = url.strip()
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password or parsed.port:
            raise ValueError
        host = (parsed.hostname or "").lower()
        parts = parsed.path.strip("/").split("/")
        if host in {"youtu.be", "www.youtu.be"} and len(parts) == 1:
            video_id = parts[0]
        elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
            if parsed.path.rstrip("/") == "/watch":
                values = parse_qs(parsed.query).get("v", [])
                video_id = values[0] if len(values) == 1 else ""
            elif len(parts) == 2 and parts[0] in {"shorts", "embed", "live"}:
                video_id = parts[1]
            else:
                raise ValueError
        else:
            raise ValueError
        if VIDEO_ID.fullmatch(video_id):
            return video_id
    except ValueError:
        pass
    raise RecommendationError("Paste a YouTube or YouTube Music link to a single song, including its video ID.", 400)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", value).split())


def recording_key(track: dict) -> tuple[str, tuple[str, ...]]:
    # Strip packaging labels, but retain live/acoustic/remix qualifiers.
    title = track["title"]
    media_label = r"(?:official\s+)?(?:(?:hd|hq|4k)\s+)?(?:music\s+video|video|audio|lyric(?:s|\s+video)?|visualizer)(?:\s+(?:hd|hq|4k))?"
    labels = media_label + r"|(?:digital\s+)?(?:\d{4}\s+)?remaster(?:ed)?(?:\s+\d{4})?|hd|hq|4k"
    title = re.sub(r"(?i)[\[(]\s*(?:" + labels + r")\s*[\])]", "", title)
    title = re.sub(r"(?i)\b(?:official (?:music )?(?:video|audio)|official lyrics?|lyrics? video)\b", "", title)
    title = re.sub(r"(?i)\s*[-–—]\s*(?:" + labels + r")\s*$", "", title)
    artists = tuple(sorted({normalize(re.sub(r"(?i)(?:\s*-\s*topic|vevo)$", "", name)) for name in track["artists"]}))
    title = normalize(title)
    # Official videos often repeat the artist in the title.
    for artist in artists:
        if title.startswith(artist + " "):
            title = title[len(artist) + 1:]
    return title, artists


def clean_track(raw: dict) -> dict | None:
    video_id = raw.get("videoId")
    if not isinstance(video_id, str) or not VIDEO_ID.fullmatch(video_id) or raw.get("isAvailable") is False:
        return None
    if raw.get("videoType") in {"MUSIC_VIDEO_TYPE_PODCAST_EPISODE", "MUSIC_VIDEO_TYPE_UGC"}:
        return None
    title = raw.get("title")
    artists = [a["name"] for a in raw.get("artists", []) if isinstance(a, dict) and a.get("name")]
    if not title or not artists:
        return None
    return {
        "video_id": video_id,
        "title": title,
        "artists": artists,
        "duration": raw.get("length") or raw.get("duration") or "",
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
    }


def select_tracks(raw_tracks: list[dict], seed: dict, limit: int = TARGET) -> list[dict]:
    excluded_ids = {seed["video_id"]}
    seen_recordings = {recording_key(seed)}
    # YouTube explicitly identifies audio/video counterparts; exclude the seed's too.
    for raw in raw_tracks:
        counterpart = raw.get("counterpart") or {}
        if raw.get("videoId") == seed["video_id"]:
            excluded_ids.add(counterpart.get("videoId"))
        if counterpart.get("videoId") == seed["video_id"]:
            excluded_ids.add(raw.get("videoId"))
    selected = []
    for raw in raw_tracks:
        track = clean_track(raw)
        counterpart_id = (raw.get("counterpart") or {}).get("videoId")
        if not track or track["video_id"] in excluded_ids or (counterpart_id and counterpart_id in excluded_ids):
            continue
        key = recording_key(track)
        if key in seen_recordings:
            continue
        excluded_ids.add(track["video_id"])
        excluded_ids.add(counterpart_id)
        seen_recordings.add(key)
        selected.append(track)
        if len(selected) >= limit:
            break
    return selected


def recommend(url: str) -> dict:
    video_id = extract_video_id(url)
    try:
        with requests.Session() as session:
            session.request = partial(session.request, timeout=15)
            ytm = YTMusic(requests_session=session)
            playlist = ytm.get_watch_playlist(videoId=video_id, radio=True, limit=25)
            raw_tracks = playlist.get("tracks") or []
            original = next((t for t in raw_tracks if t.get("videoId") == video_id), None)
            seed = clean_track(original) if original else None
            if seed is None:
                raise RecommendationError(
                    "YouTube Music couldn't recognize this as an available song. Try an official music video or a YouTube Music song link.", 422
                )
            tracks = select_tracks(raw_tracks, seed)
            if len(tracks) < TARGET:
                # A second radio varies the candidates without adding another algorithm.
                try:
                    extra = ytm.get_watch_playlist(videoId=video_id, radio=True, limit=25)
                    raw_tracks.extend(extra.get("tracks") or [])
                    tracks = select_tracks(raw_tracks, seed)
                except Exception:
                    # Keep real recommendations from the first request if the refill fails.
                    pass
            if not tracks:
                raise RecommendationError("No related songs were available for this track. Try another music link.", 404)
            return {
                "seed": seed,
                "tracks": tracks,
                "note": "" if len(tracks) == TARGET else f"YouTube Music returned {len(tracks)} unique recommendations. You can download this shorter playlist.",
            }
    except RecommendationError:
        raise
    except requests.Timeout as exc:
        raise RecommendationError("YouTube Music took too long to respond. Please try again.", 504) from exc
    except requests.RequestException as exc:
        raise RecommendationError("Couldn't reach YouTube Music. Check your connection and try again.") from exc
    except Exception as exc:
        raise RecommendationError(
            "YouTube Music couldn't return recommendations for this link. The song may be unavailable, or the unofficial API may have changed. Try another song."
        ) from exc
