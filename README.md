# 🟦 Squircle Masker

**v1.3.0** · Python · GTK 3 · GNOME

A Python utility that applies **macOS-style squircle masks** to application icons on Linux desktop environments (GNOME). Transform your Linux desktop icons into beautifully rounded squircle shapes — just like macOS.

> **Squircle** = **Squ**are + C**ircle** — a superellipse shape used by Apple for app icons.

---

## ✨ Features

- 🖼️ **Squircle Mask** — Automatically wraps any app icon in a macOS-style squircle frame with smart gradient background
- 🔵 **Circle Crop** — Crops icons into a perfect circle shape with gradient background
- 🎨 **Custom Icon** — Replace any app icon with your own image (PNG, JPG, SVG), with customizable background
- 🔙 **Restore Original** — Revert to the original system icon at any time
- 🎯 **Smart Color Detection** — Automatically detects dominant colors from the icon edges to create matching gradient backgrounds
- 🎨 **Background Modes** — Choose from White, Gray, Custom Color, or Auto background for custom icons
- 🔍 **Search & Filter** — Quickly find apps by name or icon name
- 🌐 **Multi-language** — Supports English and Vietnamese with auto-detection and manual switching
- 🖥️ **Dual Mode** — Both GUI (GTK 3) and CLI interfaces available
- ✅ **Batch Processing** — Select multiple apps with checkboxes and apply changes in one click
- 📦 **Wide App Support** — Detects apps from system packages, Flatpak, and Snap
- ⚡ **Live Preview** — Icons update in the GUI instantly after processing
- 🔄 **Icon Cache Refresh** — Automatically refreshes GNOME icon cache and toggles Dash-to-Dock for immediate effect

---

## 📸 Screenshots

<!-- Add screenshots here if available -->
<!-- ![GUI Screenshot](screenshots/gui.png) -->

---

## 📋 Requirements

| Dependency | Purpose |
|---|---|
| **Python 3** | Runtime |
| **GTK 3** (`gi` / PyGObject) | GUI framework |
| **ImageMagick 7+** (`magick` command) | Image conversion & processing |
| **Pillow** (Python PIL) | Smart color extraction |
| **A GTK icon theme** (e.g. MacTahoe / MacTahoe-dark) | Target theme to apply masks |

### Install dependencies (Arch Linux / Fedora / Ubuntu)

**Arch Linux:**
```bash
sudo pacman -S python python-gobject gtk3 imagemagick python-pillow
```

**Fedora:**
```bash
sudo dnf install python3 python3-gobject gtk3 ImageMagick python3-pillow
```

**Ubuntu / Debian:**
```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0 imagemagick python3-pil
```

---

## 🚀 Installation

### Quick Install

```bash
git clone https://github.com/your-username/SquircleMasker.git
cd SquircleMasker
chmod +x install.sh
./install.sh
```

The install script will:

1. Copy the application to `~/.local/share/SquircleMasker/`
2. Create symlinks in `~/.local/bin/` for terminal access
3. Create a `.desktop` entry so the app appears in your App Launcher

### After installation

- **App Launcher**: Search for **"Squircle Masker"** in your desktop environment's app menu
- **Terminal (GUI)**: Run `squircle-masker`
- **Terminal (CLI)**: Run `squircle-masker-cli`

### Uninstall

```bash
cd SquircleMasker
chmod +x uninstall.sh
./uninstall.sh
```

This removes all installed files, symlinks, and the `.desktop` entry.

---

## 📖 Usage

### GUI Mode

Launch the GUI application:

```bash
# After installation
squircle-masker

# Or run directly from source
python3 SquircleMasker.py
```

The GUI displays a list of all installed applications with their current icons. For each app, you can select a masking mode from the dropdown:

| Mode | Description |
|---|---|
| **From Theme** | Use the icon from the currently active GTK theme (default) |
| **Auto Squircle** | Apply a squircle mask with auto-detected gradient background colors |
| **Cropped Circle** | Crop the icon into a circle shape with auto-detected gradient background |
| **Original** | Symlink to the original system icon (bypasses theme) |
| **Custom Icon** | Select a custom image file and choose a background mode |

#### Custom Icon Background Modes

When selecting **Custom Icon**, you'll be prompted to choose a background style:

| Background Mode | Description |
|---|---|
| **White Background** | Solid white-to-light-gray gradient |
| **Gray Background** | Medium gray gradient |
| **Custom Color** | Pick any color using the color chooser dialog |
| **Auto** | Automatically detect colors from the custom image |

You can change the background mode later via the **Background** column dropdown.

#### Language Switching

