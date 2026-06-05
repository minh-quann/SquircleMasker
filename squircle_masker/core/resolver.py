"""Find original icon files from system directories and fix .desktop paths."""

import os
import subprocess

from ..config.settings import APPS_TO_MASK
from ..config.i18n import t


def find_original_icon(icon_name):
    """Search multiple system directories to locate the original icon file."""
    if not icon_name:
        return None
    if icon_name.startswith('/'):
        return icon_name

    # Custom mappings for apps not following standard naming
    custom_map = {
        "android-studio": os.path.expanduser("~/.local/share/android-studio/bin/studio.png"),
        "jetbrains-studio": os.path.expanduser("~/.local/share/android-studio/bin/studio.png")
    }
    if icon_name in custom_map and os.path.exists(custom_map[icon_name]):
        return custom_map[icon_name]

    search_dirs = [
        "/usr/share/icons/hicolor/128x128/apps",
        "/usr/share/icons/hicolor/256x256/apps",
        "/usr/share/icons/hicolor/512x512/apps",
        "/usr/share/icons/hicolor/scalable/apps",
        "/usr/share/icons/hicolor/48x48/apps",
        "/usr/share/icons/hicolor/64x64/apps",
        "/usr/share/pixmaps",
        "/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps",
        "/var/lib/flatpak/exports/share/icons/hicolor/256x256/apps",
        "/var/lib/flatpak/exports/share/icons/hicolor/512x512/apps",
        "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
        "/var/lib/flatpak/app",
        os.path.expanduser("~/.local/share/icons/hicolor/128x128/apps"),
        os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps"),
        os.path.expanduser("~/.local/share/icons"),
    ]

    for ext in ['.png', '.svg', '.webp']:
        for d in search_dirs:
            p = os.path.join(d, icon_name + ext)
            if os.path.exists(p):
                return p

    # Process flatpak app folders (fallback)
    try:
        cmd = f"find /var/lib/flatpak/app -type f \\( -name '{icon_name}.png' -o -name '{icon_name}.svg' \\) | head -1"
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        if out:
            return out
    except Exception:
        pass

    # Last resort fallback
    try:
        cmd = (
            f"find /usr/share/icons /usr/share/pixmaps /var/lib/flatpak/app "
            f"/var/lib/flatpak/exports/share/icons ~/.local/share/icons "
            f"-type f \\( -name '{icon_name}.png' -o -name '{icon_name}.svg' \\) "
            f"| grep -v 'MacTahoe' | head -1"
        )
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        if out:
            return out
    except Exception:
        pass

    return None


def fix_desktop_files():
    """Fix .desktop files that use absolute paths for icons listed in APPS_TO_MASK."""
    print(t("fixing_desktop"))
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    if not os.path.exists(desktop_dir):
        return

    for f in os.listdir(desktop_dir):
        if not f.endswith(".desktop"):
            continue
        path = os.path.join(desktop_dir, f)
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            modified = False
            for icon_name, source_path in APPS_TO_MASK.items():
                if source_path.startswith("/") and f"Icon={source_path}" in content:
                    content = content.replace(f"Icon={source_path}", f"Icon={icon_name}")
                    modified = True

            if modified:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(content)
                print(t("fixed_icon", file=f))
        except Exception as e:
            print(f" -> Error processing {f}: {e}")
