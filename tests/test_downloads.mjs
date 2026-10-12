import test from "node:test";
import assert from "node:assert/strict";
import { playlistText, playlistCsv } from "../static/downloads.mjs";

const tracks = [
  { title: 'A "Song", Part 1', artists: ["Björk", "Guest"], url: "https://www.youtube.com/watch?v=fJ9rUzIMcZQ" },
  { title: "Second\r\nSong", artists: ["Artist\tName"], url: "https://www.youtube.com/watch?v=kJQP7kiw5Fk" },
];

test("TXT preserves order and Unicode, with one artist/title pair per line", () => {
  assert.equal(playlistText(tracks), 'Björk, Guest - A "Song", Part 1\nArtist Name - Second Song\n');
});

test("CSV uses importer headers and escapes quotes, commas, and line breaks", () => {
  assert.equal(playlistCsv(tracks), 'title,artist,url\r\n"A ""Song"", Part 1","Björk, Guest","https://www.youtube.com/watch?v=fJ9rUzIMcZQ"\r\n"Second Song","Artist Name","https://www.youtube.com/watch?v=kJQP7kiw5Fk"\r\n');
});

test("CSV neutralizes formula-like metadata before spreadsheet import", () => {
  for (const prefix of ["=", "+", "-", "@", "\t=", "\r\n=", " ="]) {
    const csv = playlistCsv([{ title: `${prefix}formula`, artists: ["@artist"], url: tracks[0].url }]);
    assert.ok(csv.split("\r\n")[1].startsWith('"\''));
    assert.ok(csv.includes(',"\'@artist",'));
  }
});
