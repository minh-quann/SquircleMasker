import os
import subprocess
import io
from collections import Counter
try:
    from PIL import Image
except ImportError:
    pass

from .config import APPS_TO_MASK

def get_smart_colors(png_data):
    try:
        img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        width, height = img.size
        
        # Check 4 corners and edges for solid colors
        corners = [(0, 0), (width-1, 0), (0, height-1), (width-1, height-1),
                   (width//2, 0), (0, height//2), (width-1, height//2), (width//2, height-1)]
        
        edge_colors = []
        for x, y in corners:
            r, g, b, a = img.getpixel((x, y))
            if a > 200:
                edge_colors.append((r, g, b))
                
        if len(edge_colors) >= 3:
            base_color = Counter(edge_colors).most_common(1)[0][0]
        else:
            # If edges are transparent, get the most common color from opaque pixels
            img_small = img.resize((50, 50))
            pixels = list(img_small.getdata())
            opaque = [(r, g, b) for r, g, b, a in pixels if a > 200]
            if opaque:
                base_color = Counter(opaque).most_common(1)[0][0]
            else:
                base_color = (50, 49, 49) # Fallback dark gray
                
        # Create a subtle gradient
        c_top = tuple(min(255, int(c * 1.1)) for c in base_color)
        c_bot = tuple(max(0, int(c * 0.9)) for c in base_color)
        
        return (f"#{c_top[0]:02x}{c_top[1]:02x}{c_top[2]:02x}", 
                f"#{c_bot[0]:02x}{c_bot[1]:02x}{c_bot[2]:02x}")
    except Exception:
        return ("#3c3b3b", "#282828")

def find_original_icon(icon_name):
    if not icon_name: return None
    if icon_name.startswith('/'): return icon_name
    
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
            if os.path.exists(p): return p
            
    # Process flatpak app folders (fallback)
    try:
        cmd = f"find /var/lib/flatpak/app -type f \\( -name '{icon_name}.png' -o -name '{icon_name}.svg' \\) | head -1"
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        if out: return out
    except Exception:
        pass
        
    # Last resort fallback similar to CLI version
    try:
        cmd = f"find /usr/share/icons /usr/share/pixmaps /var/lib/flatpak/app /var/lib/flatpak/exports/share/icons ~/.local/share/icons -type f \\( -name '{icon_name}.png' -o -name '{icon_name}.svg' \\) | grep -v 'MacTahoe' | head -1"
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        if out: return out
    except Exception:
        pass

    return None

def fix_desktop_files():
    print("Fixing .desktop files with absolute paths...")
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    if not os.path.exists(desktop_dir):
        return
        
    for f in os.listdir(desktop_dir):
        if not f.endswith(".desktop"): continue
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
                print(f" -> Fixed Icon in {f}")
        except Exception as e:
            print(f" -> Error processing {f}: {e}")
