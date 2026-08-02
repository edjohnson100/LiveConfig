# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LiveConfig is an Autodesk Fusion HTML palette add-in (version 1.2.0) for parametric configuration management. It provides live user-parameter editing, configuration "Snapshots" (parameter values + timeline feature suppression, saved/restored as a set), `CFG_`-prefixed timeline feature tracking, and a theme manager — all within a docked palette UI inside Fusion.

## Architecture

Three-layer architecture, same shape as the rest of the fleet (FingerJointsLive, LiveUtilities, GridfinityGeneratorPlus):

### 1. Event Handler Layer — [LiveConfig.py](LiveConfig.py)
Entry point registered with Fusion.
- `MyCommandCreatedHandler` / `MyCommandExecuteHandler` — creates the palette on first invocation (or shows it if it already exists), restoring saved geometry via `config_logic._restore_palette_geometry()`.
- `MyHTMLEventHandler` — routes every frontend `action` string to the matching `config_logic` function, then (for actions that change state) re-scans and pushes a fresh `update_ui` payload back to HTML.
- `MyDocActivatedHandler` — re-scans and refreshes the palette when the user switches between open documents, so a `refresh_data` round-trip isn't needed after every doc switch.
- `MyPaletteCloseHandler` — saves palette geometry on close (the other save point is `stop()`, since Fusion's `Palette` has no resize/move event — geometry is only readable on demand).

### 2. Business Logic Layer — [config_logic.py](config_logic.py)
All Fusion API interactions.
- `scan_model()` — master aggregator: user parameters, `CFG_`-prefixed timeline features/groups, saved snapshots, and the active-config attribute, returned as one JSON payload alongside `addin_version` and `imported_themes`. Called after nearly every write action.
- `save_snapshot()` / `apply_snapshot()` / `delete_snapshot()` — snapshot state stored in `root.attributes` (group `EdJ_Data`), travels with the `.f3d` file. Each snapshot has `params` (name → expression) and `features` (name → isSuppressed).
- `update_parameter()` / `toggle_favorite()` / `toggle_feature()` — direct parameter/feature edits.
- `export_theme_logic(file_type, content, default_name)` / `import_theme_logic(file_type)` — `file_type` is `'css'` or `'json'`, picks the file-dialog filter accordingly. `import_theme_logic` returns the `{"file_type": ..., "content": ...}` envelope itself; `LiveConfig.py` forwards it straight to HTML without re-wrapping it.
- `save_imported_theme()` / `delete_imported_theme()` / `clear_imported_themes()` — host-side persistence for user-imported/edited themes (`imported_themes.json`), independent of the three built-in themes baked into `style.css`.
- `_save_palette_geometry()` / `_restore_palette_geometry()` — width/height/left/top/dockingState, persisted to `config.json`.
- `_read_manifest_version()` — reads `version` from `LiveConfig.manifest` at import time into module-level `ADDIN_VERSION`. Never hardcode a version string anywhere else in this repo.

### 3. Frontend Layer — [resources/html/index.html](resources/html/index.html) + [resources/html/script.js](resources/html/script.js)
Vanilla HTML/CSS/JS, no frameworks. Communicates via `sendToFusion(action, data)` (JS→Python, tries `window.adsk.fusion.sendCommand` then falls back to `window.adsk.fusionSendData`) and `window.fusionJavaScriptHandler.handle(action, data)` (Python→JS).

- **2 tabs:** `#tab-configs` (Snapshots, Live Parameters, Tracked Features — everything the app does) and `#tab-themes` (theme manager). `switchTab()` persists the active tab to `localStorage` (`ll_config_active_tab`).
- **Startup round-trip:** `waitForFusion()` retries every 500ms (up to 20 attempts) until `window.adsk` exists, then calls `refreshData()`. Any new "ask Python for state on open" flow should piggyback on this existing retry loop rather than adding a fresh unconditional send — a single unconditional send can silently no-op forever if it races Fusion's bridge injection.
- **Theme engine:** unlike LiveUtilities/FingerJointsLive, LiveConfig does **not** parse its built-in themes out of `style.css` at runtime. `builtInThemeIds` is a fixed `Set(['light', 'dark', 'sepia'])` in `script.js`; `:root` in `style.css` **is** the `light` theme (there's no separate `[data-theme="light"]` block). `generateFullCSS()` builds a full bundle by temporarily setting `data-theme` to each built-in + custom id and reading `getComputedStyle()`, rather than keeping a second copy of the built-in hex values in JS. `parseStyleCSS()` maps an imported bundle's `:root` block to id `'light'` on the way back in.
- Font property overrides (`updateActiveThemeProperty()`) are `localStorage`-only — they are not host-persisted to `imported_themes.json` unless the theme is explicitly imported/exported as a file.

## Data Persistence

| Storage | What it holds |
|---|---|
| `root.attributes` (group `EdJ_Data`) | Snapshots (`params` + `features`), last-active-config — travels with the `.f3d` file |
| `imported_themes.json` (gitignored) | User-imported/edited themes, per-machine |
| `config.json` (gitignored) | Palette geometry (width/height/left/top/dockingState) |
| Browser `localStorage` | Active tab, theme selection, custom theme overrides (incl. font overrides not yet imported/exported), favorites-only filter state |

## CFG_ Naming Convention

Root-component features and timeline groups prefixed `CFG_` are tracked in **Tracked Features** and can be individually suppressed/unsuppressed from the palette, independent of Snapshots (which capture suppression state as part of a saved config, but don't define which features are trackable).

## UI Layout (post fleet-standardization, 2026-08)

Structural elements now match the rest of the fleet — see `Archive/!Fleet_Standardization_Prompt.md` and `Archive/!Dev_Notes.md` for the full rationale:
- **Header:** title + version stacked left (`#versionTag`), theme `<select>` right — the only header control.
- **Footer:** centered two-line `.version-footer` outside both tabs — add-in name + manifest-sourced version. The "Month Year" trailer in `renderUI()` (`script.js`) is a hardcoded string, bump it by hand on every release that ships in a different month.
- **No Common Settings block** — nothing here is shared across just the 2 tabs, so this fleet-standard element was deliberately omitted.

## Development Notes

- **No build pipeline.** Pure Python + vanilla JS; no npm, no bundler, no test framework.
- **No external Python dependencies.** Only `adsk.core` / `adsk.fusion` (Fusion's built-in modules).
- **Testing:** manual, inside Fusion, via the Scripts and Add-ins panel. Changes to `.py` files require reloading the add-in; HTML/JS/CSS changes are picked up on palette reload/reopen.
- **`Archive/`** (gitignored) holds `!Dev_Notes.md`, `!Release_Notes.md`, `!Next_Chat.md`, and one-off planning docs like the fleet standardization prompt — personal working notes, not shipped, not for review.
- **Version bumps:** update `LiveConfig.manifest`'s `version` field only — everything else (header, footer, palette title) reads from it via `ADDIN_VERSION`.