Use the language selector in the header bar to switch between **English (EN)** and **Vietnamese (VN)**. The preference is saved to `~/.config/squircle_masker_lang.json`.

#### Search

Use the search bar at the top to filter apps by name or icon name.

---

### CLI Mode

The CLI mode processes a predefined list of apps (configured in `squircle_masker/config.py`):

```bash
# After installation
squircle-masker-cli

# Or run directly from source
python3 mask_icons.py

# Or as a Python module
python3 -m squircle_masker --cli
```

The CLI applies a static dark-gray squircle mask to all configured apps and refreshes the icon cache.

---

## 🗂️ Project Structure

```
SquircleMasker/
├── SquircleMasker.py                       # GUI launcher entry point
├── mask_icons.py                            # CLI launcher entry point
├── install.sh                               # Installation script
├── uninstall.sh                             # Uninstallation script
├── README.md
├── .gitignore
└── squircle_masker/                         # Main Python package
    ├── __init__.py                          # Package marker with version
    ├── __main__.py                          # Module entry point (python -m squircle_masker)
    │
    ├── config/                              # ⚙️ Configuration & Localization
    │   ├── __init__.py                      # Re-exports settings & i18n
    │   ├── settings.py                      # Theme dir, SVG templates, APPS_TO_MASK
    │   └── i18n.py                          # Internationalization (EN + VI)
    │
    ├── core/                                # 🧠 Business Logic (no GTK dependency)
    │   ├── __init__.py                      # Re-exports all core functions
    │   ├── processor.py                     # SVG generation (masked, cropped, custom)
    │   ├── resolver.py                      # Icon file searching across system dirs
    │   ├── analyzer.py                      # Smart color detection from images
    │   ├── sync.py                          # Theme directory syncing & cache refresh
    │   └── storage.py                       # JSON persistence for user preferences
    │
    ├── gui/                                 # 🖥️ GTK 3 GUI Layer
    │   ├── __init__.py                      # Re-exports run_gui
    │   └── window.py                        # Main SquircleApp window class
    │
    └── cli/                                 # ⌨️ CLI Interface
        ├── __init__.py                      # Re-exports run_cli
        └── runner.py                        # Batch icon processing
```

### Key Modules Explained

| Layer | Module | Description |
|---|---|---|
| **gui** | [window.py](squircle_masker/gui/window.py) | Main GTK 3 window. Scans `.desktop` files, provides combo dropdowns for masking mode and background selection, checkbox batch processing, and orchestrates icon processing via `core/` modules. |
| **cli** | [runner.py](squircle_masker/cli/runner.py) | Batch CLI processor. Iterates through `APPS_TO_MASK` config, applies static squircle masks, and updates the icon cache. |
| **core** | [processor.py](squircle_masker/core/processor.py) | Pure SVG generation — `generate_masked_svg()`, `generate_cropped_svg()`, `generate_custom_svg()`. Handles ImageMagick conversion, base64 encoding, and SVG template substitution. |
| **core** | [resolver.py](squircle_masker/core/resolver.py) | `find_original_icon()` searches system icon directories (hicolor, Flatpak, Snap, pixmaps), with fallback `find` commands. Also `fix_desktop_files()`. |
| **core** | [analyzer.py](squircle_masker/core/analyzer.py) | `get_smart_colors()` uses Pillow to sample edge pixels and extract dominant colors for gradient backgrounds. |
| **core** | [sync.py](squircle_masker/core/sync.py) | `sync_all_theme_icons()` handles backup/restore/symlink across MacTahoe theme variants. `refresh_icon_cache()` updates GTK cache and toggles Dash-to-Dock. |
| **core** | [storage.py](squircle_masker/core/storage.py) | JSON-based config I/O for custom icon paths and background modes. |
| **config** | [settings.py](squircle_masker/config/settings.py) | Constants: theme directory path, SVG templates (static for CLI, dynamic for GUI), and the `APPS_TO_MASK` dictionary. |
| **config** | [i18n.py](squircle_masker/config/i18n.py) | Locale dictionaries for English and Vietnamese. Auto-detects system language, supports manual override with persistence. |

---

## ⚙️ How It Works

### Masking Pipeline

```
Original Icon (PNG/SVG)
        │
        ▼
  ImageMagick converts to 128x128 transparent PNG
        │
        ▼
  Base64-encode the PNG data
        │
        ▼
  Pillow analyzes edge pixels for gradient colors (Auto mode)
        │
        ▼
  Embed into SVG template with squircle clip-path + gradient background
        │
        ▼
  Write SVG to theme directory (MacTahoe / MacTahoe-dark)
        │
        ▼
  Sync to all theme subdirectories (apps/22, categories/32, etc.)
        │
        ▼
  Refresh GTK icon cache + toggle Dash-to-Dock for immediate effect
```

