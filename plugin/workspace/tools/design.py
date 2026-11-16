#!/usr/bin/env python3
"""Helpers for UI mockups (the ui-mockup skill): exact colors from screenshots, style
summaries of saved HTML/CSS, palette checks, single-file bundling, rendering to PNG and the
design/INDEX.md index. Standard library only.

Usage: python3 tools/design.py <command> --help
  colors IMAGE [--box X,Y,W,H] [--at X,Y ...]   dominant colors (PNG; JPEG etc. on macOS)
  css FILE_OR_DIR ...                            colors, fonts, sizes, radii, shadows, variables
  check MOCKUP.html [--tokens tokens.css]        off-palette colors, undefined vars, external loads
  bundle MOCKUP.html [-o OUT]                    inline local stylesheets and images (shareable file)
  render HTML [-o PNG] [--width 1440]            screenshot for a visual self-check
  index                                          rewrite design/INDEX.md
"""
import argparse
import base64
import collections
import mimetypes
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DESIGN = ROOT / "design"


# ---------- images ----------

def png_pixels(data):
    """Decode an 8-bit non-interlaced PNG. Returns (width, height, rows of RGB tuples, profile)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, palette, profile = 8, [], None, ""
    while pos < len(data):
        size, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + size]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif kind == b"iCCP":
            profile = body.split(b"\0", 1)[0].decode("latin-1")
        elif kind == b"IDAT":
            idat.append(body)
        pos += size + 12
    if depth != 8 or interlace:
        raise ValueError("only 8-bit, non-interlaced PNGs (re-save or export the image)")
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw, stride = zlib.decompress(b"".join(idat)), w * bpp
    prev, rows, i = bytearray(stride), [], 0
    for _ in range(h):
        f, line = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += stride + 1
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif f == 3:
            for x in range(stride):
                line[x] = (line[x] + ((line[x - bpp] if x >= bpp else 0) + prev[x]) // 2) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b, c = prev[x], prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if ctype == 3:
            rows.append([palette[v] for v in line])
        elif ctype in (0, 4):
            rows.append([(v, v, v) for v in line[::bpp]])
        else:
            rows.append(list(zip(line[0::bpp], line[1::bpp], line[2::bpp])))
    return w, h, rows, profile


def load_image(path):
    data = pathlib.Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":  # JPEG, HEIC, TIFF...: convert with macOS sips
        if not shutil.which("sips"):
            raise SystemExit("Only PNG is supported here; export the image as PNG.")
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "x.png"
            subprocess.run(["sips", "-s", "format", "png", str(path), "--out", str(out)],
                           capture_output=True, check=True)
            data = out.read_bytes()
    return png_pixels(data)


def p3_to_srgb(rgb):
    """Display P3 to sRGB (macOS screenshots are often P3), clipped to the sRGB gamut."""
    lin = [(c / 255 / 12.92) if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in rgb]
    m = ((1.2249, -0.2247, 0), (-0.0420, 1.0419, 0), (-0.0197, -0.0786, 1.0979))
    out = []
    for row in m:
        v = min(1, max(0, sum(a * b for a, b in zip(row, lin))))
        out.append(round(255 * (v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)))
    return tuple(out)


def hexc(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def box_arg(spec, w, h):
    vals = []
    for v, full in zip(spec.split(","), (w, h, w, h)):
        v = v.strip()
        vals.append(int(float(v[:-1]) * full / 100) if v.endswith("%") else int(v))
    return vals


def cmd_colors(a):
    w, h, rows, profile = load_image(a.image)
    conv = p3_to_srgb if "P3" in profile else (lambda c: c)
    print(f"{a.image}: {w}x{h} px" + (f", profile {profile}" + (" (converted to sRGB)" if "P3" in profile else "")
                                      if profile else ""))
    for spec in a.at or []:
        x, y = box_arg(spec + ",0,0", w, h)[:2]
        print(f"  at {x},{y}: {hexc(conv(rows[min(y, h - 1)][min(x, w - 1)]))}")
    if a.at and not a.box:
        return 0
    x0, y0, bw, bh = box_arg(a.box, w, h) if a.box else (0, 0, w, h)
    counts = collections.Counter()
    for row in rows[y0:y0 + bh]:
        counts.update(row[x0:x0 + bw])
    total = sum(counts.values()) or 1
    groups = []  # merge anti-aliasing neighbours into the most common nearby color
    for c, n in counts.most_common():
        for g in groups:
            if max(abs(p - q) for p, q in zip(c, g[0])) <= a.merge:
                g[1] += n
                break
        else:
            if len(groups) < 200:
                groups.append([c, n])
    print(f"  region {x0},{y0} {bw}x{bh}: {len(counts)} distinct colors; top groups:")
    for c, n in sorted(groups, key=lambda g: -g[1])[:a.top]:
        if n / total >= 0.0005:
            print(f"  {hexc(conv(c))}  {100 * n / total:5.1f}%")
    return 0


# ---------- CSS ----------

COLOR = re.compile(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b|rgba?\([^)]*\)|hsla?\([^)]*\)")
EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["']?\s*(?:https?:)?//[^"'\s>]+|url\(\s*["']?(?:https?:)?//[^)"']+"""
                      r"""|@import\s+(?:url\()?\s*["']?(?:https?:)?//[^)"';]+""", re.I)


