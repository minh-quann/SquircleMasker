"""Sync masked icons across GTK theme directories and refresh caches."""

import os
import subprocess
import time


def sync_all_theme_icons(icon_name, state, svg_content=None, orig_path=None, visited=None):
    """
    Sync icon changes across MacTahoe, MacTahoe-dark, and hicolor theme directories.
    Handles backup, restore, and symlink creation for all theme subdirectories.
    """
    if visited is None:
        visited = set()
    if icon_name in visited:
        return
    visited.add(icon_name)
    base_dirs = [
        os.path.expanduser("~/.local/share/icons/MacTahoe"),
        os.path.expanduser("~/.local/share/icons/MacTahoe-dark"),
        os.path.expanduser("~/.local/share/icons/hicolor")
    ]
    scalable_paths = {
        "light": os.path.expanduser(f"~/.local/share/icons/MacTahoe/apps/scalable/{icon_name}.svg"),
        "dark": os.path.expanduser(f"~/.local/share/icons/MacTahoe-dark/apps/scalable/{icon_name}.svg"),
        "hicolor": os.path.expanduser(f"~/.local/share/icons/hicolor/scalable/apps/{icon_name}.svg")
    }

    # Alias mapping for apps with multiple icon names (e.g. coccoc-browser and com.coccoc.Browser)
    aliases = []
    if icon_name == "coccoc-browser":
        aliases = ["com.coccoc.Browser"]
    elif icon_name == "com.coccoc.Browser":
        aliases = ["coccoc-browser"]
    elif icon_name == "rquickshare":
        aliases = ["net.cozic.RQuickShare"]
    elif icon_name == "net.cozic.RQuickShare":
        aliases = ["rquickshare"]

    # 1. Backup scalable files if they are the original theme files
    for key, p in scalable_paths.items():
        bak_p = f"{p}.bak"
        if os.path.exists(p) and not os.path.islink(p):
            is_masked = False
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    header = f.read(100)
                if "<!-- SquircleMasker" in header:
                    is_masked = True
            except Exception:
                pass
            if not is_masked and not os.path.exists(bak_p):
                os.rename(p, bak_p)

    # 2. Process scalable files based on state
    if state == "theme":
        for key, p in scalable_paths.items():
            bak_p = f"{p}.bak"
            if os.path.exists(p):
                if os.path.islink(p):
                    os.remove(p)
                else:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        header = f.read(100)
                    if "<!-- SquircleMasker" in header:
                        os.remove(p)
            if os.path.exists(bak_p):
                os.rename(bak_p, p)
    elif state == "original" and orig_path:
        for key, p in scalable_paths.items():
            if os.path.lexists(p):
                os.remove(p)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            os.symlink(orig_path, p)
    else:  # custom, masked, cropped
        if svg_content:
            for key, p in scalable_paths.items():
                if os.path.lexists(p):
                    os.remove(p)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w") as f:
                    f.write(svg_content)

            # Generate PNG files for hicolor resolutions & pixmaps for dock/desktop compatibility
            # Generate PNG files for hicolor resolutions & pixmaps for dock/desktop compatibility
            hicolor_svg = scalable_paths.get("hicolor")
            if hicolor_svg and os.path.exists(hicolor_svg):
                for size in ["512x512", "256x256", "128x128", "48x48", "32x32", "22x22"]:
                    out_dir = os.path.expanduser(f"~/.local/share/icons/hicolor/{size}/apps")
                    os.makedirs(out_dir, exist_ok=True)
                    out_png = os.path.join(out_dir, f"{icon_name}.png")
                    subprocess.run(
                        ["magick", "-density", "300", "-background", "none", hicolor_svg, "-filter", "Lanczos", "-resize", size, out_png],
                        stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                    )
                pix_dir = os.path.expanduser("~/.local/share/pixmaps")
                os.makedirs(pix_dir, exist_ok=True)
                pix_png = os.path.join(pix_dir, f"{icon_name}.png")
                subprocess.run(
                    ["magick", "-density", "300", "-background", "none", hicolor_svg, "-filter", "Lanczos", "-resize", "512x512", pix_png],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                )

    # 3. Process extra directories (apps/22, categories/32, preferences/32 etc.)
    for base_dir in base_dirs:
        if not os.path.exists(base_dir):
            continue
        is_dark = "dark" in base_dir.lower()
        target_scalable = scalable_paths["dark"] if is_dark else scalable_paths["light"]
        if "hicolor" in base_dir:
            target_scalable = scalable_paths["hicolor"]

        for root, dirs, files in os.walk(base_dir):
            if "scalable" in root:
                continue
            for file in files:
                if file in (f"{icon_name}.svg", f"{icon_name}.png"):
                    full_path = os.path.join(root, file)
                    bak_path = f"{full_path}.bak"

                    if state == "theme":
                        # Restore original icon in extra folders
                        if os.path.islink(full_path):
                            os.remove(full_path)
                        elif os.path.exists(full_path):
                            try:
                                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    header = f.read(100)
                                if "<!-- SquircleMasker" in header:
                                    os.remove(full_path)
                            except Exception:
                                pass
                        if os.path.exists(bak_path):
                            os.rename(bak_path, full_path)
                    else:
                        # Backup original non-link file
                        if os.path.exists(full_path) and not os.path.islink(full_path):
                            is_masked = False
                            if file.endswith(".svg"):
                                try:
                                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        header = f.read(100)
                                    if "<!-- SquircleMasker" in header:
                                        is_masked = True
                                except Exception:
                                    pass
                            if not is_masked and not os.path.exists(bak_path):
                                os.rename(full_path, bak_path)

                        if os.path.lexists(full_path):
                            os.remove(full_path)

                        try:
                            if file.endswith(".svg"):
                                os.symlink(target_scalable, full_path)
                            else:
                                # For PNG files, render actual PNG at target resolution instead of broken SVG symlink
                                folder_name = os.path.basename(root)
                                target_size = folder_name if ("x" in folder_name and folder_name[0].isdigit()) else "512x512"
                                subprocess.run(
                                    ["magick", "-density", "300", "-background", "none", target_scalable, "-filter", "Lanczos", "-resize", target_size, full_path],
                                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                                )
                        except Exception:
                            pass

    # Sync aliases if present
    for alias in aliases:
        sync_all_theme_icons(alias, state, svg_content=svg_content, orig_path=orig_path, visited=visited)


