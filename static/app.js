import { playlistText, playlistCsv } from "/static/downloads.mjs";

const $ = (id) => document.getElementById(id);
let recommendations = null;
let busy = false;

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = !message;
}

function renderRecommendations() {
  $("track-list").replaceChildren();
  if (!recommendations) return;
  const { seed, tracks, note } = recommendations;
  $("seed-title").textContent = seed.title;
  $("seed-artist").textContent = seed.artists.join(", ");
  $("seed-link").href = seed.url;
  $("seed-link").setAttribute("aria-label", `Listen to ${seed.title} on YouTube (opens a new tab)`);
  $("track-count").textContent = `(${tracks.length})`;
  $("recommendation-note").textContent = note;
  $("recommendation-note").hidden = !note;
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
  $("generate-button").disabled = busy;
  $("song-url").disabled = busy;
  $("generate-label").textContent = busy ? "Finding tracks…" : "Generate";
  $("loading").hidden = !busy;
  $("results").hidden = busy || !recommendations;
}

$("generate-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const url = $("song-url").value.trim();
  if (!url) return;
  busy = true;
  recommendations = null;
  showError("");
  $("announcement").textContent = "";
  render();
  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: AbortSignal.timeout(65000),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "SideTrack couldn't complete that request. Please try again.");
    if (!data?.seed || !Array.isArray(data.tracks) || !data.tracks.length) {
      throw new Error("No recommendations were returned. Try another music link.");
    }
    recommendations = data;
    renderRecommendations();
    $("announcement").textContent = `${data.tracks.length} recommendations ready.`;
  } catch (error) {
    const message = error.name === "TimeoutError"
      ? "Recommendations took too long. Please try again."
      : error instanceof TypeError
        ? "Couldn't connect to SideTrack. Check your connection and try again."
        : error.message;
    showError(message);
  } finally {
    busy = false;
    render();
    if (recommendations) $("results-title").focus({ preventScroll: true });
  }
});

function download(format) {
  if (!recommendations || busy) return;
  const content = format === "csv" ? playlistCsv(recommendations.tracks) : playlistText(recommendations.tracks);
  const type = format === "csv" ? "text/csv;charset=utf-8" : "text/plain;charset=utf-8";
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `sidetrack-${recommendations.seed.video_id}.${format}`;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("announcement").textContent = `${format.toUpperCase()} download started.`;
}

$("download-txt").addEventListener("click", () => download("txt"));
$("download-csv").addEventListener("click", () => download("csv"));
render();
