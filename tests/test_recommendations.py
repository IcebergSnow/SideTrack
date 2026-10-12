import pytest
import requests

from sidetrack import recommendations as rec


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=fJ9rUzIMcZQ&list=anything&t=30",
    "https://music.youtube.com/watch?v=fJ9rUzIMcZQ&si=shared",
    "https://youtu.be/fJ9rUzIMcZQ?si=shared",
    "youtube.com/watch?v=fJ9rUzIMcZQ",
    "https://m.youtube.com/watch?v=fJ9rUzIMcZQ",
    "https://www.youtube.com/shorts/fJ9rUzIMcZQ",
    "https://www.youtube.com/embed/fJ9rUzIMcZQ",
])
def test_extract_supported_urls(url):
    assert rec.extract_video_id(url) == "fJ9rUzIMcZQ"


@pytest.mark.parametrize("url", [
    "", "fJ9rUzIMcZQ", "https://youtube.com/playlist?list=abc",
    "https://evil.test/watch?v=fJ9rUzIMcZQ",
    "https://youtube.com.evil.test/watch?v=fJ9rUzIMcZQ",
    "https://youtube.com@evil.test/watch?v=fJ9rUzIMcZQ",
    "https://evil.test@youtube.com/watch?v=fJ9rUzIMcZQ",
    "https://youtube.com:123/watch?v=fJ9rUzIMcZQ",
    "https://youtube.com/watch?v=short", "file:///watch?v=fJ9rUzIMcZQ",
    "https://youtube.com/watch?v=fJ9rUzIMcZQ&v=kJQP7kiw5Fk",
])
def test_reject_unsupported_urls(url):
    with pytest.raises(rec.RecommendationError) as error:
        rec.extract_video_id(url)
    assert error.value.status == 400


def raw(number, title="A Song", artist="Artist", **extra):
    return {"videoId": f"v{number:010d}", "title": title, "artists": [{"name": artist}], **extra}


def test_seed_ids_recordings_and_counterparts_are_excluded():
    original = raw(1, "Bohemian Rhapsody (Digital Remaster)", "Queen", counterpart=raw(2))
    seed = rec.clean_track(original)
    result = rec.select_tracks([
        original, raw(2), raw(3, "Queen - Bohemian Rhapsody [Official Video]", "QueenVEVO"),
        raw(4, "Dream On", "Aerosmith", counterpart=raw(5)), raw(4, "Different text"),
        raw(5, "Dream On audio", "Aerosmith"), raw(6, "Dream On (2011 Remaster)", "Aerosmith"),
        raw(7, "Dream On (Live)", "Aerosmith"), raw(8, "Dream On", "Another artist"),
        raw(9, "Unavailable", isAvailable=False), raw(10, "Podcast", videoType="MUSIC_VIDEO_TYPE_PODCAST_EPISODE"),
    ], seed)
    assert [track["video_id"] for track in result] == [raw(n)["videoId"] for n in [4, 7, 8]]


def test_normalization_preserves_real_title_words_and_distinct_versions():
    def key(title):
        return rec.recording_key(rec.clean_track(raw(1, title)))
    assert key("Video Games") != key("Games")
    assert key("Song") != key("Song (Acoustic)")
    assert key("Song") != key("Song (Remix)")
    assert key("Song - 2011 Remaster") == key("Song (Official Audio)")
    assert key("Song (Official HD Video)") == key("Song")
    assert key("Song - Remaster (Visualizer)") == key("Song")


def test_counterpart_deduplication_is_order_independent():
    seed = rec.clean_track(raw(0, "Seed"))
    result = rec.select_tracks([raw(1, "First title"), raw(2, "Alternate title", counterpart=raw(1))], seed)
    assert len(result) == 1


def test_refills_short_radio_and_never_fabricates_tracks(monkeypatch):
    calls = []
    class Radio:
        def __init__(self, **kwargs):
            pass

        def get_watch_playlist(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                return {"tracks": [raw(0, "Seed"), raw(1, "First")]}
            return {"tracks": [raw(0, "Seed"), raw(1, "First"), raw(2, "Second")]}

    monkeypatch.setattr(rec, "YTMusic", Radio)
    result = rec.recommend("https://youtu.be/v0000000000")
    assert len(result["tracks"]) == 2
    assert "2 unique" in result["note"]
    assert calls == [{"videoId": "v0000000000", "radio": True, "limit": 25}] * 2


@pytest.mark.parametrize("response,status", [
    ({"tracks": []}, 422),
    ({"tracks": [raw(0, "Seed")]}, 404),
    (requests.Timeout(), 504),
    (KeyError("upstream schema changed"), 502),
])
def test_real_failure_modes_are_reported(monkeypatch, response, status):
    class Radio:
        def __init__(self, **kwargs):
            pass

        def get_watch_playlist(self, **kwargs):
            if isinstance(response, Exception):
                raise response
            return response

    monkeypatch.setattr(rec, "YTMusic", Radio)
    with pytest.raises(rec.RecommendationError) as error:
        rec.recommend("https://youtu.be/v0000000000")
    assert error.value.status == status
