const $ = (id) => document.getElementById(id);
let session = null;
let busy = false;
let pollTimer = null;
let renderedTracks = "";

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = !message;
}

async function api(url, body) {
  const response = await fetch(url, body === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-SideTrack": "1" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "SideTrack couldn't complete that request. Please try again.");
  return data;
}

function renderRecommendations(recommendations) {
  const key = recommendations ? JSON.stringify(recommendations) : "";
  if (key === renderedTracks) return;
  renderedTracks = key;
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
  const recommendations = session?.recommendations;
  const exporting = session?.export.status === "exporting";
  const generating = busy || session?.generating;
  $("generate-button").disabled = !session || generating || exporting;
  $("song-url").disabled = generating || exporting;
  $("generate-label").textContent = generating ? "Finding tracks…" : "Generate";
  $("loading").hidden = !generating;
  $("results").hidden = generating || !recommendations;
  renderRecommendations(recommendations);
  if (!session) return;
  const result = session.export;
  $("export-button").disabled = generating || !recommendations || ["authorizing", "exporting", "complete", "partial"].includes(result.status);
  $("export-label").textContent = ({ authorizing: "Awaiting Google…", exporting: `Exporting ${result.added}/${recommendations?.tracks.length || 0}…`, complete: "Exported ✓", partial: "Export incomplete" })[result.status] || "Export to YouTube";
  $("export-help").textContent = session.oauth_ready ? "Creates a private playlist after Google sign-in." : "Export isn't configured on this server yet.";
  $("export-status").hidden = result.status === "idle";
  $("export-status").classList.toggle("error", ["failed", "partial"].includes(result.status));
  $("export-message").textContent = exporting ? `Adding songs to your private playlist… ${result.added} of ${recommendations?.tracks.length || 0} confirmed.` : result.message;
  $("playlist-link").hidden = !result.playlist_url;
  if (result.playlist_url) {
    $("playlist-link").href = result.playlist_url;
    $("playlist-link").textContent = result.status === "complete" ? "Open your YouTube playlist" : "Open the playlist so far";
  }
}

async function refresh() {
  clearTimeout(pollTimer);
  session = await api("/api/session");
  if (session.recommendations && !$("song-url").value) $("song-url").value = session.recommendations.seed.url;
  render();
  if (session.generating || ["authorizing", "exporting"].includes(session.export.status)) {
    pollTimer = setTimeout(() => refresh().catch(pollFailed), 1500);
  }
}

function pollFailed(error) {
  showError(`${error.message} Reconnecting to check progress…`);
  pollTimer = setTimeout(() => refresh().then(() => showError("")).catch(pollFailed), 5000);
}

$("generate-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const url = $("song-url").value.trim();
  if (!url) return;
  clearTimeout(pollTimer);
  busy = true;
  showError("");
  session.recommendations = null;
  session.export = { status: "idle", message: "", added: 0, playlist_url: null };
  render();
  try {
    const result = await api("/api/recommend", { url });
    session.recommendations = result;
    $("announcement").textContent = `${result.tracks.length} recommendations ready.`;
  } catch (error) {
    showError(error.message);
  } finally {
    busy = false;
    render();
    if (session.recommendations) $("results-title").focus({ preventScroll: true });
  }
});

$("export-button").addEventListener("click", async () => {
  showError("");
  $("export-button").disabled = true;
  $("export-label").textContent = "Connecting…";
  try {
    const result = await api("/api/export", {});
    if (result.authorization_url) window.location.assign(result.authorization_url);
    else await refresh();
  } catch (error) {
    session.export = { ...session.export, status: "failed", message: error.message };
    render();
  }
});

const callbackError = new URLSearchParams(window.location.search).get("auth_error");
if (callbackError) {
  showError(callbackError === "session" ? "Your session expired or the browser blocked its cookie. Generate again using the same browser and address for Google sign-in." : "This Google sign-in link expired or was already used. Return to your recommendations and try again.");
  history.replaceState(null, "", "/");
}
render();
refresh().catch((error) => showError(error.message));
window.addEventListener("pageshow", (event) => {
  if (event.persisted) refresh().catch((error) => showError(error.message));
});
