# Vellum App Launcher

A dark-themed desktop launcher for downloading, updating, and running
Vellum's suite of tools.

## Running it

```
python main.py
```

Requires Python 3.8+ with tkinter (bundled on Windows/macOS; on Linux run
`sudo apt install python3-tk` first). No other dependencies.

## Project layout

```
vellum-launcher/
├── main.py              ← run this
├── apps.json             ← app registry (name, category, icon, download URL...)
├── plugins/               ← downloaded app scripts land here at runtime
└── launcher/               ← application package
    ├── theme.py             design tokens (colors, fonts)
    ├── paths.py              filesystem locations
    ├── data.py                registry load/save + update checks
    ├── download.py             downloading & launching plugin scripts
    ├── widgets.py               buttons, badges, scrollable frame
    ├── dialogs.py                toast + download progress dialog
    └── app.py                    the Launcher window and its pages
```

Previously this was a single ~1,000-line script; it's now split by
responsibility so each concern (styling, data, UI widgets, pages) can be
edited independently.

## What changed recently

- **Directory structure.** Split the single `launcher.py` file into the
  package above, with `main.py` as the entry point.
- **Theme.** Recolored to black / gray surfaces with a dark blue accent
  (`launcher/theme.py`).
- **Icons.** Replaced the old text-abbreviation icons (`INS`, `VVC`, ...)
  with single glyphs that fit the monochrome-blue theme and hint at what
  each app does (↓ install, ▶ clip, ▦ organize, ♫ convert, ◷ clock,
  ▲ track, ◆ review, ● record).
- **Scrolling.** Fixed a real bug: the old code bound mouse-wheel events
  globally (`bind_all`) every time a scrollable page was built, so only
  the *last*-built page actually responded to the wheel/touchpad —
  whichever page you were looking at often didn't scroll. Wheel and
  touchpad scrolling is now bound only while the pointer is over that
  page's own canvas, and delta handling is tuned per platform (Windows,
  macOS trackpads, Linux `Button-4`/`Button-5`).
- **apps.json.** Fixed typos ("Organzer" → "Organizer", "Businesss" →
  "Business"), rewrote descriptions, and made category names consistent
  (`Utilities` / `Creator` / `Business` / `Gaming`) — the old file mixed
  casing like `"gaming"` vs `"Gaming"`, which silently broke the category
  filter tabs since the match was case-sensitive. The category-tab filter
  in `app.py` is now also case-insensitive as a safety net.
- Same eight products throughout — only names, descriptions, categories,
  icons, and colors were touched.

## Adding new products without redistributing the launcher

`apps.json` bundled with the launcher is only the *offline fallback* copy.
If you set `CATALOG_URL` in `launcher/data.py` to a JSON file you host
somewhere (a GitHub raw link works fine — no server needed), the launcher
fetches it on every startup and merges it in:

- add a new app to the hosted catalog → it shows up in everyone's Store
  next time they open the launcher
- bump an app's `"version"` in the catalog → anyone with it installed sees
  it flagged on the Updates page automatically

The hosted file uses the exact same shape as `apps.json` (a `launcher`
info block, `categories`, and `apps`). Nobody needs a new copy of the
launcher itself for either of those — only for changes to the launcher's
own code.

Each user's local `installed` / `installed_path` / `installed_version`
state is never touched by a sync — only catalog-level fields (name,
description, category, icon, script, download_url, version) get
refreshed from the remote copy.

## Getting apps onto disk

Gumroad product links are checkout pages, not direct file URLs, so there's
no way to fetch them headlessly (and no reason to try — that's just
routing around checkout). The "Download" / "Update" buttons instead:

1. open the product's Gumroad page in your real default browser — you
   check out and download exactly like you always would
2. let you point the launcher at the file once it's landed in your
   Downloads folder, and it copies (or, for a zip, extracts) it into
   `plugins/`
