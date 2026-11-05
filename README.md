# NL → LTL Results

A static website for the NL → LTL / FRETish result viewers, hosted on GitHub Pages.

```
index.html              landing page; lists everything in pages.json
pages.json              the list of pages (title, group, description, tags)
pages/                  the viewer pages (each sub-folder becomes a group)
  traces/
  no-var-input/
assets/fonts.css        IBM Plex fonts used by the pages
tools/build_pages.py    adds new pages to pages.json automatically
.github/workflows/      publishes the site on every push to main
.nojekyll               tells GitHub Pages to serve files as-is
```

## Publish on GitHub

1. Create a new repository on GitHub, e.g. `ltl-results`.
2. Push this folder to it:
   ```bash
   cd ltl-results-site
   git init -b main
   git add .
   git commit -m "Initial site"
   git remote add origin https://github.com/<your-user>/ltl-results.git
   git push -u origin main
   ```
3. On GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. Open the **Actions** tab and wait for "Deploy site" to finish (about a minute).
   The site is at `https://<your-user>.github.io/ltl-results/`.

If the repository is private, GitHub Pages needs a paid plan (Pro, Team or Enterprise).
On a free account, make the repository public, and remember that anyone with the link can see the data.

## Add a page

1. Copy the `.html` file into `pages/`, or into a sub-folder of it. The sub-folder name
   becomes the group heading, e.g. `pages/with-vars/` → "With vars".
   Use file names without spaces.
2. Commit and push. The workflow runs `tools/build_pages.py`, which adds the page to
   the list, using its `<title>` as the title.
3. Optional: to give it a better title, description or tags, edit its entry in
   `pages.json`. Run `python tools/build_pages.py` locally first, so the entry exists to edit.
   The script never overwrites what you write there.

To remove a page, delete its file and push; its entry is removed automatically.

## Link a page hosted elsewhere

Add an entry with `url` instead of `path` to `pages.json`:

```json
{
  "title": "My other results",
  "url": "https://example.com/results.html",
  "group": "External",
  "description": "Opens in a new tab.",
  "tags": ["external"]
}
```

## What build_pages.py changes in a page

- A stylesheet link to `./css2` (left by the browser's "Save page as") is pointed at
  `assets/fonts.css`. GitHub Pages serves files without an extension with a type that
  browsers refuse to use as a stylesheet.
- A small "← All pages" link is added in the bottom-left corner, between
  `<!-- site-nav:start -->` and `<!-- site-nav:end -->` markers.
  `python tools/build_pages.py --remove-nav` takes it out again;
  `--no-nav` leaves pages without it.

## Preview locally

`index.html` loads `pages.json`, which browsers block when the file is opened directly.
Run a small server instead:

```bash
python tools/build_pages.py
python -m http.server 8000
# open http://localhost:8000
```