def refresh_icon_cache():
    """Refresh GTK icon cache and toggle Dash-to-Dock extension for immediate visual update."""
    from .resolver import fix_desktop_files
    fix_desktop_files()

    subprocess.run("gtk-update-icon-cache -f -t ~/.local/share/icons/MacTahoe-dark/ 2>/dev/null", shell=True)
    subprocess.run("gtk-update-icon-cache -f -t ~/.local/share/icons/MacTahoe/ 2>/dev/null", shell=True)
    subprocess.run("gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor/ 2>/dev/null", shell=True)
    subprocess.run("touch ~/.local/share/icons", shell=True)
    subprocess.run("touch ~/.local/share/applications", shell=True)
    subprocess.run("update-desktop-database ~/.local/share/applications/ 2>/dev/null", shell=True)

    # Toggle Dash to Dock extension to force icon cache refresh
    # (GNOME 50+ disables Shell.Eval, this is the only reliable method)
    try:
        result = subprocess.check_output(
            "gnome-extensions list --enabled 2>/dev/null",
            shell=True, text=True
        ).strip()
        dock_extensions = [
            ext for ext in result.split('\n')
            if 'dock' in ext.lower() or 'dash' in ext.lower()
        ]
        for ext in dock_extensions:
            subprocess.run(
                f"gnome-extensions disable {ext}",
                shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
            )
        if dock_extensions:
            time.sleep(0.5)
        for ext in dock_extensions:
            subprocess.run(
                f"gnome-extensions enable {ext}",
                shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
            )
    except Exception:
        pass
