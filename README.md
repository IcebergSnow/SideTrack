# SideTrack

Find similar music from a single YouTube song link. Browse the recommendations, then download a list to import into your music library.

**[Open SideTrack →](https://side-track.vercel.app/)**

No installation or sign-in is needed to use the website. SideTrack uses experimental, unofficial `ytmusicapi` recommendations and does not download audio.

[First use](#try-it-with-one-song) · [Downloads](#choose-what-to-download) · [Import to YouTube](#get-the-songs-into-youtube) · [Troubleshooting](#troubleshooting)

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

Follow the [importer's step-by-step guide](https://github.com/IcebergSnow/SideTrack_CLI_PlaylistImporter#readme) to install it, set up Google access, and import your CSV. You need Python, Git, and your own Google Desktop OAuth client; the guide walks through each step.

Google sign-in happens on your computer. The CLI returns a YouTube playlist link when you import; wait for its completion message before opening the finished playlist. Some videos may be available on regular YouTube but unavailable in YouTube Music.

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
| The importer picked a different recording | Transfer services may match by title/artist. Review their matches, or use the companion CLI with CSV to submit the exact video IDs. |

## Privacy and limitations

- Recommendations are **experimental and unofficial**. `ytmusicapi` is not a Google-supported API, and YouTube changes can break it. Repeating the same input may produce a different set or order of songs.
- SideTrack removes the original song, repeated video IDs, known audio/video counterparts, and obvious duplicate recordings. This uses song metadata, not audio analysis; some alternate versions may remain.
- Recommendations live in the current browser tab's memory. The app has no accounts, database, or saved playlist history. A session holds at most 2,000 songs; download them before starting over.
- SideTrack sends the seed video ID to YouTube Music. When loading more songs, the browser sends the earlier songs' IDs and metadata to SideTrack so it can filter repeats. Download files are generated in the browser.
- When enabled on Vercel, Web Analytics records standard visit/page-view information. SideTrack does not attach your pasted song URL or playlist contents to analytics events. See [Vercel's analytics privacy information](https://vercel.com/docs/analytics/privacy-policy). The website's hosting provider may also retain operational logs.
- SideTrack never asks for Google credentials. An importer handles Google authorization separately and has its own permissions, limits, and privacy behavior. No audio is downloaded by SideTrack.

To run a local or hosted copy of SideTrack, see the separate [self-hosting guide](docs/self-hosting.md).