def norm_color(c):
    c = c.lower().replace(" ", "")
    if c.startswith("#"):
        h = c[1:]
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h)
        return "#" + (h[:6] if h[6:] in ("", "ff") else h)
    m = re.match(r"rgba?\((\d+),(\d+),(\d+)(?:,([\d.]+%?))?\)", c.replace("/", ","))
    if m:
        out = "#%02x%02x%02x" % tuple(min(255, int(v)) for v in m.groups()[:3])
        alpha = m.group(4)
        if alpha and alpha not in ("1", "100%"):
            a = float(alpha[:-1]) / 100 if alpha.endswith("%") else float(alpha)
            out += "%02x" % round(a * 255)
        return out
    return c


def styles_of(path):
    """All CSS in a file: the whole file for .css, <style> blocks and style="" for HTML."""
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    if pathlib.Path(path).suffix.lower() == ".css":
        return text
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", text, re.S | re.I)
    attrs = re.findall(r"""\sstyle\s*=\s*("[^"]*"|'[^']*')""", text, re.I)
    return "\n".join(blocks + [a[1:-1] for a in attrs])


def css_files(paths):
    for p in map(pathlib.Path, paths):
        if p.is_dir():
            yield from sorted(f for f in p.rglob("*") if f.suffix.lower() in (".css", ".html", ".htm"))
        else:
            yield p


def cmd_css(a):
    css = "\n".join(styles_of(f) for f in css_files(a.paths))
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    def top(title, values, n=a.top):
        c = collections.Counter(v.strip() for v in values if v.strip())
        if c:
            print(f"## {title} ({len(c)} distinct)")
            for v, k in c.most_common(n):
                print(f"  {k:5d}  {v[:120]}")
    print(f"{len(css)} chars of CSS from {len(list(css_files(a.paths)))} file(s)")
    top("custom properties", [f"{k}: {v}" for k, v in re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", css)], 60)
    top("colors", [norm_color(c) for c in COLOR.findall(css)], 40)
    for prop in ("font-family", "font-size", "font-weight", "line-height", "border-radius",
                 "box-shadow", "padding", "gap", "border"):
        top(prop, re.findall(r"(?<![\w-])" + prop + r"\s*:\s*([^;}]+)", css))
    return 0


def cmd_check(a):
    src = pathlib.Path(a.mockup)
    html = src.read_text(encoding="utf-8", errors="replace")
    local = [x or y for x, y in re.findall(r"""<link[^>]+href\s*=\s*["']([^"':]+)["']"""
                                           r"""|<img[^>]+src\s*=\s*["']([^"':]+)["']""", html, re.I)]
    sheets = [src.parent / h for h in local if h.endswith(".css") and (src.parent / h).is_file()]
    css = "\n".join([styles_of(src)] + [styles_of(f) for f in sheets])
    problems = []
    for m in EXTERNAL.finditer(html + css):
        problems.append(f"external load (fails offline and in a shared file): {m.group(0)[:100]}")
    if a.shareable:
        problems += [f"local file reference left (the file won't stand alone): {h}" for h in local]
    defined = set(re.findall(r"(--[\w-]+)\s*:", css))
    if a.tokens:
        tokens = pathlib.Path(a.tokens).read_text(encoding="utf-8")
        defined |= set(re.findall(r"(--[\w-]+)\s*:", tokens))
        palette = {norm_color(c)[:7] for c in COLOR.findall(tokens)}
        # colors written outside a custom property definition are off-token
        literal = re.sub(r"--[\w-]+\s*:[^;}]+", "", css)
        for c in sorted({norm_color(c)[:7] for c in COLOR.findall(literal)} - palette):
            near = min(palette, key=lambda p: dist(p, c), default=None)
            problems.append(f"color {c} is not in the tokens" + (f" (nearest {near})" if near else ""))
    for v in sorted(set(re.findall(r"var\(\s*(--[\w-]+)", css)) - defined):
        problems.append(f"var({v}) is used but never defined")
    for p in problems:
        print(p)
    print(f"check: {len(problems)} problem(s)" + ("" if a.shareable or not local else
                                                 "; links local files: bundle before sharing"))
    return 1 if problems else 0


def dist(a, b):
    return sum((int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) ** 2 for i in (1, 3, 5)) ** 0.5


# ---------- bundle and render ----------

def data_uri(path):
    kind = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{kind};base64," + base64.b64encode(path.read_bytes()).decode()


def inline_urls(css, base):
    def sub(m):
        ref = m.group(1).strip("'\" ")
        p = (base / ref).resolve()
        return f'url("{data_uri(p)}")' if ":" not in ref and p.is_file() else m.group(0)
    return re.sub(r"url\(([^)]+)\)", sub, css)


def bundled(src):
    """The HTML of src with local stylesheets and images inlined."""
    src = pathlib.Path(src).resolve()
    base, html = src.parent, src.read_text(encoding="utf-8")

    def link(m):
        href = re.search(r"""href\s*=\s*["']([^"']+)["']""", m.group(0))
        p = (base / href.group(1)).resolve() if href and ":" not in href.group(1) else None
        if not p or not p.is_file():
            return m.group(0)
        css = inline_urls(p.read_text(encoding="utf-8"), p.parent)
        return f"<style>/* {href.group(1)} */\n{css}</style>"

    def img(m):
        p = (base / m.group(2)).resolve()
        return m.group(1) + data_uri(p) + m.group(3) if ":" not in m.group(2) and p.is_file() else m.group(0)
    html = re.sub(r"<link\b[^>]*rel\s*=\s*[\"']?stylesheet[^>]*>", link, html, flags=re.I)
    html = re.sub(r"""(<img\b[^>]*\bsrc\s*=\s*["'])([^"']+)(["'])""", img, html, flags=re.I)
    return re.sub(r"(<style[^>]*>)(.*?)(</style>)",
                  lambda m: m.group(1) + inline_urls(m.group(2), base) + m.group(3), html, flags=re.S | re.I)


def cmd_bundle(a):
    html = bundled(a.mockup)
    out = pathlib.Path(a.output or a.mockup)
    out.write_text(html, encoding="utf-8")
    print(f"bundled {out} ({len(html.encode()) // 1024} KB)")
    a.mockup, a.tokens, a.shareable = str(out), None, True
    return cmd_check(a)


def chrome():
    for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if os.path.exists(p):
            return p
    return next(filter(None, map(shutil.which, ("google-chrome", "chromium", "chromium-browser",
                                                 "microsoft-edge", "msedge"))), None)


def cmd_render(a):
    src = pathlib.Path(a.html).resolve()
    out = pathlib.Path(a.output or src.with_suffix(".png")).resolve()
    browser = chrome()
    try:
        if browser:
            with tempfile.TemporaryDirectory() as profile:
                subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                                f"--user-data-dir={profile}", f"--window-size={a.width},{a.height}",
                                f"--screenshot={out}", src.as_uri()],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        elif shutil.which("qlmanage"):  # macOS Quick Look: square thumbnail, approximate
            with tempfile.TemporaryDirectory() as tmp:
                subprocess.run(["qlmanage", "-t", "-s", str(a.width), "-o", tmp, str(src)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
                made = pathlib.Path(tmp) / (src.name + ".png")
                if made.exists():
                    shutil.move(str(made), str(out))
        else:
            print("No renderer found (Chrome, Edge, Chromium or macOS Quick Look). Skip the self-check.")
            return 1
    except subprocess.TimeoutExpired:
        print("Renderer timed out. Skip the self-check.")
        return 1
    if not out.exists():
        print("Rendering failed. Skip the self-check.")
        return 1
    print(f"rendered {out}" + ("" if browser else " (Quick Look: approximate)"))
    return 0


# ---------- index ----------

def title_of(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^title:\s*(.+)$", text, re.M) or re.search(r"<title>(.*?)</title>", text, re.S | re.I) \
        or re.search(r"^# (.+)$", text, re.M)
    return m.group(1).strip() if m else path.stem


def field(path, name):
    m = re.search(rf"^{name}:\s*(.+?)\s*(?:#.*)?$", path.read_text(encoding="utf-8", errors="replace"), re.M)
    return m.group(1) if m else ""


def cmd_index(a):
    rel = lambda p: p.relative_to(DESIGN).as_posix()
    out = ["# Design index", "", "Generated by `python3 tools/design.py index`. Don't edit by hand."]

    def section(title, lines):
        out.extend(["", "## " + title, ""] + (lines or ["(none yet)"]))
    lines = []
    for f in sorted(DESIGN.glob("systems/*/SYSTEM.md")):
        kit = f.parent / "kit.html"
        lines.append(f"- [{title_of(f)}]({rel(f)})" + (f" · [kit]({rel(kit)})" if kit.exists() else ""))
    section("Design systems", lines)
    lines = []
    for f in sorted(DESIGN.glob("products/*/PRODUCT.md")):
        lines.append(f"- [{title_of(f)}]({rel(f)}) · system: {field(f, 'system') or '(unknown)'}")
        for s in sorted(f.parent.glob("screens/*.html")):
            lines.append(f"  - screen: [{title_of(s)}]({rel(s)})")
    section("Products and screens", lines)
    lines = []
    for f in sorted(DESIGN.glob("mockups/*/notes.md"), reverse=True):
        versions = sorted(f.parent.glob("v*.html"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
        latest = f" · latest: [{versions[-1].name}]({rel(versions[-1])})" if versions else ""
        lines.append(f"- [{title_of(f)}]({rel(f)}) · {field(f, 'product')} / {field(f, 'screen')}"
                     f" · {field(f, 'status') or 'draft'}{latest}")
    section("Mockups", lines)
    section("References", [f"- {rel(p)}" for p in sorted(DESIGN.glob("refs/*"))
                           if p.is_file() and not p.name.startswith(".")])
    (DESIGN / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote design/INDEX.md: {len(out)} lines")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("colors", help="dominant colors of a screenshot or region")
    p.add_argument("image")
    p.add_argument("--box", help="region X,Y,W,H in pixels or percent (0,0,100%%,8%%)")
    p.add_argument("--at", action="append", help="sample one pixel X,Y (pixels or percent); repeatable")
    p.add_argument("--top", type=int, default=16)
    p.add_argument("--merge", type=int, default=6, help="merge colors within this channel distance")
    p = sub.add_parser("css", help="summarize styles in saved HTML/CSS files or folders")
    p.add_argument("paths", nargs="+")
    p.add_argument("--top", type=int, default=12)
    p = sub.add_parser("check", help="check a mockup against a design system's tokens")
    p.add_argument("mockup")
    p.add_argument("--tokens")
    p.add_argument("--shareable", action="store_true", help="also fail on local file references")
    p = sub.add_parser("bundle", help="inline local stylesheets and images into one file")
    p.add_argument("mockup")
    p.add_argument("-o", "--output")
    p = sub.add_parser("render", help="render HTML to a PNG for a visual self-check")
    p.add_argument("html")
    p.add_argument("-o", "--output")
    p.add_argument("--width", type=int, default=1440)
    p.add_argument("--height", type=int, default=900)
    sub.add_parser("index", help="rewrite design/INDEX.md")
    a = ap.parse_args(argv)
    return {"colors": cmd_colors, "css": cmd_css, "check": cmd_check, "bundle": cmd_bundle,
            "render": cmd_render, "index": cmd_index}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
