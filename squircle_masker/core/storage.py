"""JSON persistence for custom icon paths and background modes."""

import os
import json

CUSTOM_PATHS_FILE = os.path.expanduser("~/.config/squircle_masker_custom_paths.json")
CUSTOM_BG_FILE = os.path.expanduser("~/.config/squircle_masker_bg_modes.json")


def get_custom_icon_path(icon_name):
    """Get the custom icon path for a given application icon name."""
    if os.path.exists(CUSTOM_PATHS_FILE):
        try:
            with open(CUSTOM_PATHS_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get(icon_name)
        except Exception:
            pass
    return None


def set_custom_icon_path(icon_name, path):
    """Set or delete the custom icon path for a given application icon name."""
    data = {}
    if os.path.exists(CUSTOM_PATHS_FILE):
        try:
            with open(CUSTOM_PATHS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    if path is None:
        data.pop(icon_name, None)
    else:
        data[icon_name] = path

    try:
        os.makedirs(os.path.dirname(CUSTOM_PATHS_FILE), exist_ok=True)
        with open(CUSTOM_PATHS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def get_custom_bg_mode(icon_name):
    """
    Get the saved background mode and custom color for a given icon.
    Returns (bg_mode, custom_color) tuple.
    """
    if os.path.exists(CUSTOM_BG_FILE):
        try:
            with open(CUSTOM_BG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                entry = data.get(icon_name, {})
                return entry.get("bg_mode", "white"), entry.get("custom_color")
        except Exception:
            pass
    return "white", None


def set_custom_bg_mode(icon_name, bg_mode, custom_color=None):
    """Save the background mode and optional custom color for a given icon."""
    data = {}
    if os.path.exists(CUSTOM_BG_FILE):
        try:
            with open(CUSTOM_BG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    if bg_mode is None:
        data.pop(icon_name, None)
    else:
        data[icon_name] = {"bg_mode": bg_mode, "custom_color": custom_color}

    try:
        os.makedirs(os.path.dirname(CUSTOM_BG_FILE), exist_ok=True)
        with open(CUSTOM_BG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass
