"""
build_pages.py — keep pages.json in sync with the HTML files in pages/.

What it does (safe to run any number of times):
  1. Finds every .html file under pages/ (sub-folders included).
  2. Adds any new file to pages.json:
       title  <- the page's <title> (filename added if two pages share a title)
       group  <- the folder name, e.g. pages/no-var-input/x.html -> "No var input"
       date   <- today
     Existing entries are never overwritten, so your hand-edited titles,
     descriptions, groups and tags are kept.
  3. Removes entries whose file was deleted (external "url" links are kept).
  4. Updates each entry's size.
  5. Fixes "Save page as" leftovers: a stylesheet link to "./css2" (no extension,
     which GitHub Pages serves with the wrong type) is pointed at assets/fonts.css.
  6. Adds a small "← All pages" link to each page so visitors can get back to the
     index. Use --no-nav to skip this, or --remove-nav to take it out again.

Usage (from the repository root):
  python tools/build_pages.py
  python tools/build_pages.py --check      # exit 1 if pages.json is out of date (no writes)
"""

import argparse
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES_DIR = os.path.join(ROOT, "pages")
MANIFEST = os.path.join(ROOT, "pages.json")

NAV_START = "<!-- site-nav:start -->"
NAV_END = "<!-- site-nav:end -->"
NAV_RE = re.compile(re.escape(NAV_START) + r".*?" + re.escape(NAV_END) + r"\n?", re.S)
CSS2_RE = re.compile(r'href="\./css2"')


def nav_html(depth):
    up = "../" * depth
    return (
        f'{NAV_START}\n'
        f'<a href="{up}index.html" style="position:fixed;left:12px;bottom:12px;z-index:2147483647;'
        f'font:600 12px/1 system-ui,sans-serif;padding:8px 12px;border-radius:999px;'
        f'background:#1d2330;color:#fff;text-decoration:none;opacity:.85;'
        f'box-shadow:0 2px 8px rgba(0,0,0,.25)" '
        f'onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.85">&larr; All pages</a>\n'
        f'{NAV_END}\n'
    )


def read_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return " ".join(m.group(1).split()) if m else ""


def pretty(name):
    name = re.sub(r"[-_]+", " ", name).strip()
    return name[:1].upper() + name[1:] if name else ""


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    return {"site": {"title": "Results", "description": ""}, "pages": []}


def patch_page(path, rel, mode):
    """Fix css2 link and add/remove the back link. Returns True if the file changed."""
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        html = f.read()
    orig = html
    depth = rel.count("/")  # pages/a/b.html -> 2 levels up to the root

    if CSS2_RE.search(html):
        html = CSS2_RE.sub(f'href="{"../" * depth}assets/fonts.css"', html)

    html = NAV_RE.sub("", html)
    if mode == "add":
        nav = nav_html(depth)
        i = html.lower().rfind("</body>")
        html = html[:i] + nav + html[i:] if i != -1 else html + nav

    if html != orig:
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(html)
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only report; exit 1 if out of date")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--no-nav", action="store_true", help="don't add the back link")
    g.add_argument("--remove-nav", action="store_true", help="remove the back link from all pages")
    a = ap.parse_args()

    man = load_manifest()
    entries = man.setdefault("pages", [])
    by_path = {e["path"]: e for e in entries if e.get("path")}

    found = []
    for d, _, files in os.walk(PAGES_DIR):
        for fn in sorted(files):
            if fn.lower().endswith((".html", ".htm")):
                full = os.path.join(d, fn)
                found.append((full, os.path.relpath(full, ROOT).replace(os.sep, "/")))
    found.sort(key=lambda x: x[1])
    found_paths = {rel for _, rel in found}

    added, removed, patched = [], [], []
    titles = {e.get("title") for e in entries}
    today = dt.date.today().isoformat()

    for full, rel in found:
        if rel not in by_path:
            with open(full, encoding="utf-8", errors="replace") as f:
                title = read_title(f.read(200_000))
            stem = os.path.splitext(os.path.basename(rel))[0]
            if not title or title in titles:
                title = f"{title} — {pretty(stem)}" if title else pretty(stem)
            titles.add(title)
            folder = os.path.dirname(os.path.relpath(full, PAGES_DIR))
            e = {"title": title, "path": rel, "group": pretty(folder.split(os.sep)[0]) if folder else "Pages",
                 "description": "", "tags": [], "date": today}
            entries.append(e)
            by_path[rel] = e
            added.append(rel)
        by_path[rel]["size_kb"] = round(os.path.getsize(full) / 1024)

    kept = []
    for e in entries:
        if e.get("path") and e["path"] not in found_paths:
            removed.append(e["path"])
        else:
            kept.append(e)
    man["pages"] = kept

    if a.check:
        for r in added:
            print(f"not in pages.json: {r}")
        for r in removed:
            print(f"missing file:      {r}")
        sys.exit(1 if added or removed else 0)

    mode = "remove" if a.remove_nav else (None if a.no_nav else "add")
    for full, rel in found:
        if mode is None:
            # still fix the css link, keep nav as it is
            with open(full, encoding="utf-8", errors="surrogateescape") as f:
                html = f.read()
            has_nav = NAV_START in html
            if patch_page(full, rel, "add" if has_nav else "remove"):
                patched.append(rel)
        elif patch_page(full, rel, mode):
            patched.append(rel)

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2, ensure_ascii=False)
        f.write("\n")

    for r in added:
        print(f"added:   {r}")
    for r in removed:
        print(f"removed: {r}")
    for r in patched:
        print(f"patched: {r}")
    print(f"pages.json: {len(man['pages'])} entries")


if __name__ == "__main__":
    main()
