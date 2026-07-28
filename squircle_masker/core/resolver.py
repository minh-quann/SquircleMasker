"""Find original icon files from system directories and fix .desktop paths."""

import os
import subprocess

from ..config.settings import APPS_TO_MASK
from ..config.i18n import t


def find_original_icon(icon_name):
    """Search all installed system icon themes and directories for the highest resolution original icon."""
    if not icon_name:
        return None
    if icon_name.startswith('/'):
        return icon_name

    custom_map = {
        "android-studio": os.path.expanduser("~/.local/share/android-studio/bin/studio.png"),
        "jetbrains-studio": os.path.expanduser("~/.local/share/android-studio/bin/studio.png")
    }
    if icon_name in custom_map and os.path.exists(custom_map[icon_name]):
        return custom_map[icon_name]

    base_dirs = [
        os.path.expanduser("~/.local/share/icons"),
        "/usr/share/icons",
        "/var/lib/flatpak/exports/share/icons",
    ]

    themes = []
    for base in base_dirs:
        if os.path.exists(base):
            for t_dir in os.listdir(base):
                if not t_dir.startswith("MacTahoe"):
                    full_t = os.path.join(base, t_dir)
                    if os.path.isdir(full_t) and full_t not in themes:
                        themes.append(full_t)

    # 1. Search for SVG vector files across all installed themes
    for t_dir in themes:
        for sub in ["apps/scalable", "scalable/apps", "apps/symbolic", "scalable"]:
            p = os.path.join(t_dir, sub, f"{icon_name}.svg")
            if os.path.exists(p) and not os.path.islink(p):
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        hdr = f.read(100)
                    if "<!-- SquircleMasker" in hdr:
                        bak_p = f"{p}.bak"
                        if os.path.exists(bak_p):
                            return bak_p
                        continue
                except Exception:
                    pass
                return p

    # 2. Search for PNGs in high-resolution folders (512 -> 256 -> 128 -> 64 -> 48)
    for size in ["512x512", "256x256", "128x128", "64x64", "48x48"]:
        for t_dir in themes:
            for sub in [f"apps/{size}", f"{size}/apps", "apps"]:
                p = os.path.join(t_dir, sub, f"{icon_name}.png")
                if os.path.exists(p) and not os.path.islink(p):
                    return p

    # 3. Search pixmaps and fallback directories
    pixmap_dirs = ["/usr/share/pixmaps", "/var/lib/flatpak/exports/share/pixmaps"]
    for d in pixmap_dirs:
        for ext in [".svg", ".png", ".webp"]:
            p = os.path.join(d, icon_name + ext)
            if os.path.exists(p):
                return p

    # 4. Fallback search using find
    try:
        cmd = (
            f"find /usr/share/icons /usr/share/pixmaps /var/lib/flatpak "
            f"~/.local/share/icons -type f \\( -name '{icon_name}.svg' -o -name '{icon_name}.png' \\) "
            f"| grep -v 'MacTahoe' | grep -v '\\.bak' | head -1"
        )
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        if out:
            return out
    except Exception:
        pass

    return None


def fix_desktop_files():
    """Fix .desktop files that use absolute paths or generic fallback icons, and ensure StartupWMClass."""
    print(t("fixing_desktop"))
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    if not os.path.exists(desktop_dir):
        return

    known_fixes = {
        "antigravity-ide.desktop": {"icon": "antigravity-ide", "wmclass": "antigravity-ide"},
        "antigravity.desktop": {"icon": "antigravity", "wmclass": "antigravity"},
    }

    for f in os.listdir(desktop_dir):
        if not f.endswith(".desktop"):
            continue
        path = os.path.join(desktop_dir, f)
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            modified = False
            if f in known_fixes:
                target_icon = known_fixes[f]["icon"]
                target_wmclass = known_fixes[f]["wmclass"]
                for line in content.splitlines():
                    if line.startswith("Icon=") and line != f"Icon={target_icon}":
                        content = content.replace(line, f"Icon={target_icon}")
                        modified = True
                if "StartupWMClass=" not in content:
                    content += f"\nStartupWMClass={target_wmclass}\n"
                    modified = True

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
