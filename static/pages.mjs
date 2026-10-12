export const PAGE_SIZE = 20;
export const MAX_TRACKS = 2000;

export function appendPages(pages, tracks) {
  const previous = pages.flat();
  const seen = new Set(previous.map((track) => track.video_id));
  const fresh = tracks.filter((track) => {
    if (seen.has(track.video_id)) return false;
    seen.add(track.video_id);
    return true;
  }).slice(0, Math.max(0, MAX_TRACKS - previous.length));
  const added = [];
  for (let start = 0; start < fresh.length; start += PAGE_SIZE) {
    added.push(fresh.slice(start, start + PAGE_SIZE));
  }
  // Preserve earlier pages, including a short final page, when more songs arrive.
  return [...pages, ...added];
}

export function downloadTracks(pages, index, scope) {
  return scope === "through" ? pages.slice(0, index + 1).flat() : (pages[index] || []);
}

export function exclusionHistory(pages) {
  return pages.flat().map(({ video_id, title, artists, counterpart_id }) => ({ video_id, title, artists, counterpart_id }));
}
