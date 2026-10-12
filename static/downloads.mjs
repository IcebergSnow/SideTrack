// One track per line, using the importer's artist/title matching format.
function singleLine(value) {
  return String(value).replace(/[\r\n\t]+/g, " ").trim();
}

export function playlistText(tracks) {
  return tracks.map((track) => `${singleLine(track.artists.join(", "))} - ${singleLine(track.title)}`).join("\n") + "\n";
}

function csvCell(value) {
  let text = singleLine(value);
  // Metadata is untrusted. Prevent spreadsheet formula execution on opening.
  if (/^[=+@-]/.test(text)) text = "'" + text;
  return `"${text.replaceAll('"', '""')}"`;
}

export function playlistCsv(tracks) {
  const rows = tracks.map((track) => [track.title, track.artists.join(", "), track.url].map(csvCell).join(","));
  return "title,artist,url\r\n" + rows.join("\r\n") + "\r\n";
}
