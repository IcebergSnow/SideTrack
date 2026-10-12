import test from "node:test";
import assert from "node:assert/strict";
import { appendPages, downloadTracks, exclusionHistory, MAX_TRACKS } from "../static/pages.mjs";
import { playlistText } from "../static/downloads.mjs";

function tracks(count, start = 0) {
  return Array.from({length: count}, (_, index) => ({
    video_id: `v${String(start + index).padStart(10, "0")}`,
    title: `Song ${start + index}`, artists: ["Artist"], counterpart_id: null,
    url: `https://www.youtube.com/watch?v=v${String(start + index).padStart(10, "0")}`,
  }));
}

test("cached pages contain 20 songs and cumulative downloads stop at the current page", () => {
  const all = tracks(200);
  const pages = appendPages([], all);
  assert.equal(pages.length, 10);
  assert.deepEqual(downloadTracks(pages, 2, "current"), all.slice(40, 60));
  assert.deepEqual(downloadTracks(pages, 2, "through"), all.slice(0, 60));
  assert.deepEqual(downloadTracks(pages, 0, "through"), all.slice(0, 20));
  assert.equal(playlistText(downloadTracks(pages, 2, "through")).trimEnd().split("\n").length, 60);
});

test("refilling after a short page never changes or renumbers earlier pages", () => {
  const first = tracks(23);
  const pages = appendPages([], first);
  const updated = appendPages(pages, tracks(25, 23));
  assert.deepEqual(updated.map(page => page.length), [20, 3, 20, 5]);
  assert.strictEqual(updated[1], pages[1]);
  assert.deepEqual(downloadTracks(updated, 1, "through"), first);
  assert.equal(downloadTracks(updated, 2, "through").length, 43);
  assert.deepEqual(appendPages(updated, []), updated);
});

test("refill guards against repeated IDs within and across pools", () => {
  const original = tracks(20);
  const fresh = tracks(20, 20);
  const updated = appendPages(appendPages([], original), [...original, ...fresh, ...fresh]);
  assert.deepEqual(updated.flat(), [...original, ...fresh]);
});

test("exclusions contain every cached song including known counterparts", () => {
  const all = tracks(45);
  all[0].counterpart_id = "kJQP7kiw5Fk";
  const history = exclusionHistory(appendPages([], all));
  assert.equal(history.length, 45);
  assert.equal(history[0].counterpart_id, "kJQP7kiw5Fk");
  assert.equal(history[44].video_id, all[44].video_id);
  assert.equal(history[0].url, undefined);
});

test("the browsing limit keeps earlier pages and never exceeds the API history cap", () => {
  const pages = appendPages([], tracks(MAX_TRACKS - 10));
  const updated = appendPages(pages, tracks(200, MAX_TRACKS - 10));
  assert.equal(updated.flat().length, MAX_TRACKS);
  assert.deepEqual(updated.slice(0, pages.length), pages);
});
