import os
import subprocess
import base64
from .config import THEME_DIR, SVG_TEMPLATE_STATIC, APPS_TO_MASK
from .utils import find_original_icon, fix_desktop_files
from .i18n import t

def run_cli():
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
        except Exception as e:
            print(t("skip_err_convert", app=app))
            continue
            
        # Replace base64 in template
        svg_content = SVG_TEMPLATE_STATIC.replace("{b64}", b64)
        out_path = os.path.join(THEME_DIR, f"{app}.svg")
        
        with open(out_path, "w") as f:
            f.write(svg_content)
        print(t("success_create", app=app))
        
    print(t("reloading_cache"))
    subprocess.run("gtk-update-icon-cache ~/.local/share/icons/MacTahoe-dark/ 2>/dev/null", shell=True)
    print(t("done_msg"))

if __name__ == "__main__":
    run_cli()
