"""Core business logic package - icon processing with no GTK dependency."""

from .processor import generate_masked_svg, generate_cropped_svg, generate_custom_svg
from .resolver import find_original_icon, fix_desktop_files
from .analyzer import get_smart_colors
from .sync import sync_all_theme_icons, refresh_icon_cache
from .storage import (
    get_custom_icon_path, set_custom_icon_path,
    get_custom_bg_mode, set_custom_bg_mode,
)

__all__ = [
    "generate_masked_svg", "generate_cropped_svg", "generate_custom_svg",
    "find_original_icon", "fix_desktop_files",
    "get_smart_colors",
    "sync_all_theme_icons", "refresh_icon_cache",
    "get_custom_icon_path", "set_custom_icon_path",
    "get_custom_bg_mode", "set_custom_bg_mode",
]
