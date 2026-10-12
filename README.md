# SideTrack

One music link → Generate → browse pages of 20 → Download TXT or CSV → import into your music library.

A small Python/FastAPI app with plain HTML, CSS, and JavaScript. Recommendations come from **experimental, unofficial `ytmusicapi`**. No database, accounts, Google credentials, cookies, audio downloads, or frontend build step. Each recommendation request is independent; the browser creates the download.

## Run locally

Requires **Python 3.12** and an internet connection.

```sh
git clone https://github.com/IcebergSnow/SideTrack.git
cd SideTrack
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m sidetrack
```

On Windows, create the environment with `py -3.12 -m venv .venv` and activate with `.venv\Scripts\activate`.

Open [http://localhost:8000](http://localhost:8000). No `.env` file is needed; `.env.example` documents this. Existing Google OAuth variables are no longer read.

Try `https://www.youtube.com/watch?v=fJ9rUzIMcZQ`, then click **Generate**.

SideTrack loads a pool of up to 200 unique songs and displays 20 per page. **Previous** and **Next** browse the saved pages without reshuffling. At the end of the pool, **Next** requests more songs and filters out everything already loaded. A short page stays unchanged when another pool arrives.

Choose **Current page** or **Everything through this page** before downloading TXT/CSV. On page 3, the second option includes pages 1–3, not later pages already held in the browser. The number of songs in the download is shown below the controls. Refreshing or generating again clears the pages.

## Deploy on Vercel

1. Sign in to [Vercel](https://vercel.com/new) with GitHub.
2. Choose **Add New → Project**, find **IcebergSnow/SideTrack**, and click **Import**. If it is missing, adjust the Vercel GitHub integration's repository access.
3. Use these settings:

   | Setting | Value |
   | --- | --- |
   | Framework Preset | **FastAPI** (auto-detected; select it if necessary) |
   | Root Directory | Repository root (`./`) |
   | Build Command | Leave the override off |
   | Output Directory | Leave the override off |
   | Install Command | Leave the override off |
   | Environment Variables | None |

4. Click **Deploy**. Vercel installs `requirements.txt` and loads the root `app.py`. `.python-version` selects Python 3.12; `vercel.json` sets a 60-second function limit. Do not enter a Uvicorn start command or `dist` output directory.
5. When deployment is ready, open its `.vercel.app` URL. Paste the example song, click **Generate**, and confirm that the songs appear. Download TXT and CSV and check their contents.
6. Subsequent pushes to the connected production branch (`main` for this repository) redeploy automatically.

Vercel setup follows its [FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi) and [Python runtime documentation](https://vercel.com/docs/functions/runtimes/python). There is no session store, OAuth callback, or background export task to configure.

**Verify recommendations on the deployed URL.** Working on a laptop does not guarantee that YouTube Music will accept traffic from a hosting provider's IP. A successful Vercel build only verifies deployment, not the upstream music service. To check the deployed API from a terminal:

```sh
python scripts/check_recommendations.py --base-url https://YOUR-PROJECT.vercel.app
```

For a failure, open the deployment's **Logs**, reproduce the request, and inspect `/api/recommend`. Check build logs for installation errors. If the homepage loads but recommendations fail, try another official music link and compare with a local run. YouTube may block, throttle, or change its unofficial endpoint; SideTrack displays an error instead of substituting sample tracks. Preview deployment protection may require signing in through the browser before testing.

## Vercel Web Analytics

The plain HTML frontend includes Vercel Web Analytics for visitor and page-view counts. It loads Vercel's same-origin script, so the existing Content Security Policy allows it without inline scripts or extra domains. No npm dependency or frontend build step is needed. Analytics is skipped on localhost.

In your Vercel project, open **Analytics** and click **Enable** if it is not already enabled. Deploy the latest commit after enabling it, visit your production site, then check the Analytics dashboard. If Vercel shows framework-specific setup instructions, choose **HTML**; the integration is already in this repository. See [Vercel's setup guide](https://vercel.com/docs/analytics/quickstart).

SideTrack adds no custom events or song metadata to analytics. Standard page-view information is handled by Vercel; see [Vercel's analytics privacy documentation](https://vercel.com/docs/analytics/privacy-policy). Your pasted song URL and downloaded playlist contents are not attached to analytics events.

## Import the downloaded playlist

1. Generate recommendations and browse to a page. Choose **Current page** or **Everything through this page**, then click **TXT** or **CSV**.
2. Open a transfer service such as [Soundiiz](https://soundiiz.com/tutorial/import-text-to-youtube-music) or [TuneMyMusic](https://www.tunemymusic.com/).
3. Choose its file-import option and upload the downloaded file. For Soundiiz: **Import Playlist → From File**.
4. Review the detected tracks, choose YouTube Music as the destination, connect your Google account there, and complete the transfer.
5. Open the resulting playlist in YouTube Music and check its songs and privacy setting.

SideTrack never receives the transfer service's Google credentials or tokens. Importing is a separate step on that service; its account requirements, permissions, fees, and limits apply. SideTrack does not create a YouTube playlist or return a playlist URL itself.

TXT has one `Artist - Title` entry per line. CSV has `title,artist,url` columns, following [Soundiiz's documented format](https://support.soundiiz.com/hc/en-us/articles/360010006793-What-is-the-CSV-format-to-import-playlists-and-favorites). URLs are included for reference, but importers can match by artist/title and choose different recordings. Exact YouTube video IDs and private visibility are not guaranteed by file import. CSV escapes quotes and neutralizes formula-like metadata; this can add a leading apostrophe to unusual titles or artist names.

## Recommendation behavior and limitations

- Accepts YouTube watch links, YouTube Music links, `youtu.be` links, and video-specific shorts/embed/live URL forms. Playlist-only links are rejected. A valid video URL does not guarantee that YouTube Music recognizes it as a song.
- Calls `get_watch_playlist(videoId=..., radio=True, limit=200)` without authentication. The library may make several underlying requests and return more than 200 raw candidates.
- Removes the original video, known audio/video counterparts, duplicate video IDs, unavailable entries, and obvious duplicate recordings using normalized artist/title metadata. Packaging labels such as “Official Video” and “2011 Remaster” are ignored; live/acoustic/remix qualifiers are retained.
- Keeps YouTube Music's ordering and returns up to 200 unique recommendations per pool, displayed in pages of 20. If fewer than 20 remain after filtering, tries one additional radio request. Short pages are usable; an empty initial pool or unsupported song produces an error.
- The browser sends earlier songs' IDs, titles, artists, and known counterpart IDs when requesting another pool. The stateless backend excludes these songs and their obvious duplicate recordings. Browsing back preserves each page; an export through page N contains exactly pages 1–N in their original order.
- If two radio attempts find no unseen songs, **Next** stops at the last page with a message. An upstream failure keeps the previous pages and allows a retry. The app cannot promise endless unique recommendations.
- Each pool request has a 16-HTTP-request cap, a 35-second budget checked before upstream requests, and connect/read timeouts of at most 10 seconds each. One browser run holds at most 2,000 songs; download them or generate again at that point. No server session or database is introduced.

`ytmusicapi` is not a Google-supported API. YouTube changes can break its response parsing or unauthenticated access. Results vary by song, request, region, and IP. Private, deleted, age/region-restricted, podcast, or unrecognized uploads may not work. Duplicate detection is a metadata heuristic, not audio fingerprinting. Consult YouTube's applicable terms before broader use.

The app keeps results only in the current page's memory. Refreshing clears them; download a file to keep them. No application database or persistent token storage is used. The server sends the seed video ID to YouTube Music. Your hosting provider may retain operational logs. The public recommendation endpoint has no application-level rate limiting; use Vercel's access controls or firewall if traffic becomes an issue.

## Verify

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --test tests/test_downloads.mjs tests/test_pages.mjs
```

Node.js 20+ is needed only for the frontend tests, not to run the app. Tests cover URL parsing, duplicate filtering across pools, upstream failures and exhaustion, request bounds, stateless API requests, history validation, frontend serving, page preservation, export boundaries, and file formatting. Successful API fixtures exist **only in tests**; the running app always calls YouTube Music.

Run the real recommendation flow:

```sh
python scripts/check_recommendations.py
python scripts/check_recommendations.py 'https://music.youtube.com/watch?v=kJQP7kiw5Fk'
python scripts/check_recommendations.py --refill
python scripts/check_recommendations.py --base-url https://YOUR-PROJECT.vercel.app --refill
```

The smoke test fails on upstream errors and checks that results exclude the seed and contain unique IDs/recording keys. `--refill` checks another pool against the full first pool for repeated IDs, recordings, and known counterparts. It never substitutes sample data.

The original recommendation flow was tested live before the earlier Google export implementation. Later overlap tests used five repeated requests per song, including real requests to the deployed app. Larger local tests returned more than 200 usable songs for Queen (`fJ9rUzIMcZQ`) and Luis Fonsi (`kJQP7kiw5Fk`), motivating the pool-and-pages design. These are development observations, not guarantees for every song. The paging implementation passes 48 Python tests and 8 JavaScript tests.

Live pool/refill checks returned 200 initial songs for both inputs, then 2 new songs for Queen and 45 for Despacito without repeated IDs or recording keys. Browser checks covered 10 cached pages, additional pools, unchanged previous pages, a 20-song page download and a 60-song cumulative download in exact displayed order, plus recovery after the local server was stopped and restarted.

Google OAuth and official YouTube API writes have been removed in favor of file downloads. A real third-party import still needs to be verified with your account. Always check the deployed recommendation flow after deployment; local checks cannot establish cloud availability.

## Files

```text
app.py                           Vercel entrypoint
vercel.json                      FastAPI deployment settings
sidetrack/app.py                 Stateless API and frontend routes
sidetrack/recommendations.py     URL parsing, live ytmusicapi calls, filtering
static/                         Barebones HTML/CSS/JS and download formatting
scripts/check_recommendations.py Live local or deployed API smoke test
tests/                          Isolated Python and JavaScript tests
```