### Smart Color Detection

The `get_smart_colors()` function:

1. Samples pixels along the **top and bottom edges** of the icon (avoiding corners)
2. Filters for **opaque pixels** (alpha > 200)
3. Uses `Counter.most_common()` to find the **dominant color** at each edge
4. Falls back to the **overall dominant opaque color** if edges are transparent
5. Creates a subtle **10% gradient** between top and bottom colors

### Theme Sync

The GUI syncs masked icons across:
- `~/.local/share/icons/MacTahoe/apps/scalable/`
- `~/.local/share/icons/MacTahoe-dark/apps/scalable/`
- All subdirectories containing matching icon files (via symlinks)
- Original theme icons are backed up with `.bak` extension for safe restoration

---

## 💾 Configuration Files

The app stores user preferences in `~/.config/`:

| File | Purpose |
|---|---|
| `squircle_masker_lang.json` | Saved language preference (`en` or `vi`) |
| `squircle_masker_custom_paths.json` | Custom icon file paths per app |
| `squircle_masker_bg_modes.json` | Background mode and custom color per app |

---

## 🔧 Customization

### Adding Apps to CLI Batch Processing

Edit `src/config.py` and add entries to the `APPS_TO_MASK` dictionary:

```python
APPS_TO_MASK = {
    "icon-name-to-save": "original-icon-name-or-path",
    "my-custom-app": "my-custom-app",
    "custom-app": "/path/to/custom/icon.png",
}
```

### Modifying SVG Templates

The squircle shape is defined as an SVG `<path>` in `src/config.py`:

- **`SVG_TEMPLATE_STATIC`** — Used by CLI, has a fixed dark-gray gradient
- **`SVG_TEMPLATE_DYNAMIC`** — Used by GUI, has placeholder `{color_top}` and `{color_bottom}` for dynamic gradients

---

## 🐛 Troubleshooting

### Icons not updating after masking

1. **X11**: Press `Alt+F2`, type `r`, and press Enter to restart GNOME Shell
2. **Wayland**: Log out and log back in
3. The app automatically tries to toggle Dash-to-Dock extension to force refresh

### ImageMagick errors

Make sure you have **ImageMagick 7+** installed (the `magick` command, not the legacy `convert`):

```bash
magick --version
```

### "Theme directory not found" error

Ensure you have the MacTahoe icon theme installed at:
```
~/.local/share/icons/MacTahoe-dark/apps/scalable/
```

### App not appearing in the list

The GUI scans `.desktop` files from:
- `/usr/share/applications/`
- `~/.local/share/applications/`
- `/var/lib/flatpak/exports/share/applications/`
- `~/.local/share/flatpak/exports/share/applications/`
- `/var/lib/snapd/desktop/applications/`

Make sure your app has a valid `.desktop` file with both `Name=` and `Icon=` fields.

---

## 📋 Changelog

### v1.3.0

- ✅ **Batch Selection** — Added checkbox column to select multiple apps at once
- 🔘 **Select All / Deselect All** — Quickly toggle all checkboxes
- ⚡ **Batch Apply** — Apply masking mode to all selected apps with a single click (icon cache refreshes only once at the end)
- 🏗️ **Project Restructuring** — Reorganized into layered architecture: `config/`, `core/`, `gui/`, `cli/`
- 🧩 **Modular Core** — Extracted icon processing, color analysis, theme syncing, and storage into standalone modules with no GTK dependency
- 🐍 **Module Entry Point** — Added `python -m squircle_masker` support
- 🌐 **i18n Updates** — Added Vietnamese and English translations for all new UI elements

### v1.2.1

- 🎨 **Custom Icon** — Select custom image files with background mode selection
- 🎨 **Background Modes** — White, Gray, Custom Color, Auto for custom icons
- 🔵 **Circle Crop** — New cropped circle masking mode
- 🎯 **Smart Color Detection** — Auto-detect gradient colors from icon edges
- 🌐 **Multi-language** — English and Vietnamese support

### v1.0.0

- 🖼️ **Initial Release** — Squircle masking with GUI and CLI
- 🔙 **Restore** — Revert icons to theme or original
- 🔍 **Search** — Filter apps by name

---

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

---

## 🙏 Credits

- Squircle (superellipse) shape inspired by **Apple's macOS icon design**
- Built with **GTK 3** (PyGObject), **ImageMagick**, and **Pillow**
