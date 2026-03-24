# Lobby Screen Manager

A Windows desktop application for corporate lobby displays that cycles through mixed content automatically.

Supports web URLs, PDFs, images, PowerPoint presentations, and Word documents in a configurable playlist with full-screen kiosk mode.

## Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| GUI Framework | PySide6 (Qt6) with Fusion style |
| Web/PDF Rendering | QWebEngineView (Chromium) |
| Image Processing | Pillow |
| Office Support | python-pptx, python-docx |
| Screen Wake | Windows SetThreadExecutionState API |
| Packaging | PyInstaller |

## Architecture Decisions

- **PySide6 over Tkinter/wxPython**: Qt6 provides a modern, corporate-quality UI with native look and feel, plus QWebEngineView for reliable web/PDF rendering.
- **QWebEngineView for PDFs**: Chromium's built-in PDF viewer handles PDFs cleanly without additional dependencies.
- **python-pptx + Pillow for PowerPoint**: Slides are rendered to PNG images as a practical fallback. This avoids requiring PowerPoint to be installed. Complex elements (charts, SmartArt) are rendered as placeholders.
- **python-docx for Word**: Documents are converted to styled HTML and displayed in QWebEngineView. This handles headings, paragraphs, formatting, tables, and inline images.
- **QThreadPool for content loading**: File I/O and conversions run in background threads so the UI never freezes.

## Setup

### Prerequisites

- Python 3.12 or later
- Windows 10/11

### Install Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run from IDE / Command Line

```bash
python main.py
```

## Usage

### Playlist Editor

1. **Add File** — Browse for images, PDFs, PowerPoint, or Word files
2. **Add URL** — Enter a web URL (supports dashboards, Power BI reports, etc.)
3. **Edit** — Double-click any item or select and press Ctrl+E
4. **Remove** — Select an item and press Delete
5. **Reorder** — Use Ctrl+Up / Ctrl+Down to move items
6. **Settings** — Configure default durations, looping, screen wake, auto-start

### Playback

- **F5** — Start playback (opens full-screen kiosk window)
- **Shift+F5** — Stop playback
- **Esc** or **Ctrl+Shift+Q** — Exit kiosk mode

### Playlist Files

- Save/Load playlists as `.lsm.json` files
- The last-used playlist is auto-loaded on startup
- See `sample_playlist.lsm.json` for the format

### Global Settings

| Setting | Description |
|---------|------------|
| Default Duration | Time each item displays (seconds) |
| Loop | Restart playlist after last item |
| Keep Screen Awake | Prevent display sleep during playback |
| Refresh Web Pages | Reload URLs each time they're shown |
| Auto-Start | Begin playback when app launches |
| Transition Delay | Fade-in duration between items (ms) |

## Packaging as Standalone .exe

```bash
pip install pyinstaller

pyinstaller --name "LobbyScreenManager" ^
  --onedir ^
  --windowed ^
  --add-data "resources;resources" ^
  --hidden-import PySide6.QtWebEngineWidgets ^
  --hidden-import PySide6.QtWebEngineCore ^
  main.py
```

The output will be in `dist/LobbyScreenManager/`. Copy the entire folder to the target machine.

**Note:** QWebEngineView requires the Chromium runtime files, so `--onefile` is not recommended (it would create a very large exe with slow startup). Use `--onedir` instead.

## Content Type Support

| Type | Rendering Method | Notes |
|------|-----------------|-------|
| Web URLs | QWebEngineView (Chromium) | Full browser rendering, supports dashboards |
| PDF | QWebEngineView built-in viewer | Fit-to-screen, native scrolling |
| Images | QLabel with QPixmap | PNG, JPG, BMP, GIF, WebP. Aspect-ratio preserved |
| PowerPoint | python-pptx → Pillow → PNG slides | Best-effort rendering. Text, pictures, tables supported. Charts/SmartArt shown as placeholders |
| Word | python-docx → HTML → QWebEngineView | Headings, paragraphs, formatting, tables, inline images |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Shift+A | Add file |
| Ctrl+U | Add URL |
| Ctrl+E | Edit selected item |
| Delete | Remove selected item |
| Ctrl+Up | Move item up |
| Ctrl+Down | Move item down |
| Ctrl+N | New playlist |
| Ctrl+O | Open playlist |
| Ctrl+S | Save playlist |
| Ctrl+Shift+S | Save As |
| F5 | Start playback |
| Shift+F5 | Stop playback |
| Esc | Exit kiosk mode |
| Ctrl+Shift+Q | Exit kiosk mode |

