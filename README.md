# SideTrack

Find similar music from a single YouTube song link. Browse the recommendations, then download a list to import into your music library.

**[Open SideTrack →](https://side-track.vercel.app/)**

No installation or sign-in is needed to use the website. SideTrack uses experimental, unofficial `ytmusicapi` recommendations and does not download audio.

[First use](#try-it-with-one-song) · [Downloads](#choose-what-to-download) · [Import to YouTube](#get-the-songs-into-youtube) · [Run locally](#run-on-your-own-computer) · [Deploy on Vercel](#deploy-your-own-copy-on-vercel) · [Troubleshooting](#troubleshooting)

## Try it with one song

1. Open [SideTrack](https://side-track.vercel.app/).
2. Copy a link to **one song** from YouTube or YouTube Music and paste it into the URL field. You can try this example:

   ```text
   https://www.youtube.com/watch?v=fJ9rUzIMcZQ
   ```

3. Click **Generate** and wait for the recommendations to appear.
4. Use **Previous** and **Next** to browse pages of up to 20 songs. Click a song title to open it on YouTube.
5. Choose what to include using the **Download** menu, then click **CSV** or **TXT**.
6. Find the file in your browser's downloads and use one of the [import options below](#get-the-songs-into-youtube).

**Downloading a file does not create a playlist in your YouTube account.** That happens in a separate importer, where you grant Google access.

Download the songs you want to keep **before refreshing the page or clicking Generate again**. Both clear the current recommendations.

## Choose what to download

### Which pages?

| Download setting | What is included |
| --- | --- |
| **Current page** | Only the songs visible on that page. |
| **Everything through this page** | All songs from page 1 through the page you are viewing, in order. |

For example, on page 3, **Current page** contains 20 songs and **Everything through this page** contains 60, assuming all three pages are full. Later pages are not included. Check the song count shown under the download controls before saving.

SideTrack loads up to 200 unique recommendations at a time. Moving between loaded pages keeps their songs unchanged. At the end, **Next** asks for more and filters out songs already loaded. A page can contain fewer than 20 songs, and new results are not guaranteed indefinitely.

### CSV or TXT?

| Format | Contents | Use it for |
| --- | --- | --- |
| **CSV** | Song title, artist, and YouTube URL in columns. | The companion CLI, supported file-import services, or a spreadsheet. |
| **TXT** | One `Artist - Title` entry per line. | Supported text-import services or a readable song list. |

**Choose CSV if you plan to use the SideTrack CLI importer.** Renaming a TXT file to `.csv` does not add the missing video links.

## Get the songs into YouTube

There are two separate import options. SideTrack itself does not handle Google sign-in or create playlists.

### Option A: Use a transfer website

This option lets you complete the import in your browser.

1. Open [Soundiiz's import guide](https://soundiiz.com/tutorial/import-text-to-youtube-music) or [TuneMyMusic's file importer](https://www.tunemymusic.com/transfer/file-to-youtube-music).
2. Choose file import and upload your downloaded CSV or TXT. In Soundiiz, use **Import Playlist → From File**.
3. Review the detected songs, choose **YouTube Music** as the destination, and connect your Google account on that service.
4. Complete the transfer, then check the resulting songs and playlist privacy setting in YouTube Music.

The service may require an account, have transfer limits, or charge a fee. It may match by artist/title and select a different recording. SideTrack's YouTube URLs do not guarantee that a third-party service will use those exact videos. See [Soundiiz's CSV format guidance](https://support.soundiiz.com/hc/en-us/articles/360010006793-What-is-the-CSV-format-to-import-playlists-and-favorites).

### Option B: Use the companion CLI on your computer

[SideTrack CLI Playlist Importer](https://github.com/IcebergSnow/SideTrack_CLI_PlaylistImporter) is a separate command-line tool that reads SideTrack **CSV** files and uses their exact YouTube video IDs. It supports combining files, creating a private playlist, and resuming an interrupted import.

Follow its [installation and Google setup guide](https://github.com/IcebergSnow/SideTrack_CLI_PlaylistImporter#readme) first. After installing it and configuring your own Google Desktop OAuth client, you can run:

```sh
playlist-importer playlist.csv --name "My discoveries"
```

Replace `playlist.csv` with the downloaded file's path, or rename the file and put it in the folder where you run the command. Quote paths containing spaces.

Google sign-in happens locally for this option. Credentials are not uploaded to SideTrack or Vercel. The CLI returns a regular YouTube playlist link; availability in YouTube Music can differ. Its README explains API quotas, local token storage, and verification status. **A real-account Google import has not yet been verified during development.**

## Run on your own computer

You can skip this section if you only want to use the [hosted website](https://side-track.vercel.app/).

You need **Python 3.12**, [Git](https://git-scm.com/downloads), and an internet connection. Check Python with `python3.12 --version` on macOS/Linux or `py -3.12 --version` on Windows. Install Python 3.12 if that command is unavailable.

The commands below download SideTrack into your home folder and create a separate Python environment called `.venv`. Already cloned it? Open the existing project folder and start at the `venv` command.

### macOS or Linux — Terminal

```sh
cd ~
git clone https://github.com/IcebergSnow/SideTrack.git
cd SideTrack
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m sidetrack
```

### Windows — Command Prompt

Open **Command Prompt** from the Start menu and run:

```bat
cd /d "%USERPROFILE%"
git clone https://github.com/IcebergSnow/SideTrack.git
cd SideTrack
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m sidetrack
```

### Open the app

Keep the terminal running and open **[http://localhost:8000](http://localhost:8000)** in your browser. You should see SideTrack's URL field and **Generate** button. Try the example song from [First use](#try-it-with-one-song).

**No `.env` file, API key, Google credentials, Node.js, or frontend build is required to run SideTrack.** [`.env.example`](.env.example) documents this. Google setup is only needed if you separately choose the CLI importer.

Press **Ctrl+C** in the terminal to stop the local server. To start again later, open the project folder, activate `.venv` with the command for your operating system, and run `python -m sidetrack`.

## Deploy your own copy on Vercel

Use this if you want your own public URL. You need GitHub and Vercel accounts; you do not need to configure Google OAuth for the SideTrack website.

1. **Fork this repository** into your GitHub account using GitHub's **Fork** button. A fork is your own copy that Vercel can deploy.
2. Sign in to [Vercel](https://vercel.com/new) with GitHub. Choose **Add New → Project** and import your SideTrack fork. If it is missing, grant the Vercel GitHub integration access to that repository.
3. Check these settings:

   | Setting | Value |
   | --- | --- |
   | Framework Preset | **FastAPI** |
   | Root Directory | Repository root (`./`) |
   | Build Command | Leave the override off |
   | Output Directory | Leave the override off |
   | Install Command | Leave the override off |
   | Environment Variables | None |

4. Click **Deploy** and wait for it to finish. The repository includes the Python version, dependencies, and FastAPI entrypoint Vercel needs. You do not need to enter a server start command or a `dist` folder.
5. Open the production `.vercel.app` URL. Generate recommendations from the example song, browse to another page, and download a CSV. A successful build alone does not confirm that recommendations work from Vercel.
6. Future pushes to the connected production branch, usually `main`, redeploy your copy.

Deployment follows Vercel's [FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi) and [Python runtime documentation](https://vercel.com/docs/functions/runtimes/python). Hosting usage is subject to your Vercel plan's limits.

If the page loads but recommendations fail, open the Vercel deployment's **Logs** and reproduce the request. YouTube Music can block, throttle, or change the unofficial endpoint. A song working locally does not guarantee it will work from a hosting provider's IP address.

### Optional: enable visitor analytics

The repository already includes Vercel's plain-HTML analytics integration.

1. Open your Vercel project's **Analytics** tab and click **Enable** if needed.
2. Redeploy the project, visit its production URL, then check the dashboard.
3. If Vercel shows framework setup instructions, choose **HTML**. You do not need to add a React component or npm package.

See [Vercel's analytics setup guide](https://vercel.com/docs/analytics/quickstart). Analytics is skipped on localhost, and blockers can prevent visits from appearing. SideTrack adds no custom song or download events; [privacy details are below](#privacy-and-limitations).

## Troubleshooting

| What happens | What to try |
| --- | --- |
| The URL is rejected | Use a link to one YouTube or YouTube Music song. Playlist-only links are not supported. |
| The song is unsupported or no recommendations appear | Try an official music video or the same song's YouTube Music link. Private, deleted, restricted, or unrecognized uploads may not work. |
| Generating takes too long or fails | Check your connection and try again. If it keeps happening, try another song. The unofficial YouTube Music endpoint may be unavailable or changed. |
| **Next** fails while loading more songs | Existing pages remain available to download. Click **Next** to retry. Avoid refreshing if you want to keep those pages. |
| A page has fewer than 20 songs, or **Next** stops finding more | YouTube Music did not return enough new songs after filtering. You can still download the available pages. |
| My download has fewer songs than expected | Check **Current page** versus **Everything through this page**, your current page number, and the displayed download count. Short pages also reduce the total. |
| Recommendations disappeared | Refreshing or generating again clears them. SideTrack does not save past sessions; download a file to keep a list. |
| I downloaded a file but there is no YouTube playlist | Follow one of the [import options](#get-the-songs-into-youtube). Downloading alone does not write to your Google account. |
| The local page will not open | Keep `python -m sidetrack` running and use `http://localhost:8000`, not an HTML file opened directly from disk. Check the terminal for errors. |
| `python3.12`, `py -3.12`, or `git` is not found | Install the missing prerequisite, reopen the terminal, and check its version. |
| Python says `No module named sidetrack` or a dependency is missing | Open the SideTrack project folder, activate `.venv`, and run `python -m pip install -r requirements.txt` before starting it. |
| PowerShell blocks environment activation | Use **Command Prompt** with the Windows instructions, or run `.\.venv\Scripts\python.exe -m sidetrack` from the project folder after installing the dependencies into that environment. |
| Port 8000 is already in use | Stop the other local server if it is yours, or run `python -m uvicorn sidetrack.app:app --host 127.0.0.1 --port 8001` and open `http://localhost:8001`. |
| Vercel's build fails | Check the build logs, select **FastAPI**, and use the repository root. Leave build/output/install overrides off. |
| A Vercel link asks me to sign in | You may be using a protected preview deployment. Use your public production URL when sharing the app, or check the project's deployment-protection settings. |
| The importer picked a different recording | Transfer services may match by title/artist. Review their matches, or use the companion CLI with CSV to submit the exact video IDs. |

## Privacy and limitations

- Recommendations are **experimental and unofficial**. `ytmusicapi` is not a Google-supported API, and YouTube changes can break it. Repeating the same input may produce a different set or order of songs.
- SideTrack removes the original song, repeated video IDs, known audio/video counterparts, and obvious duplicate recordings. This uses song metadata, not audio analysis; some alternate versions may remain.
- Recommendations live in the current browser tab's memory. The app has no accounts, database, or saved playlist history. A session holds at most 2,000 songs; download them before starting over.
- SideTrack sends the seed video ID to YouTube Music. When loading more songs, the browser sends the earlier songs' IDs and metadata to SideTrack so it can filter repeats. Download files are generated in the browser.
- When enabled on Vercel, Web Analytics records standard visit/page-view information. SideTrack does not attach your pasted song URL or playlist contents to analytics events. See [Vercel's analytics privacy information](https://vercel.com/docs/analytics/privacy-policy). Your hosting provider may also retain operational logs.
- SideTrack never asks for Google credentials. An importer handles Google authorization separately and has its own permissions, limits, and privacy behavior. No audio is downloaded by SideTrack.

## For developers

<details>
<summary>Architecture and recommendation behavior</summary>

The app uses Python/FastAPI and plain HTML, CSS, and JavaScript. There is no frontend build step or server session store. Each recommendation request is independent.

The backend calls `get_watch_playlist(videoId=..., radio=True, limit=200)`. That limit is a target used by `ytmusicapi`; it may make several underlying requests and return more raw candidates. SideTrack filters them and returns up to 200 unique tracks, displayed in pages of 20. If fewer than 20 new tracks remain, it tries one additional radio request.

Deduplication uses video IDs, known audio/video counterparts, and normalized artist/title keys. It ignores packaging labels such as “Official Video” or “2011 Remaster” while retaining live/acoustic/remix qualifiers. Later pools exclude all previously loaded tracks. Old pages, including short ones, stay unchanged when a new pool arrives.

Each pool request has a 16-HTTP-request cap, a 35-second budget checked before upstream requests, and connect/read timeouts of at most 10 seconds each. The browser limits a run to 2,000 tracks. `vercel.json` sets a 60-second function limit; root `app.py` exposes the FastAPI app and `.python-version` selects Python 3.12.

The public recommendation endpoint has no application-level rate limiting. For a public deployment, use your hosting provider's access controls or firewall if traffic becomes an issue. Review YouTube's applicable terms before broader use.

CSV downloads contain `title,artist,url`; TXT uses one `Artist - Title` per line. CSV escaping also neutralizes formula-like metadata, so unusual titles/artists can gain a leading apostrophe when opened as a spreadsheet.

</details>

<details>
<summary>Tests and live recommendation checks</summary>

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

The paging implementation previously passed 48 Python tests and 8 JavaScript tests. Real local and Vercel checks exercised recommendations and refills; browser checks covered saved pages, a 20-song download, a 60-song cumulative download, and retry recovery. These observations do not guarantee availability for every song or hosting IP. A real third-party account import remains unverified; see the companion CLI's README for its separate verification status.

</details>

<details>
<summary>Project files and updating a local copy</summary>

| File or folder | Purpose |
| --- | --- |
| `app.py` | Vercel entrypoint |
| `vercel.json` / `.python-version` | Hosting and Python version settings |
| `sidetrack/app.py` | API endpoints and frontend routes |
| `sidetrack/recommendations.py` | URL parsing, YouTube Music requests, and filtering |
| `static/` | Plain HTML/CSS/JS, pagination, and download formatting |
| `scripts/check_recommendations.py` | Live local/deployed API check |
| `tests/` | Python and JavaScript tests |

To update a Git checkout, stop the local server, open the repository folder, activate `.venv`, and run:

```sh
git pull --ff-only
python -m pip install -r requirements.txt
python -m sidetrack
```

</details>
