"""CLI batch processing for SquircleMasker."""

import os
import subprocess
import base64

from ..config.settings import THEME_DIR, SVG_TEMPLATE_STATIC, APPS_TO_MASK
from ..core.resolver import find_original_icon, fix_desktop_files
from ..core.sync import sync_all_theme_icons, refresh_icon_cache
from ..config.i18n import t


def run_cli():
    """Process all apps in APPS_TO_MASK with static squircle masks."""
    if not os.path.exists(THEME_DIR):
        print(t("err_theme_not_found", theme_dir=THEME_DIR))
        return

    fix_desktop_files()
    subprocess.run("update-desktop-database ~/.local/share/applications/ 2>/dev/null", shell=True)
    print("")

    for app, source in APPS_TO_MASK.items():
        print(t("masking_app", app=app))
        icon_path = find_original_icon(source)
        if not icon_path or not os.path.exists(icon_path):
            print(t("skip_not_found", app=app))
            continue

        # Use ImageMagick to convert original image to transparent PNG, base64
        cmd = ["magick", icon_path, "-background", "none", "-resize", "128x128", "png:-"]
        try:
            png_data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            b64 = base64.b64encode(png_data).decode('utf-8')
        except Exception:
            print(t("skip_err_convert", app=app))
            continue

        # Replace base64 in template
        svg_content = SVG_TEMPLATE_STATIC.replace("{b64}", b64)
        sync_all_theme_icons(app, "masked", svg_content=svg_content)
        print(t("success_create", app=app))

    print(t("reloading_cache"))
    refresh_icon_cache()
    print(t("done_msg"))


if __name__ == "__main__":
    run_cli()
