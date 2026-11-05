/* Shared by all pages: data loading, the move rule, navigation, shortlist. */
const NUMERIC = [
  {key: "launches_next_7d", label: "Launches in 7 days", unit: "launches"},
  {key: "launches_next_30d", label: "Launches in 30 days", unit: "launches"},
  {key: "days_to_next_launch", label: "Days to next launch", unit: "days"},
  {key: "days_in_space", label: "Days in space", unit: "days"},
  {key: "eva_hours", label: "Spacewalk hours", unit: "hours"},
];
const PAGES = [["index.html", "Today"], ["browse.html", "Browse"], ["trends.html", "Trends"]];

function parseCSV(text) {
  const rows = []; let row = [], field = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') q = false;
      else field += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  const head = rows.shift() || [];
  return rows.filter(r => r.length === head.length).map(r => {
    const o = {}; head.forEach((h, i) => o[h] = r[i]);
    NUMERIC.forEach(n => o[n.key] = o[n.key] === "" ? null : Number(o[n.key]));
    return o;
  });
}

async function loadData() {
  const [h, s] = await Promise.all([
    fetch("data/history.csv", {cache: "no-cache"}).then(r => { if (!r.ok) throw new Error(r.status); return r.text(); }),
    fetch("data/status.json", {cache: "no-cache"}).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }),
  ]);
  const history = parseCSV(h);
  const dates = [...new Set(history.map(r => r.date))].sort();
  return {history, status: s, dates};
}

function rowsOn(history, date) { return history.filter(r => r.date === date); }

/* Latest day in the history and the day before it (the "previous run"). */
function latestAndPrevious(data) {
  const d = data.dates;
  const latest = d[d.length - 1], prev = d.length > 1 ? d[d.length - 2] : null;
  return {latest, prev, cur: latest ? rowsOn(data.history, latest) : [], old: prev ? rowsOn(data.history, prev) : []};
}

/* The move rule (same as tracker/moves.py): providers only,
   score = |change in launches_next_30d| + |change in launches_next_7d|. */
function computeMoves(old, cur, limit = 10) {
  const prev = new Map(old.map(r => [r.item_id, r]));
  const now = new Map(cur.map(r => [r.item_id, r]));
  const moves = [];
  for (const [id, r] of now) {
    const b = prev.get(id);
    if (!b || r.kind !== "provider") continue;
    if ([b.launches_next_30d, r.launches_next_30d, b.launches_next_7d, r.launches_next_7d].includes(null)) continue;
    const score = Math.abs(r.launches_next_30d - b.launches_next_30d) + Math.abs(r.launches_next_7d - b.launches_next_7d);
    if (score) moves.push({item: r.item, score, old30: b.launches_next_30d, new30: r.launches_next_30d, old7: b.launches_next_7d, new7: r.launches_next_7d});
  }
  moves.sort((a, c) => c.score - a.score || a.item.localeCompare(c.item));
  return {
    moves: moves.slice(0, limit),
    added: [...now.keys()].filter(i => !prev.has(i)).map(i => now.get(i).item).sort(),
    gone: [...prev.keys()].filter(i => !now.has(i)).map(i => prev.get(i).item).sort(),
  };
}

function fmt(v) {
  if (v === null || v === undefined) return "";
  return Number.isInteger(v) ? String(v) : v.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}
function deltaHTML(now, before) {
  if (now === null || before === null || before === undefined) return "";
  const d = Math.round((now - before) * 100) / 100;
  if (d === 0) return '<span class="delta flat">0</span>';
  return `<span class="delta ${d > 0 ? "up" : "down"}">${d > 0 ? "+" : ""}${fmt(d)}</span>`;
}
function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }

/* Shortlist, kept in the browser. */
function getShortlist() {
  try { return new Set(JSON.parse(localStorage.getItem("shortlist") || "[]")); } catch (e) { return new Set(); }
}
function saveShortlist(set) {
  try { localStorage.setItem("shortlist", JSON.stringify([...set])); } catch (e) {}
}

function renderNav(active) {
  const nav = document.createElement("nav");
  nav.innerHTML = '<a class="brand" href="index.html">🚀 Space Tracker</a>' +
    PAGES.map(([h, l]) => `<a class="tab${h === active ? " active" : ""}" href="${h}">${l}</a>`).join("");
  document.body.prepend(nav);
  const off = document.createElement("div");
  off.className = "offline"; off.id = "offline";
  off.textContent = "Offline: showing the last data this device loaded.";
  nav.after(off);
  const upd = () => off.classList.toggle("show", !navigator.onLine);
  addEventListener("online", upd); addEventListener("offline", upd); upd();
}

if ("serviceWorker" in navigator) {
  addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}

async function start(active, render) {
  renderNav(active);
  const main = document.querySelector("main");
  try {
    const data = await loadData();
    render(data, main);
  } catch (e) {
    main.insertAdjacentHTML("afterbegin", '<p class="chip bad">Could not load the data files: ' + esc(e.message) + "</p>");
  }
}
