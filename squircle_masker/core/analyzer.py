"""Smart color detection from icon images for gradient backgrounds."""

import io
from collections import Counter

try:
    from PIL import Image
except ImportError:
    pass


def get_smart_colors(png_data):
    """
    Analyze PNG image data to extract dominant top and bottom edge colors.
    Returns a (color_top, color_bottom) tuple of hex color strings.
    """
    try:
        img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        width, height = img.size

        # Sample points along the top and bottom edge, avoiding extreme corners
        # to handle icons with rounded corners.
        top_points = [
            (x, y)
            for x in range(int(width * 0.2), int(width * 0.8), max(1, width // 10))
            for y in range(0, 3)
        ]
        bot_points = [
            (x, y)
            for x in range(int(width * 0.2), int(width * 0.8), max(1, width // 10))
            for y in range(height - 3, height)
        ]

        top_colors = []
        for x, y in top_points:
            try:
                r, g, b, a = img.getpixel((x, y))
                if a > 200:
                    top_colors.append((r, g, b))
            except Exception:
                pass

        bot_colors = []
        for x, y in bot_points:
            try:
                r, g, b, a = img.getpixel((x, y))
                if a > 200:
                    bot_colors.append((r, g, b))
            except Exception:
                pass

        c_top = None
        c_bot = None

        # Require a reasonable number of opaque pixels to consider it a solid edge background
        min_opaque = max(3, len(top_points) // 3)

        if len(top_colors) >= min_opaque:
            c_top = Counter(top_colors).most_common(1)[0][0]
        if len(bot_colors) >= min_opaque:
            c_bot = Counter(bot_colors).most_common(1)[0][0]

        if c_top and c_bot:
            pass  # Keep exact colors to preserve original gradient
        elif c_top:
            c_bot = c_top
        elif c_bot:
            c_top = c_bot
        else:
            # Edges are mostly transparent, fall back to dominant opaque color
            img_small = img.resize((50, 50))
            pixels = list(img_small.getdata())
            opaque = [(r, g, b) for r, g, b, a in pixels if a > 200]
            if opaque:
                base_color = Counter(opaque).most_common(1)[0][0]
            else:
                base_color = (50, 49, 49)  # Fallback dark gray

            # Create a subtle gradient for transparent-background icons
            c_top = tuple(min(255, int(c * 1.1)) for c in base_color)
            c_bot = tuple(max(0, int(c * 0.9)) for c in base_color)

        return (
            f"#{c_top[0]:02x}{c_top[1]:02x}{c_top[2]:02x}",
            f"#{c_bot[0]:02x}{c_bot[1]:02x}{c_bot[2]:02x}",
        )
    except Exception:
        return ("#3c3b3b", "#282828")
