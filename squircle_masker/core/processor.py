"""Core icon processing: generate masked, cropped, and custom SVG icons."""

import subprocess
import base64

from ..config.settings import SVG_TEMPLATE_DYNAMIC
from .analyzer import get_smart_colors


def resolve_bg_colors(png_data, bg_mode="auto", custom_color=None):
    """Determine background top and bottom gradient colors based on mode."""
    if bg_mode == "white":
        return "#ffffff", "#f0f0f0"
    elif bg_mode == "gray":
        return "#e0e0e0", "#c0c0c0"
    elif bg_mode == "custom_color" and custom_color:
        try:
            r = int(custom_color[1:3], 16)
            g = int(custom_color[3:5], 16)
            b_val = int(custom_color[5:7], 16)
            color_bot = "#{:02x}{:02x}{:02x}".format(
                max(0, int(r * 0.9)),
                max(0, int(g * 0.9)),
                max(0, int(b_val * 0.9))
            )
            return custom_color, color_bot
        except Exception:
            return "#ffffff", "#f0f0f0"
    elif bg_mode == "auto":
        return get_smart_colors(png_data)
    else:
        return "#ffffff", "#f0f0f0"


def generate_masked_svg(icon_path, bg_mode="auto", custom_color=None):
    """
    Generate a squircle-masked SVG from an icon file.
    Returns the SVG content string with gradient background.
    """
    cmd = ["magick", icon_path, "-background", "none", "-resize", "512x512", "png:-"]
    png_data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    b64 = base64.b64encode(png_data).decode('utf-8')

    color_top, color_bot = resolve_bg_colors(png_data, bg_mode, custom_color)

    svg_content = (
        SVG_TEMPLATE_DYNAMIC
        .replace("{b64}", b64)
        .replace("{color_top}", color_top)
        .replace("{color_bottom}", color_bot)
    )
    if "<!-- SquircleMasker" not in svg_content:
        svg_content = "<!-- SquircleMasker -->\n" + svg_content
    return svg_content


def generate_cropped_svg(icon_path, bg_mode="auto", custom_color=None):
    """
    Generate a circle-cropped SVG from an icon file.
    Returns the SVG content string with gradient background.
    """
    cmd = [
        "magick", icon_path, "-background", "none", "-resize", "512x512!",
        "(", "-size", "512x512", "xc:none", "-fill", "white", "-draw", "circle 256,256 256,0", ")",
        "-compose", "DstIn", "-composite", "png:-"
    ]
    png_data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    b64 = base64.b64encode(png_data).decode('utf-8')

    color_top, color_bot = resolve_bg_colors(png_data, bg_mode, custom_color)

    svg_content = f"""<!-- SquircleMaskerCropped -->
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="512" viewBox="0 0 128 128">
  <defs>
    <linearGradient id="bg" x1="64" x2="64" y1="0" y2="128" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{color_top}"/>
      <stop offset="1" stop-color="{color_bot}"/>
    </linearGradient>
  </defs>
  <circle cx="64" cy="64" r="64" fill="url(#bg)"/>
  <image xlink:href="data:image/png;base64,{b64}" width="96" height="96" x="16" y="16" preserveAspectRatio="xMidYMid meet"/>
</svg>"""
    return svg_content


def generate_custom_svg(icon_path, bg_mode="white", custom_color=None):
    """
    Generate a custom-icon SVG with the specified background mode.
    Returns the SVG content string.
    """
    cmd = ["magick", icon_path, "-background", "none", "-resize", "512x512", "png:-"]
    png_data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    b64 = base64.b64encode(png_data).decode('utf-8')

    color_top, color_bot = resolve_bg_colors(png_data, bg_mode, custom_color)

    svg_content = (
        SVG_TEMPLATE_DYNAMIC
        .replace("{b64}", b64)
        .replace("{color_top}", color_top)
        .replace("{color_bottom}", color_bot)
    )
    svg_content = svg_content.replace("<!-- SquircleMasker -->", "<!-- SquircleMaskerCustom -->")
    if "<!-- SquircleMaskerCustom" not in svg_content:
        svg_content = "<!-- SquircleMaskerCustom -->\n" + svg_content
    return svg_content
