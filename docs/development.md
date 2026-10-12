# Development

For installation and deployment, see [self-hosting](self-hosting.md). For app usage, see the [user guide](../README.md).

## Architecture and recommendation behavior

The app uses Python/FastAPI and plain HTML, CSS, and JavaScript. There is no frontend build step or server session store. Each recommendation request is independent.

The backend calls `get_watch_playlist(videoId=..., radio=True, limit=200)`. That limit is a target used by `ytmusicapi`; it may make several underlying requests and return more raw candidates. SideTrack filters them and returns up to 200 unique tracks, displayed in pages of 20. If fewer than 20 new tracks remain, it tries one additional radio request.

Deduplication uses video IDs, known audio/video counterparts, and normalized artist/title keys. It ignores packaging labels such as “Official Video” or “2011 Remaster” while retaining live/acoustic/remix qualifiers. Later pools exclude all previously loaded tracks. Old pages, including short ones, stay unchanged when a new pool arrives.

Each pool request has a 16-HTTP-request cap, a 35-second budget checked before upstream requests, and connect/read timeouts of at most 10 seconds each. The browser limits a run to 2,000 tracks. `vercel.json` sets a 60-second function limit; root `app.py` exposes the FastAPI app and `.python-version` selects Python 3.12.

The public recommendation endpoint has no application-level rate limiting. For a public deployment, use your hosting provider's access controls or firewall if traffic becomes an issue. Review YouTube's applicable terms before broader use.

CSV downloads contain `title,artist,url`; TXT uses one `Artist - Title` per line. CSV escaping also neutralizes formula-like metadata, so unusual titles/artists can gain a leading apostrophe when opened as a spreadsheet.

## Tests and live recommendation checks

From the repository folder in an activated environment:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --test tests/test_downloads.mjs tests/test_pages.mjs
```

Node.js 20+ is only needed for the JavaScript tests. Tests cover input validation, filtering across pools, upstream failures, page preservation, download boundaries, and file formatting. Successful API fixtures are confined to tests; the running app never substitutes sample recommendations for a failed request.

To check real recommendations from your machine:

```sh
python scripts/check_recommendations.py
python scripts/check_recommendations.py --refill
```

To check a deployed instance, replace the example hostname with its public production URL:

```sh
python scripts/check_recommendations.py --base-url https://YOUR-PROJECT.vercel.app --refill
```

These commands contact YouTube Music. `--refill` requests a second pool and checks it against the first for repeated IDs, recording keys, and known counterparts. Errors fail the check instead of returning fake songs.

## Project files

| File or folder | Purpose |
| --- | --- |
| `app.py` | Vercel entrypoint |
| `vercel.json` / `.python-version` | Hosting and Python version settings |
| `sidetrack/app.py` | API endpoints and frontend routes |
| `sidetrack/recommendations.py` | URL parsing, YouTube Music requests, and filtering |
| `static/` | Plain HTML/CSS/JS, pagination, and download formatting |
| `scripts/check_recommendations.py` | Live local/deployed API check |
| `tests/` | Python and JavaScript tests |
