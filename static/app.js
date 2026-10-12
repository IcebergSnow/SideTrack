import { playlistText, playlistCsv } from "/static/downloads.mjs";
import { appendPages, downloadTracks, exclusionHistory, MAX_TRACKS } from "/static/pages.mjs";

const $ = (id) => document.getElementById(id);
let recommendations = null;
let pages = [];
let pageIndex = 0;
let exhausted = false;
let busy = "";

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = !message;
}

function errorMessage(error) {
  if (error.name === "TimeoutError") return "Recommendations took too long. Please try again.";
  if (error instanceof TypeError) return "Couldn't connect to SideTrack. Check your connection and try again.";
  return error.message;
}

async function fetchPool(url, exclude = []) {
  const response = await fetch("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, exclude }),
    signal: AbortSignal.timeout(65000),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "SideTrack couldn't complete that request. Please try again.");
  if (!data?.seed || !Array.isArray(data.tracks) || (!data.tracks.length && !data.exhausted)) {
    throw new Error("No recommendations were returned. Try another music link.");
  }
  return data;
}

function selectedDownload() {
  return downloadTracks(pages, pageIndex, $("download-scope").value);
}

function renderRecommendations() {
  $("track-list").replaceChildren();
  if (!recommendations || !pages.length) return;
  const { seed, note } = recommendations;
  const tracks = pages[pageIndex];
  $("seed-title").textContent = seed.title;
  $("seed-artist").textContent = seed.artists.join(", ");
  $("seed-link").href = seed.url;
  $("seed-link").setAttribute("aria-label", `Listen to ${seed.title} on YouTube (opens a new tab)`);
  $("track-count").textContent = `(${tracks.length})`;
  $("recommendation-note").textContent = note;
  $("recommendation-note").hidden = !note || pageIndex !== pages.length - 1;
  $("track-list").start = pages.slice(0, pageIndex).flat().length + 1;
  for (const track of tracks) {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = track.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.setAttribute("aria-label", `${track.title} by ${track.artists.join(", ")} (opens YouTube in a new tab)`);
    link.textContent = track.title;
    const artist = document.createElement("span");
    artist.className = "track-artist";
    artist.textContent = ` — ${track.artists.join(", ")}`;
    const duration = document.createElement("span");
    duration.className = "track-duration";
    duration.textContent = track.duration ? ` (${track.duration})` : "";
    li.append(link, artist, duration);
    $("track-list").append(li);
  }
}

function render() {
  $("generate-button").disabled = Boolean(busy);
  $("song-url").disabled = Boolean(busy);
  $("generate-label").textContent = busy === "generate" ? "Finding tracks…" : "Generate";
  $("loading").hidden = busy !== "generate";
  $("more-loading").hidden = busy !== "more";
  $("results").hidden = busy === "generate" || !pages.length;
  $("previous-page").disabled = Boolean(busy) || pageIndex === 0;
  $("next-page").disabled = Boolean(busy) || (exhausted && pageIndex === pages.length - 1);
  $("next-page").textContent = busy === "more" ? "Finding more…" : "Next";
  $("page-status").textContent = pages.length ? `Page ${pageIndex + 1} of ${pages.length}` : "";
  $("download-count").textContent = `${selectedDownload().length} songs in this download.`;
  renderRecommendations();
}

function applyPoolLimit() {
  if (pages.flat().length >= MAX_TRACKS) {
    exhausted = true;
    recommendations.note = `Reached ${MAX_TRACKS.toLocaleString()} songs. Download your pages or generate a new list.`;
  }
}

$("generate-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const url = $("song-url").value.trim();
  if (!url) return;
  busy = "generate";
  recommendations = null;
  pages = [];
  pageIndex = 0;
  exhausted = false;
  showError("");
  $("announcement").textContent = "";
  render();
  try {
    const result = await fetchPool(url);
    if (!result.tracks.length) throw new Error("No recommendations were returned. Try another music link.");
    recommendations = result;
    pages = appendPages([], result.tracks);
    applyPoolLimit();
    $("announcement").textContent = `${result.tracks.length} recommendations ready in ${pages.length} pages.`;
  } catch (error) {
    showError(errorMessage(error));
  } finally {
    busy = "";
    render();
    if (pages.length) $("results-title").focus({ preventScroll: true });
  }
});

$("previous-page").addEventListener("click", () => {
  if (busy || pageIndex === 0) return;
  pageIndex -= 1;
  render();
  $("results-title").focus({ preventScroll: true });
});

$("next-page").addEventListener("click", async () => {
  if (busy || !pages.length) return;
  if (pageIndex < pages.length - 1) {
    pageIndex += 1;
    render();
    $("results-title").focus({ preventScroll: true });
    return;
  }
  if (exhausted) return;
  busy = "more";
  showError("");
  render();
  try {
    const result = await fetchPool(recommendations.seed.url, exclusionHistory(pages));
    const previousCount = pages.length;
    const updatedPages = appendPages(pages, result.tracks);
    if (updatedPages.length === previousCount) {
      exhausted = true;
      recommendations.note = "No more new recommendations found right now. Your previous pages are still available to download.";
    } else {
      pages = updatedPages;
      pageIndex = previousCount;
      recommendations.note = result.note;
      applyPoolLimit();
    }
  } catch (error) {
    showError(`${errorMessage(error)} Your previous pages are still here; click Next to retry.`);
  } finally {
    busy = "";
    render();
    $("results-title").focus({ preventScroll: true });
  }
});

function download(format) {
  const tracks = selectedDownload();
  if (!recommendations || !tracks.length) return;
  const content = format === "csv" ? playlistCsv(tracks) : playlistText(tracks);
  const type = format === "csv" ? "text/csv;charset=utf-8" : "text/plain;charset=utf-8";
  const url = URL.createObjectURL(new Blob([content], { type }));
  const scope = $("download-scope").value === "through" ? `pages-1-${pageIndex + 1}` : `page-${pageIndex + 1}`;
  const link = document.createElement("a");
  link.href = url;
  link.download = `sidetrack-${recommendations.seed.video_id}-${scope}.${format}`;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("announcement").textContent = `${format.toUpperCase()} download started: ${tracks.length} songs.`;
}

$("download-scope").addEventListener("change", render);
$("download-txt").addEventListener("click", () => download("txt"));
$("download-csv").addEventListener("click", () => download("csv"));
render();
