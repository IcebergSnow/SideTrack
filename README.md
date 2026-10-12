# SideTrack

One music link → Generate → Export → a private YouTube playlist.

A small Python/FastAPI app with plain HTML, CSS, and JavaScript. Recommendations come from **experimental, unofficial `ytmusicapi`**; playlist writes use the **official YouTube Data API v3**. No database, user accounts, audio downloads, or build step.

## Run locally

Requires **Python 3.11+** (tested with Python 3.12) and an internet connection.

```sh
git clone https://github.com/IcebergSnow/SideTrack.git
cd SideTrack
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m sidetrack
```

On Windows, activate with `.venv\Scripts\activate` and copy with `copy .env.example .env`.

Open **[http://localhost:8000](http://localhost:8000)**. Use `localhost`, rather than switching to `127.0.0.1`, throughout the browser flow so the origin and session cookie match the registered callback.

**Generate works immediately without Google credentials or login.** Try:

```text
https://www.youtube.com/watch?v=fJ9rUzIMcZQ
```

## Configure Google export

1. Create or select a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com).
3. Configure the Google Auth Platform consent screen. For a personal proof of concept, keep the external app in **Testing** and add your Google account under **Test users**. Configure the requested YouTube scope: `https://www.googleapis.com/auth/youtube.force-ssl`.
4. Create an OAuth client of type **Web application**. Add this exact **Authorized redirect URI**:

   ```text
   http://localhost:8000/oauth/callback
   ```

5. Put the client ID and client secret in your local `.env`:

   ```dotenv
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback
   ```

6. Restart SideTrack, generate recommendations, and click **Export to YouTube**. Sign in to the Google account/channel you want to use and grant the requested YouTube permission. SideTrack returns to the song list, displays export progress, and shows **Open your YouTube playlist** when complete.

The account must have a YouTube channel. This scope is Google's write-capable scope accepted by playlist creation/insertion; Google does not offer a playlist-only write permission. SideTrack only creates one private playlist and inserts the displayed songs. The app requests online access and does not retain refresh tokens for later use.

Never commit `.env` or put secrets in frontend code. `.env` is ignored, and deployment environments can supply the same variables directly. You do not need a YouTube API key, browser cookies, or `ytmusicapi` authentication.

## Recommendation behavior

- Accepts ordinary YouTube watch links, YouTube Music links, `youtu.be` links, and video-specific shorts/embed/live URL forms. Playlist-only links are rejected. A valid URL does not guarantee that YouTube Music recognizes the video as a song.
- Calls `get_watch_playlist(videoId=..., radio=True, limit=25)` without authentication. `limit` is a minimum; the service may return more candidates.
- Removes the original video, audio/video counterparts where supplied, duplicate video IDs, unavailable entries, and obvious duplicate recordings using normalized artist/title metadata. Packaging labels such as “Official Video” and “2011 Remaster” are ignored; live/acoustic/remix qualifiers are retained.
- Keeps YouTube Music's ordering and selects up to 20 recommendations. If fewer remain, makes one additional radio request and filters again. Shorter usable lists are explicitly labeled; empty lists and unsupported songs produce errors.
- Export uses the exact video IDs shown in the preview, held in the server session. Client-supplied video lists are not accepted.

`ytmusicapi` is not a Google-supported API. YouTube changes can break its response parsing or unauthenticated access. Results vary by song, request, region, and IP. Private, deleted, age/region-restricted, podcast, or unrecognized uploads may not work. Matching is a small metadata heuristic, so some alternate recordings can slip through or be grouped together; this is not audio fingerprinting. Playability can change between generation and export. Consult YouTube's applicable terms before broader use.

## State, privacy, and failures

- Single process, **one worker**. Sessions and recommendations are held in memory for up to one hour of inactivity, with a 200-session cap. A restart loses all pending work. This is a local proof of concept, not a multi-user hosted service.
- The browser gets only a random `HttpOnly`, `SameSite=Lax` session cookie. OAuth state and PKCE are verified server-side and expire after 10 minutes. Tokens and client secrets never enter browser storage or responses. The session never stores OAuth access tokens; the export task holds credentials only while executing.
- API mutations require a matching configured origin and a custom header. HTTPS callbacks are required outside loopback; HTTPS makes the session cookie `Secure`.
- `python -m sidetrack` disables access logs so callback authorization codes are not logged. If running Uvicorn directly, use `uvicorn sidetrack.app:app --host 127.0.0.1 --port 8000 --no-access-log`. Avoid request/query logging in a reverse proxy, too.
- Writes are never automatically retried. Double clicks and callback replay cannot create a second playlist for the same completed export in the same session. If an insertion fails, the app reports confirmed additions and links to the partial private playlist. It does not silently claim success or delete that playlist.
- A network timeout can occur **after** Google processes a write. If playlist creation times out before returning its ID, check your YouTube library before retrying. Process crashes have the same limitation. Guaranteed exactly-once export would require persistent state, intentionally omitted here.
- Quota exhaustion, permission errors, missing OAuth configuration, cancellation, and unavailable recommendations have visible error messages. Google API quota is consumed for the playlist creation and each song insertion.

## Verify

Install development dependencies and run the isolated tests:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests cover URL parsing, duplicate filtering, API failure handling, OAuth state/PKCE/cancellation/expiry, session isolation, private playlist payloads, insertion order, partial writes, and replay prevention. API stubs exist **only in tests**. The running app always calls the actual services.

Run the real recommendation flow independently of OAuth:

```sh
python scripts/check_recommendations.py
python scripts/check_recommendations.py 'https://music.youtube.com/watch?v=kJQP7kiw5Fk'
```

This script fails on upstream errors, prints the actual songs, and checks that recommendations exclude the seed and contain unique IDs/recording keys. It never substitutes sample data.

### Validation status

Before implementing export, live unauthenticated radio requests succeeded for Queen's “Bohemian Rhapsody” (`fJ9rUzIMcZQ`) and Luis Fonsi's “Despacito” (`kJQP7kiw5Fk`), returning 50 raw candidates each with `ytmusicapi 1.12.3`. The implemented recommendation flow passed live smoke tests with 20 unique songs for both inputs. Browser checks covered real generation, invalid-link feedback, missing export configuration, and desktop/mobile layouts. All 36 isolated tests passed. These are observations from development, not guarantees of future availability.

**Real Google OAuth consent and playlist creation have not been verified with a user account.** Configure your own OAuth credentials above, then complete the three-button workflow to verify the resulting playlist and its privacy setting in YouTube. The unit tests validate export logic without creating real playlists.

## Files

```text
sidetrack/app.py              FastAPI routes and ephemeral browser sessions
sidetrack/recommendations.py  URL parsing, ytmusicapi calls, filtering
sidetrack/export.py           Google OAuth and official YouTube API writes
static/                      Plain HTML, CSS, JavaScript
scripts/check_recommendations.py  Live upstream smoke test
tests/                       Isolated tests (test-only API stubs)
```

API references: [ytmusicapi watch playlists](https://ytmusicapi.readthedocs.io/en/stable/reference/playlists.html), [Google web-server OAuth](https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps), [playlist creation](https://developers.google.com/youtube/v3/docs/playlists/insert), [playlist item insertion](https://developers.google.com/youtube/v3/docs/playlistItems/insert).