## Project Structure

```
lobby-screen-manager/
├── main.py                       # Entry point
├── requirements.txt              # Python dependencies
├── sample_playlist.lsm.json     # Example playlist
├── .gitignore
├── README.md
├── app/
│   ├── __init__.py               # App constants
│   ├── application.py            # QApplication subclass
│   ├── models/
│   │   ├── playlist.py           # Data model (PlaylistItem, Playlist)
│   │   └── schema.py             # JSON validation
│   ├── ui/
│   │   ├── main_window.py        # Main editor window
│   │   ├── playback_window.py    # Full-screen kiosk display
│   │   ├── playlist_table.py     # Table model + view
│   │   ├── item_editor_dialog.py # Add/edit item dialog
│   │   └── settings_panel.py     # Global settings dialog
│   ├── engine/
│   │   ├── playback_engine.py    # QTimer-based playlist cycling
│   │   └── content_loader.py     # Background content preparation
│   ├── renderers/
│   │   ├── base.py               # RenderedContent container
│   │   ├── web_renderer.py       # Web URL handling
│   │   ├── image_renderer.py     # Image file loading
│   │   ├── pdf_renderer.py       # PDF file handling
│   │   ├── pptx_renderer.py      # PowerPoint rendering
│   │   └── docx_renderer.py      # Word document rendering
│   ├── services/
│   │   ├── screen_wake.py        # Windows sleep prevention
│   │   ├── file_converter.py     # PPTX→PNG, DOCX→HTML conversion
│   │   └── temp_manager.py       # Temp file lifecycle
│   └── utils/
│       ├── logging_config.py     # Rotating log file setup
│       └── paths.py              # App data directories
└── resources/
    └── styles/
        └── main.qss              # Qt stylesheet
```

## Logging

Logs are written to `%LOCALAPPDATA%\LobbyScreenManager\logs\lobby_screen_manager.log` with automatic rotation (5 MB max, 3 backups).

## Troubleshooting

| Issue | Solution |
|-------|---------|
| App won't start | Ensure Python 3.12+ and all dependencies are installed |
| Web pages don't render | QWebEngineView requires the Chromium runtime. Ensure PySide6-WebEngine is installed |
| PowerPoint slides look different | The built-in renderer is best-effort. For pixel-perfect rendering, export slides to PDF or images first |
| Screen still sleeps | Run as administrator, or check Windows power settings |
| UNC paths fail | Ensure the network drive is accessible and the user has read permissions |
| High memory usage | QWebEngineView uses Chromium under the hood. This is normal for web rendering |

## Limitations and Future Improvements

### Current Limitations
- PowerPoint rendering is best-effort (no charts, SmartArt, animations, or gradient fills)
- Word documents lose complex formatting (footnotes, headers/footers, tracked changes)
- No video file support (can be added via QMediaPlayer)
- Single monitor only (displays on primary)

### Planned Improvements
- Video file support (MP4, AVI, WMV)
- Transition effects (slide, fade, dissolve)
- Multi-monitor support with per-display playlists
- Remote admin mode (web-based playlist management)
- Scheduled playlists (different content at different times)
- Authentication proxy for protected dashboards
- System tray icon with quick controls

## Git

**Recommended repo name:** `lobby-screen-manager`

**Recommended first commit message:**
```
Initial implementation of Lobby Screen Manager

Full-featured Windows desktop app for corporate lobby displays.
Supports web URLs, PDFs, images, PowerPoint, and Word documents
in a configurable playlist with kiosk mode and screen-wake.
```

## Changelog

### v1.0.0 (2026-03-24)
- Initial release
- Playlist editor with add/remove/edit/reorder
- Full-screen kiosk playback mode
- Content support: Web URLs, PDFs, images, PPTX, DOCX
- Keep-screen-awake via Windows API
- Playlist save/load as JSON
- Auto-load last playlist on startup
- Rotating log files
- Corporate-style Qt UI with Fusion theme
- PyInstaller packaging support
