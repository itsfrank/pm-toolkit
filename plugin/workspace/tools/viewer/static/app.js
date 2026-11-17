// PM wiki viewer: renders workspace markdown, links citations, searches, shows what needs
// attention, and records notes, requests and documents the PM adds.
// Plain browser JS, no dependencies. All document text is escaped; no raw HTML passthrough.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { tree: [], path: "", text: "", sha: "", notes: [], cards: {}, pending: null };
const ORDER = ["wiki", "INDEX.md", "pages", "reports", "sources", "work", "design", "mockups", "products", "systems", "raw", "refs"];

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function api(url, opts) {
  const r = await fetch(url, opts);
  const body = await r.json();
  if (!r.ok) throw new Error(body.error || r.statusText);
  return body;
}
// Every write carries a header only this page can send; the server refuses posts without it.
function post(url, body, headers) {
  const json = !(body instanceof Blob);
  return api(url, { method: "POST", body: json ? JSON.stringify(body || {}) : body,
    headers: Object.assign({ "X-PM-Viewer": "1", "Content-Type": json ? "application/json" : "application/octet-stream" }, headers) });
}
// ---------- paths and routing ----------
function dirname(p) { return p.includes("/") ? p.slice(0, p.lastIndexOf("/")) : ""; }
function normalize(p) {
  const out = [];
  for (const part of p.split("/")) {
    if (part === "..") out.pop();
    else if (part && part !== ".") out.push(part);
  }
  return out.join("/");
}
function route() {
  const h = decodeURIComponent(location.hash.replace(/^#\/?/, ""));
  const [path, query] = h.split("?");
  const q = new URLSearchParams(query || "");
  return { path, line: parseInt(q.get("line") || "0", 10), anchor: q.get("h") || "", q: q.get("q") || "", in: q.get("in") || "", hl: q.get("hl") || "" };
}

// ---------- frontmatter ----------
function splitFront(text) {
  const m = /^---\n([\s\S]*?)\n---\n/.exec(text);
  if (!m) return { fields: {}, body: text, offset: 0 };
  const fields = {};
  for (const line of m[1].split("\n")) {
    const mm = /^([\w-]+):\s*(.*)$/.exec(line);
    if (mm) fields[mm[1]] = mm[2].replace(/\s+#.*$/, "").trim();
  }
  return { fields, body: text.slice(m[0].length), offset: m[0].split("\n").length - 1 };
}

// ---------- inline markdown ----------
function rawHref(path) { return "/api/raw?path=" + encodeURIComponent(path); }
function designHref(path) { return "/api/design?path=" + encodeURIComponent(path); }
// Links from a source card to its saved copy (in the viewer for markdown, else the file)
// and to the original where it lives.
function sourceLinks(fields) {
  const links = [];
  const origin = (fields.origin || "").trim();
  if (origin && !/^https?:/i.test(origin)) {
    const p = normalize("wiki/" + origin.replace(/^wiki\//, ""));
    links.push(p.endsWith(".md") ? '<a href="#/' + esc(p) + '">Saved copy</a>'
      : '<a href="' + esc(rawHref(p)) + '" target="_blank" rel="noopener noreferrer">Saved copy (' + esc(p.split(".").pop()) + ")</a>");
  }
  for (const u of [fields.origin_url, /^https?:/i.test(origin) ? origin : ""]) {
    const h = u && safeHref(u);
    if (h && h.external) { links.push('<a href="' + esc(h.href) + '" target="_blank" rel="noopener noreferrer">Original ↗</a>'); break; }
  }
  return links.length ? '<div class="source-links">Source document: ' + links.join(" · ") + "</div>"
    : '<div class="source-links missing">No source document recorded on this card.</div>';
}
function hideTip() { $("tip").hidden = true; }
function safeHref(url) {
  const u = url.trim();
  if (/^(https?:|mailto:)/i.test(u)) return { href: u, external: true };
  if (/^[a-z][\w+.-]*:/i.test(u)) return null;              // javascript:, data:, file: ...
  if (u.startsWith("#")) return { href: "#/" + state.path + "?h=" + encodeURIComponent(u.slice(1)) };
  const [p, frag] = u.split("#");
  const target = normalize((dirname(state.path) ? dirname(state.path) + "/" : "") + p);
  if (target.endsWith(".md")) return { href: "#/" + target + (frag ? "?h=" + encodeURIComponent(frag) : "") };
  if (target.startsWith("wiki/raw/")) return { href: rawHref(target), external: true };  // original file
  if (target.startsWith("design/")) return { href: designHref(target), external: true };  // mockup or reference
  return { href: null, text: target };                     // other non-markdown file: show, don't link
}

function inline(src) {
  const slots = [];
  const hold = (html) => "\u0000" + (slots.push(html) - 1) + "\u0000";
  let s = src.replace(/\u0000/g, "");
  s = s.replace(/(`+)([\s\S]*?[^`])\1(?!`)/g, (_, __, code) => hold("<code>" + esc(code.trim()) + "</code>"));
  s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)[^)]*\)/g, (_, alt, url) => {
    const h = safeHref(url);  // screenshots under design/ show inline; other images stay labels
    if (h && h.href && h.href.startsWith("/api/design?") && /\.(png|jpe?g|gif)$/i.test(url))
      return hold('<a href="' + esc(h.href) + '" target="_blank" rel="noopener noreferrer"><img class="shot" alt="' + esc(alt) + '" src="' + esc(h.href) + '"></a>');
    return hold('<span class="lbl">[image: ' + esc(alt) + "]</span>");
  });
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g, (_, label, url) => {
    const h = safeHref(url);
    if (!h) return hold(inline(label));
    if (!h.href) return hold('<span title="' + esc(h.text) + '">' + inline(label) + "</span>");
    return hold('<a href="' + esc(h.href) + '"' + (h.external ? ' target="_blank" rel="noopener noreferrer"' : "") + ">" + inline(label) + "</a>");
  });
  s = s.replace(/\[(S-\d{4}\b[^\]]*)\](?!\()/g, (_, inner) => {
    const parts = inner.split(/(S-\d{4})/).map((x) => /^S-\d{4}$/.test(x)
      ? '<a class="cite" data-card="' + x + '" href="#/wiki/sources/' + x + '.md">' + x + "</a>" : esc(x));
    return hold('<span class="cite">[' + parts.join("") + "]</span>");
  });
  s = s.replace(/<(https?:\/\/[^>\s]+)>/g, (_, url) => hold('<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(url) + "</a>"));
  s = esc(s);
  s = s.replace(/\*\*([^*]+?)\*\*|__([^_]+?)__/g, (_, a, b) => "<strong>" + (a || b) + "</strong>");
  s = s.replace(/(^|[^\w*])\*([^*\s][^*]*?)\*(?!\w)/g, "$1<em>$2</em>");
  s = s.replace(/(^|[^\w])_([^_\s][^_]*?)_(?!\w)/g, "$1<em>$2</em>");
  s = s.replace(/~~([^~]+)~~/g, "<del>$1</del>");
  s = s.replace(/\((inferred|assumption|unknown)\)/g, '<span class="lbl $1">($1)</span>');
  return s.replace(/\u0000(\d+)\u0000/g, (_, i) => slots[+i]);
}

// ---------- block markdown ----------
const RE = {
  fence: /^\s{0,3}(`{3,}|~{3,})/,
  heading: /^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$/,
  hr: /^\s{0,3}([-*_])(\s*\1){2,}\s*$/,
  quote: /^\s{0,3}>\s?/,
  item: /^(\s*)([-*+]|\d{1,9}[.)])(\s+|$)/,
  tsep: /^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$/,
};
const indentOf = (l) => l.match(/^\s*/)[0].replace(/\t/g, "    ").length;
const blank = (l) => !l.trim();
const startsBlock = (lines, i) => RE.fence.test(lines[i]) || RE.heading.test(lines[i]) || RE.hr.test(lines[i]) ||
  RE.quote.test(lines[i]) || RE.item.test(lines[i]) || isTable(lines, i);
function isTable(lines, i) { return lines[i].includes("|") && i + 1 < lines.length && RE.tsep.test(lines[i + 1]) && lines[i + 1].includes("-"); }
function cells(l) { return l.trim().replace(/^\|/, "").replace(/\|$/, "").split(/(?<!\\)\|/).map((c) => c.trim().replace(/\\\|/g, "|")); }
function slug(t) { return t.toLowerCase().replace(/<[^>]+>/g, "").replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "-"); }

// lines: array of strings; nos: their 1-based source line numbers.
function blocks(lines, nos) {
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i], n = nos[i];
    if (blank(line)) { i++; continue; }
    let m;
    if ((m = RE.fence.exec(line))) {
      const fence = m[1], lang = line.slice(m[0].length).trim().split(/\s/)[0];
      const body = [];
      i++;
      while (i < lines.length && !new RegExp("^\\s{0,3}" + fence[0] + "{" + fence.length + ",}\\s*$").test(lines[i])) body.push(lines[i++]);
      i++;
      out.push('<pre data-line="' + n + '"><code' + (lang ? ' class="lang-' + esc(lang) + '"' : "") + ">" + esc(body.join("\n")) + "</code></pre>");
    } else if ((m = RE.heading.exec(line))) {
      const lvl = m[1].length, html = inline(m[2]);
      out.push("<h" + lvl + ' id="' + esc(slug(m[2])) + '" data-line="' + n + '">' + html + "</h" + lvl + ">");
      i++;
    } else if (RE.hr.test(line)) {
      out.push('<hr data-line="' + n + '">');
      i++;
    } else if (isTable(lines, i)) {
      const head = cells(line);
      let html = '<table data-line="' + n + '"><thead><tr>' + head.map((c) => "<th>" + inline(c) + "</th>").join("") + "</tr></thead><tbody>";
      i += 2;
      while (i < lines.length && !blank(lines[i]) && lines[i].includes("|")) {
        html += '<tr data-line="' + nos[i] + '">' + cells(lines[i]).map((c) => "<td>" + inline(c) + "</td>").join("") + "</tr>";
        i++;
      }
      out.push(html + "</tbody></table>");
    } else if (RE.quote.test(line)) {
      const sub = [], subNos = [];
      while (i < lines.length && !blank(lines[i]) && (RE.quote.test(lines[i]) || !startsBlock(lines, i))) {
        sub.push(lines[i].replace(RE.quote, "")); subNos.push(nos[i]); i++;
      }
      out.push('<blockquote data-line="' + n + '">\n' + blocks(sub, subNos) + "\n</blockquote>");
    } else if (RE.item.test(line)) {
      i = list(lines, nos, i, out);
    } else {
      const para = [line.trim()];
      i++;
      while (i < lines.length && !blank(lines[i]) && !startsBlock(lines, i)) para.push(lines[i++].trim());
      out.push('<p data-line="' + n + '">' + inline(para.join("\n")).replace(/\n/g, " ") + "</p>");
    }
  }
  return out.join("\n");
}

function list(lines, nos, i, out) {
  const first = RE.item.exec(lines[i]);
  const base = indentOf(first[1]), ordered = /\d/.test(first[2]);
  const start = ordered ? parseInt(first[2], 10) : 1;
  const items = [];
  while (i < lines.length) {
    const m = RE.item.exec(lines[i]);
    if (!m || indentOf(m[1]) !== base || /\d/.test(m[2]) !== ordered) break;
    const contentCol = m[0].length;
    const body = [lines[i].slice(contentCol)], bodyNos = [nos[i]];
    const line = nos[i];
    i++;
    while (i < lines.length) {
      const l = lines[i];
      if (blank(l)) {
        let j = i + 1;
        while (j < lines.length && blank(lines[j])) j++;
        if (j < lines.length && indentOf(lines[j]) > base) { body.push(""); bodyNos.push(nos[i]); i++; continue; }
        break;
      }
      if (indentOf(l) > base) { body.push(l.slice(Math.min(contentCol, indentOf(l)))); bodyNos.push(nos[i]); i++; continue; }
      if (RE.item.test(l) || startsBlock(lines, i)) break;
      body.push(l.trim()); bodyNos.push(nos[i]); i++;           // lazy continuation
    }
    items.push({ line, body, bodyNos });
  }
  const tag = ordered ? "ol" : "ul";
  let html = "<" + tag + (ordered && start !== 1 ? ' start="' + start + '"' : "") + ' data-line="' + items[0].line + '">';
  for (const it of items) {
    let k = 0;
    const text = [];
    while (k < it.body.length && !blank(it.body[k]) && (k === 0 || !startsBlock(it.body, k))) text.push(it.body[k++].trim());
    let head = text.join("\n"), cls = "";
    const task = /^\[([ xX])\]\s+/.exec(head);
    if (task) {
      cls = ' class="task"';
      head = head.slice(task[0].length);
    }
    const box = task ? '<input type="checkbox" disabled' + (task[1] !== " " ? " checked" : "") + "> " : "";
    const rest = blocks(it.body.slice(k), it.bodyNos.slice(k));
    html += "<li" + cls + ' data-line="' + it.line + '">' + box + inline(head).replace(/\n/g, " ") + (rest ? "\n" + rest : "") + "</li>\n";
  }
  out.push(html + "</" + tag + ">");
  return i;
}

function render(text) {
  const { fields, body, offset } = splitFront(text);
  const lines = body.split("\n");
  return { fields, html: blocks(lines, lines.map((_, k) => k + 1 + offset)) };
}

// ---------- sidebar ----------
function rank(name) { const k = ORDER.indexOf(name); return k < 0 ? 99 : k; }
function fileLink(f) {
  const label = /^S-\d{4}$/.test(f.path.split("/").pop().replace(/\.md$/, "")) && f.title
    ? f.path.split("/").pop().replace(/\.md$/, "") + " · " + f.title : (f.title || f.path);
  return '<a class="file' + (f.path === state.path ? " active" : "") + '" href="#/' + esc(f.path) + '" title="' + esc(f.path) +
    '"><span class="dot ' + esc(f.status) + '"></span><span class="t">' + esc(label) + "</span></a>";
}
function drawTree() {
  const filter = $("filter").value.trim().toLowerCase();
  if (filter) {
    $("tree").innerHTML = state.tree.filter((f) => (f.path + " " + f.title).toLowerCase().includes(filter)).map(fileLink).join("") || "<p>No files match.</p>";
    return;
  }
  const root = { dirs: {}, files: [] };
  for (const f of state.tree) {
    const parts = f.path.split("/");
    let node = root;
    for (const d of parts.slice(0, -1)) node = node.dirs[d] = node.dirs[d] || { dirs: {}, files: [] };
    node.files.push(f);
  }
  const draw = (node, prefix) => {
    let html = node.files.sort((a, b) => rank(a.path.split("/").pop()) - rank(b.path.split("/").pop()) || a.path.localeCompare(b.path)).map(fileLink).join("");
    for (const d of Object.keys(node.dirs).sort((a, b) => rank(a) - rank(b) || a.localeCompare(b))) {
      const p = prefix + d;
      const open = ["wiki", "wiki/pages", "work"].includes(p) || state.path.startsWith(p + "/");
      html += '<details class="group"' + (open ? " open" : "") + "><summary>" + esc(d) + "</summary>" + draw(node.dirs[d], p + "/") + "</details>";
    }
    return html;
  };
  $("tree").innerHTML = draw(root, "");
}
// ---------- search ----------
// Results are a page of their own (#/search?q=…&in=pages), so Back returns to them.
// Matched words arrive wrapped in \u0001…\u0002; everything else is escaped.
const KINDS = { pages: "Pages", reports: "Reports", sources: "Sources", originals: "Originals", work: "Work", design: "Design", other: "Other" };
const marked = (t) => esc(t).replace(/\u0001/g, "<mark>").replace(/\u0002/g, "</mark>");
// A line of markdown as plain text: no heading, list, table or link syntax.
function plain(t) {
  return t.replace(/^(\s*([-*+>]|\d+[.)]|#{1,6})\s+)+/, "").replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/^\s*\|\s*|\s*\|\s*$/g, "").replace(/\s*\|\s*/g, " · ").replace(/\*\*|__|`/g, "");
}
function hitHref(h, line, words) {
  return h.path.endsWith(".md") ? '"#/' + esc(h.path) + "?line=" + (line || 0) + (words ? "&hl=" + esc(encodeURIComponent(words)) : "") + '"'
    : '"' + esc(rawHref(h.path)) + '" target="_blank" rel="noopener noreferrer"';
}
function searchHash(q, kind) { return "#/search?q=" + encodeURIComponent(q) + (kind ? "&in=" + kind : ""); }
async function drawSearch(r) {
  const key = r.q + "|" + r.in, same = state.searchKey === key && state.path !== "search";
  Object.assign(state, { path: "search", text: "", notes: [], searchKey: key });
  document.title = (r.q ? r.q + " · " : "") + "Search · PM Wiki";
  if (document.activeElement !== $("search")) $("search").value = r.q;
  drawTree();
  if (r.q.length < 2) { $("doc").innerHTML = "<h1>Search</h1><p>Type two or more letters in the search box at the top.</p>"; return; }
  let res;
  try { res = await api("/api/search?q=" + encodeURIComponent(r.q)); } catch (e) { res = { hits: [], error: e.message }; }
  const now = route();
  if (now.path !== "search" || now.q !== r.q || now.in !== r.in) return;        // a newer search has started
  const counts = {};
  for (const h of res.hits) counts[h.kind] = (counts[h.kind] || 0) + 1;
  const chip = (kind, label, n) => '<a class="chip' + (r.in === kind ? " on" : "") + '" href="' + esc(searchHash(r.q, kind)) + '">' + label + " " + n + "</a>";
  const shown = res.hits.filter((h) => !r.in || h.kind === r.in);
  const line = (h, l, words) => "<a class=\"ln\" href=" + hitHref(h, l.line, words) + ">" + marked(plain(l.text)) + "</a>";
  $("doc").innerHTML = "<h1>Search</h1>" + (res.error ? '<p class="err">' + esc(res.error) + "</p>" : "") +
    '<p class="hint">' + (res.hits.length >= 100 ? "100+" : res.hits.length) + " file" + (res.hits.length === 1 ? "" : "s") +
    (res.corrected ? " for <b>" + esc(res.corrected) + "</b>; nothing found for “" + esc(r.q) + "”" : " for “" + esc(r.q) + "”") +
    (res.any ? ", matching some of the words" : "") + ", best matches first</p>" +
    (res.hits.length ? '<p class="chips">' + chip("", "All", res.hits.length) + Object.keys(KINDS).filter((k) => counts[k]).map((k) => chip(k, KINDS[k], counts[k])).join("") + "</p>" : "") +
    (shown.map((h) => {
      const words = Array.from(new Set(h.lines.flatMap((l) => (l.text.match(/\u0001[^\u0002]*/g) || []).map((w) => w.slice(1).toLowerCase())))).slice(0, 8).join(",");
      const best = h.lines.filter((l) => l.best), more = h.matches - best.length;
      return '<div class="res"><a class="title" href=' + hitHref(h, (best[0] || {}).line, words) + ">" + esc(h.title) + "</a> " +
        [KINDS[h.kind] === "Pages" ? h.type || "page" : KINDS[h.kind].toLowerCase().replace(/s$/, ""), h.status].filter(Boolean).map((b) => '<span class="badge">' + esc(b) + "</span>").join(" ") +
        "<small>" + esc(h.path) + '</small><div class="best">' + best.map((l) => line(h, l, words)).join("") + "</div>" +
        (more > 0 ? "<details><summary>Show all " + h.matches + " matching lines</summary>" + h.lines.map((l) => line(h, l, words)).join("") +
          (h.matches > h.lines.length ? '<p class="hint">…and ' + (h.matches - h.lines.length) + " more in the file.</p>" : "") + "</details>" : "") + "</div>";
    }).join("") || "<p>Nothing found. Try fewer or different words.</p>");
  $("note-count").textContent = "0";
  $("note-list").innerHTML = '<li class="empty">Open a page and select text to add a note.</li>';
  $("main").scrollTop = same ? state.searchTop || 0 : 0;      // coming Back: where she left off
}
// Typing replaces the current search in the history, so Back leaves search in one step.
function runSearch() {
  const q = $("search").value.trim();
  if (route().path === "search") { history.replaceState(null, "", searchHash(q, "")); open(); } else if (q.length >= 2) location.hash = searchHash(q, "");
}
// Mark the words a search matched on the page it opened.
function markWords(list) {
  for (const m of $("doc").querySelectorAll("mark.find")) { const parent = m.parentNode; m.replaceWith(m.textContent); parent.normalize(); }
  const words = list.split(",").map((w) => w.trim()).filter((w) => w.length > 1);
  if (!words.length) return;
  const rx = new RegExp("(" + words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")", "i");
  const walker = document.createTreeWalker($("doc"), NodeFilter.SHOW_TEXT), nodes = [];
  for (let n; (n = walker.nextNode());) if (!n.parentNode.closest(".path, .badges, mark.find") && rx.test(n.nodeValue)) nodes.push(n);
  for (const n of nodes) {
    const span = document.createElement("span");
    span.innerHTML = n.nodeValue.split(rx).map((part, k) => k % 2 ? '<mark class="find">' + esc(part) + "</mark>" : esc(part)).join("");
    n.replaceWith(...span.childNodes);
  }
}

// ---------- document ----------
async function open() {
  const r = route();
  if (!r.path) { location.hash = "#/home"; return; }
  if (r.path === "home") return drawHome();
  if (r.path === "search") return drawSearch(r);
  if (r.path !== state.path || !state.text) {
    try {
      const f = await api("/api/file?path=" + encodeURIComponent(r.path));
      Object.assign(state, { path: f.path, text: f.text, sha: f.sha256 });
    } catch (e) {
      Object.assign(state, { path: r.path, text: "" });
      $("doc").innerHTML = '<p class="err">Could not open ' + esc(r.path) + ": " + esc(e.message) + "</p>";
      drawTree();
      return;
    }
    const { fields, html } = render(state.text);
    const keys = ["id", "type", "status", "trust", "updated", "published", "captured", "asked", "as_of", "external_ok"];
    const shown = keys.filter((k) => fields[k]).concat(Object.keys(fields).filter((k) => !keys.includes(k) && fields[k] && fields[k] !== "[]"));
    const badges = shown.map((k) => '<span class="badge' + (k === "status" ? " status-" + esc(fields[k]) : "") + '">' + esc(k) + ": <b>" + esc(fields[k].length > 80 ? fields[k].slice(0, 77) + "…" : fields[k]) + "</b></span>").join("");
    const card = /^wiki\/sources\/S-\d+\.md$/.test(state.path) ? sourceLinks(fields) : "";
    $("doc").innerHTML = '<div class="path">' + esc(state.path) + "</div>" + (badges ? '<div class="badges">' + badges + "</div>" : "") + card + html;
    document.title = (fields.title || (/^# (.+)$/m.exec(state.text) || [])[1] || state.path) + " · PM Wiki";
    markUncited();
    drawTree();
    await loadNotes();
  }
  markWords(r.hl);
  if (r.anchor) {
    const el = document.getElementById(r.anchor);
    if (el) el.scrollIntoView();
  } else if (r.line) {
    scrollToLine(r.line);
  } else {
    $("main").scrollTop = 0;
  }
}

// ---------- home ----------
const plural = (n, word) => n + " " + word + (n === 1 ? "" : "s");
const pageLink = (path, label, line) => '<a href="#/' + esc(path) + (line ? "?line=" + line : "") + '">' + esc(label || path) + "</a>";
const section = (title, body) => body ? "<h2>" + esc(title) + "</h2>" + body : "";
const bullets = (items) => items.length ? "<ul>" + items.map((i) => "<li>" + i + "</li>").join("") + "</ul>" : "";
async function drawHome(message) {
  Object.assign(state, { path: "home", text: "", notes: [] });
  document.title = "Home · PM Wiki";
  drawTree();
  let h;
  try { h = await api("/api/home"); } catch (e) { h = { error: e.message }; }
  if (route().path !== "home") return;
  const s = h.status || {};
  const has = (p) => state.tree.some((f) => f.path === p);
  const waiting = (s.needs_info || []).map((n) =>
    '<div class="card" data-id="' + esc(n.id) + '"><div>' + (n.file ? pageLink(n.file) + ": " : "") + "“" + esc(n.note) + "”</div>" +
    '<div class="needs">' + esc(n.needs || "Needs your answer.") + '</div><textarea rows="2" placeholder="Your answer"></textarea>' +
    '<button class="reply">Send answer</button></div>').join("");
  const queued = (h.queued || []).map((n) => (n.file ? pageLink(n.file) + ": " : "") + esc(n.text) +
    n.replies.map((t) => "<br><small>You answered: " + esc(t) + "</small>").join(""));
  const saved = (s.to_ingest || []).map((c) => pageLink("wiki/sources/" + c.id + ".md", c.id + " · " + c.title));
  const stage = (a, st) => /^[\w-]+$/.test(st) && has(a.folder + "/" + st + ".md") ? pageLink(a.folder + "/" + st + ".md", st) : esc(st);
  const work = (s.recent_asks || []).map((a) => "<b>" + esc(a.folder.replace(/^work\//, "")) + "</b>: " + (a.stages.map((st) => stage(a, st)).join(" · ") || "not started"))
    .concat((s.recent_reports || []).map((r) => "Report: " + pageLink(r.path, r.title)));
  $("doc").innerHTML = "<h1>Home</h1>" + (h.error ? '<p class="err">Could not check the wiki: ' + esc(h.error) + "</p>" : "") +
    (message ? '<p class="done">' + message + "</p>" : "") +
    '<div class="two"><div class="card"><h3>Add a document</h3><div id="drop" tabindex="0">Drop files here, or click to choose</div>' +
    '<input id="pick" type="file" multiple hidden><input id="cap-title" type="search" placeholder="Or paste text: give it a title">' +
    '<textarea id="cap-text" rows="3" placeholder="…and paste the text here"></textarea><button id="cap-save">Save text</button>' +
    "<p class=\"hint\">Saved to the wiki's originals and searchable right away. The assistant reads it into the pages next time you work with it.</p></div>" +
    '<div class="card"><h3>Ask for later</h3><textarea id="req-text" rows="5" placeholder="Something for the assistant to do next time: a question, a report, a page to fix."></textarea>' +
    '<button id="req-save">Add to the list</button><p class="hint">Nothing runs now. The assistant picks up this list when you next say “process my notes”.</p></div></div>' +
    section("Waiting on you", waiting) +
    section("Waiting for the assistant", bullets(queued.concat(saved.length ? ["Saved documents to read in: " + saved.join(", ")] : []))) +
    section("Sources to recheck", bullets((h.due || []).map((d) => pageLink("wiki/sources/" + d.id + ".md", d.id + " · " + d.title) + " <small>" + esc(d.why) + "</small>" +
      (/^https?:/i.test(d.url) ? ' · <a href="' + esc(d.url) + '" target="_blank" rel="noopener noreferrer">Original ↗</a>' : "")))) +
    section("Pages with conflicting sources", bullets((h.conflicts || []).map((p) => pageLink(p)))) +
    section("Pages with facts that have no source", bullets((h.uncited || []).map((u) => pageLink(u.path, u.path, u.line) + " <small>" + plural(u.count, "line") + "</small>"))) +
    section("Recent work", bullets(work)) +
    '<p class="hint">' + (has("wiki/CHEATSHEET.md") ? pageLink("wiki/CHEATSHEET.md", "What you can ask the assistant") + " · " : "") +
    (has("wiki/INDEX.md") ? pageLink("wiki/INDEX.md", "All pages") : "") + "</p>";
  $("note-count").textContent = "0";
  $("note-list").innerHTML = '<li class="empty">Open a page and select text to add a note.</li>';
  $("main").scrollTop = 0;
}
async function capture(files) {
  const done = [];
  for (const f of files) {
    try {
      const r = await post("/api/capture", f, { "X-Filename": encodeURIComponent(f.name) });
      done.push("Saved " + esc(f.name) + (r.card ? " as " + pageLink("wiki/sources/" + r.card + ".md", r.card) : "") + ".");
    } catch (e) { done.push('<span class="err">' + esc(f.name) + " was not saved: " + esc(e.message) + "</span>"); }
  }
  state.tree = await api("/api/tree");
  drawHome(done.join("<br>"));
}
$("doc").addEventListener("click", async (e) => {
  if (state.path !== "home") return;
  const id = e.target.id;
  try {
    if (id === "drop") $("pick").click();
    else if (id === "cap-save" && $("cap-text").value.trim()) {
      const r = await post("/api/capture", { title: $("cap-title").value, text: $("cap-text").value });
      state.tree = await api("/api/tree");
      drawHome("Saved your text" + (r.card ? " as " + pageLink("wiki/sources/" + r.card + ".md", r.card) : "") + ".");
    } else if (id === "req-save" && $("req-text").value.trim()) {
      await post("/api/notes", { kind: "request", text: $("req-text").value });
      drawHome("Added to the assistant's list.");
    } else if (e.target.classList.contains("reply")) {
      const card = e.target.closest(".card"), text = card.querySelector("textarea").value.trim();
      if (!text) return;
      await post("/api/reply", { id: card.dataset.id, text });
      drawHome("Answer saved.");
    } else return;
    loadStatus();
  } catch (err) { drawHome('<span class="err">Not saved: ' + esc(err.message) + "</span>"); }
});
$("doc").addEventListener("change", (e) => { if (e.target.id === "pick" && e.target.files.length) capture(e.target.files); });
$("doc").addEventListener("dragover", (e) => { if (e.target.closest("#drop")) { e.preventDefault(); $("drop").classList.add("over"); } });
$("doc").addEventListener("dragleave", (e) => { if (e.target.id === "drop") e.target.classList.remove("over"); });
$("doc").addEventListener("drop", (e) => { if (e.target.closest("#drop")) { e.preventDefault(); capture(e.dataTransfer.files); } });
// A file dropped anywhere else must not replace the viewer with the file.
window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => e.preventDefault());
async function loadStatus() {
  let s;
  try { s = await api("/api/status"); } catch (e) { return; }
  if (s.error) return;
  const parts = [];
  if (s.open_notes) parts.push(s.open_notes + " open note" + (s.open_notes > 1 ? "s" : ""));
  if (s.needs_info_notes) parts.push(s.needs_info_notes + " waiting on you");
  if (s.sources_due) parts.push(s.sources_due + " source" + (s.sources_due > 1 ? "s" : "") + " to recheck");
  if (s.lint_due) parts.push("wiki check due");
  if ((s.to_ingest || []).length) parts.push(plural(s.to_ingest.length, "saved document") + " to read in");
  if ((s.unfinished_runs || []).length) parts.push(s.unfinished_runs.length + " unfinished run" + (s.unfinished_runs.length > 1 ? "s" : ""));
  $("status").textContent = parts.join(" · ");
  $("status").title = parts.length ? "See Home for the details. Type /wiki in Claude to handle these." : "";
}
function scrollToLine(line) {
  let best = null;
  for (const el of $("doc").querySelectorAll("[data-line]")) if (+el.dataset.line <= line && (!best || +el.dataset.line >= +best.dataset.line)) best = el;
  if (best) { best.scrollIntoView({ block: "center" }); flash(best); }
}
function flash(el) { el.classList.add("flash"); setTimeout(() => el.classList.remove("flash"), 1500); }

// Facts in curated pages with neither a citation nor a label.
function markUncited() {
  if (!state.path.startsWith("wiki/pages/")) return;
  let section = "";
  for (const el of $("doc").querySelectorAll("h2, h3, p, li")) {
    if (/^H/.test(el.tagName)) { if (el.tagName === "H2") section = el.textContent.toLowerCase(); continue; }
    if (/related|open questions|conflicts|see also|history/.test(section) || !section) continue;
    const own = Array.from(el.childNodes).filter((c) => !/^(UL|OL)$/.test(c.nodeName)).map((c) => c.textContent).join("");
    if (!own.trim() || /none recorded/i.test(own)) continue;
    if (!/\[S-\d{4}|\((inferred|assumption|unknown)\)/.test(own)) el.classList.add("uncited");
  }
}

// Citation hover cards.
async function cardInfo(id) {
  if (!state.cards[id]) {
    state.cards[id] = api("/api/file?path=wiki/sources/" + id + ".md").then((f) => splitFront(f.text).fields).catch(() => ({ title: "No source card found" }));
  }
  return state.cards[id];
}
document.addEventListener("mouseover", async (e) => {
  const a = e.target.closest && e.target.closest("a[data-card]");
  if (!a) return;
  const f = await cardInfo(a.dataset.card);
  if (!a.matches(":hover")) return;
  const r = a.getBoundingClientRect();
  $("tip").innerHTML = "<b>" + esc(a.dataset.card) + "</b> " + esc(f.title || "") +
    '<br><small>trust: ' + esc(f.trust || "?") + (f.published ? " · published " + esc(f.published) : "") + (f.captured ? " · captured " + esc(f.captured) : "") + "</small>";
  $("tip").style.left = Math.min(r.left, innerWidth - 370) + "px";
  $("tip").style.top = r.bottom + 6 + "px";
  $("tip").hidden = false;
});
document.addEventListener("mouseout", (e) => { if (e.target.closest && e.target.closest("a[data-card]")) hideTip(); });
// A clicked citation navigates away before mouseout fires, so hide on click and scroll too.
document.addEventListener("click", hideTip, true);
$("main").addEventListener("scroll", hideTip);

// ---------- notes ----------
async function loadNotes() {
  state.notes = await api("/api/notes?path=" + encodeURIComponent(state.path)).catch(() => []);
  const open = state.notes.filter((n) => n.status === "open" || n.status === "needs-info");
  $("note-count").textContent = open.length;
  highlightNotes(open);
  $("note-list").innerHTML = state.notes.length ? state.notes.slice().reverse().map((n) =>
    '<li data-id="' + esc(n.id) + '"><span class="st ' + esc(n.status) + '">' + esc(n.status) + "</span> <small>" + esc(n.created.slice(0, 16).replace("T", " ")) +
    '</small><span class="q">“' + esc(n.quote.exact) + "”</span>" + esc(n.text) + (n.resolution ? "<br><small>→ " + esc(n.resolution) + "</small>" : "") + "</li>").join("")
    : '<li class="empty">No notes on this page. Select text to add one.</li>';
}

// Map whitespace-collapsed document text back to text nodes so quotes can be found.
function textIndex() {
  const walker = document.createTreeWalker($("doc"), NodeFilter.SHOW_TEXT);
  const map = [];
  let text = "", space = true;
  for (let node; (node = walker.nextNode());) {
    if (node.parentNode.closest(".path, .badges")) continue;
    const v = node.nodeValue;
    for (let k = 0; k < v.length; k++) {
      if (/\s/.test(v[k])) { if (space) continue; text += " "; space = true; } else { text += v[k]; space = false; }
      map.push([node, k]);
    }
    if (!space) { text += " "; space = true; map.push([node, v.length]); }
  }
  return { text, map };
}
const squash = (s) => s.replace(/\s+/g, " ").trim();

function highlightNotes(notes) {
  for (const n of notes) {
    const { text, map } = textIndex();
    const exact = squash(n.quote.exact);
    if (!exact) continue;
    let at = -1, best = -1;
    for (let k = text.indexOf(exact); k >= 0; k = text.indexOf(exact, k + 1)) {
      const score = (squash(n.quote.prefix || "") && text.slice(0, k).trimEnd().endsWith(squash(n.quote.prefix).slice(-20)) ? 2 : 0) +
        (squash(n.quote.suffix || "") && text.slice(k + exact.length).trimStart().startsWith(squash(n.quote.suffix).slice(0, 20)) ? 1 : 0);
      if (score > best) { best = score; at = k; }
    }
    if (at < 0) continue;
    // Wrap each text-node piece of the match in its own <mark>.
    const pieces = new Map();
    for (let k = at; k < at + exact.length; k++) {
      const [node, off] = map[k];
      const p = pieces.get(node) || [off, off];
      pieces.set(node, [Math.min(p[0], off), Math.max(p[1], off + 1)]);
    }
    for (const [node, [s, e]] of pieces) {
      if (node.nodeValue.slice(s, e).trim() === "" || node.parentNode.closest("mark")) continue;
      const range = document.createRange();
      range.setStart(node, s);
      range.setEnd(node, Math.min(e, node.nodeValue.length));
      const mark = document.createElement("mark");
      mark.className = "note-hl";
      mark.dataset.id = n.id;
      mark.title = n.text;
      range.surroundContents(mark);
    }
  }
}

function blockOf(node) {
  const el = node.nodeType === 1 ? node : node.parentNode;
  return el.closest("li, p, td, th, h1, h2, h3, h4, h5, h6, pre, blockquote") || el.closest("[data-line]");
}
document.addEventListener("mouseup", (e) => {
  if (e.target.closest && e.target.closest("#note-box, #note-btn")) return;
  setTimeout(() => {
    const sel = getSelection();
    const btn = $("note-btn");
    if (/^(home|search)$/.test(state.path) || !sel.rangeCount || sel.isCollapsed || !$("doc").contains(sel.anchorNode) || !squash(sel.toString())) { btn.hidden = true; return; }
    const range = sel.getRangeAt(0);
    const block = blockOf(range.startContainer) || $("doc");
    const before = document.createRange();
    before.setStart(block, 0);
    before.setEnd(range.startContainer, range.startOffset);
    const endBlock = blockOf(range.endContainer) || block;
    const after = document.createRange();
    after.setStart(range.endContainer, range.endOffset);
    after.setEnd(endBlock, endBlock.childNodes.length);
    const lineEl = block.closest("[data-line]");
    state.pending = {
      exact: sel.toString(), prefix: squash(before.toString()).slice(-60), suffix: squash(after.toString()).slice(0, 60),
      line: lineEl ? +lineEl.dataset.line : null,
    };
    const r = range.getBoundingClientRect();
    btn.style.left = Math.min(r.right + scrollX + 4, innerWidth - 70) + "px";
    btn.style.top = r.bottom + scrollY + 4 + "px";
    btn.hidden = false;
  }, 0);
});
$("note-btn").onclick = () => {
  const btn = $("note-btn"), box = $("note-box");
  btn.hidden = true;
  $("note-quote").textContent = "“" + squash(state.pending.exact).slice(0, 200) + "”";
  box.style.left = Math.max(8, Math.min(parseInt(btn.style.left, 10) - 160, innerWidth - 340)) + "px";
  box.style.top = btn.style.top;
  box.hidden = false;
  $("note-text").value = "";
  $("note-text").focus();
};
$("note-text").addEventListener("keydown", async (e) => {
  if (e.key === "Escape") { $("note-box").hidden = true; return; }
  if (e.key !== "Enter" || e.shiftKey) return;
  e.preventDefault();
  const text = $("note-text").value.trim();
  if (!text || !state.pending) return;
  const p = state.pending;
  try {
    await post("/api/notes", { file: state.path, quote: { exact: p.exact, prefix: p.prefix, suffix: p.suffix }, line: p.line, text });
    $("note-box").hidden = true;
    state.pending = null;
    getSelection().removeAllRanges();
    state.text = "";                // re-render so the new highlight shows
    await open();
  } catch (err) {
    $("note-quote").innerHTML = '<span class="err">Not saved: ' + esc(err.message) + "</span>";
  }
});
document.addEventListener("mousedown", (e) => {
  if (!(e.target.closest && e.target.closest("#note-box, #note-btn")) && !$("note-box").hidden && !$("note-text").value.trim()) $("note-box").hidden = true;
});
$("note-list").onclick = (e) => {
  const li = e.target.closest("li[data-id]");
  if (!li) return;
  const mark = $("doc").querySelector('mark[data-id="' + CSS.escape(li.dataset.id) + '"]');
  if (mark) { mark.scrollIntoView({ block: "center" }); flash(mark); return; }
  const n = state.notes.find((x) => x.id === li.dataset.id);
  if (n && n.line) scrollToLine(n.line);
};
$("doc").addEventListener("click", (e) => {
  const mark = e.target.closest("mark.note-hl");
  if (!mark) return;
  document.body.classList.add("notes-open");
  document.body.classList.remove("no-notes");
  const li = $("note-list").querySelector('li[data-id="' + CSS.escape(mark.dataset.id) + '"]');
  if (li) { li.scrollIntoView({ block: "nearest" }); flash(li); }
});

// ---------- wiring ----------
$("toggle-side").onclick = () => document.body.classList.toggle(innerWidth <= 700 ? "side-open" : "no-side");
$("toggle-notes").onclick = () => document.body.classList.toggle(innerWidth <= 900 ? "notes-open" : "no-notes");
$("uncited").onchange = (e) => document.body.classList.toggle("show-uncited", e.target.checked);
$("filter").oninput = drawTree;
let searchTimer;
$("search").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(runSearch, 250); });
$("search").addEventListener("keydown", (e) => { if (e.key === "Enter") { clearTimeout(searchTimer); runSearch(); } if (e.key === "Escape") e.target.blur(); });
$("main").addEventListener("scroll", () => { if (state.path === "search") state.searchTop = $("main").scrollTop; });
// "/" jumps to the search box; the arrow keys walk the results.
document.addEventListener("keydown", (e) => {
  const typing = /^(INPUT|TEXTAREA)$/.test(e.target.tagName);
  if (e.key === "/" && !typing) { e.preventDefault(); $("search").focus(); $("search").select(); return; }
  if (state.path !== "search" || !/^Arrow(Down|Up)$/.test(e.key) || (typing && e.target.id !== "search")) return;
  const titles = Array.from($("doc").querySelectorAll(".res > a.title"));
  const next = titles[titles.indexOf(document.activeElement) + (e.key === "ArrowDown" ? 1 : -1)] || (e.key === "ArrowUp" ? $("search") : null);
  if (next) { e.preventDefault(); next.focus(); if (next.scrollIntoView) next.scrollIntoView({ block: "nearest" }); }
});
$("quit").onclick = async () => {
  if (!confirm("Close the wiki viewer? Your notes and saved documents are kept.")) return;
  await post("/api/stop").catch(() => {});
  document.body.innerHTML = '<p class="closed">The wiki viewer is closed. Open it again from Applications (or Spotlight), or with /wiki open in Claude. You can close this tab.</p>';
};
window.addEventListener("hashchange", () => { hideTip(); if (innerWidth <= 700) document.body.classList.remove("side-open"); open(); });

(async () => {
  try {
    state.tree = await api("/api/tree");
  } catch (e) {
    $("doc").innerHTML = '<p class="err">Could not load the file list: ' + esc(e.message) + "</p>";
    return;
  }
  drawTree();
  open();
  loadStatus();
})();
