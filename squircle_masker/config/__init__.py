"""Configuration package - settings and internationalization."""

from .settings import THEME_DIR, SVG_TEMPLATE_STATIC, SVG_TEMPLATE_DYNAMIC, APPS_TO_MASK
from . import i18n
from .i18n import t

__all__ = [
    "THEME_DIR", "SVG_TEMPLATE_STATIC", "SVG_TEMPLATE_DYNAMIC", "APPS_TO_MASK",
    "i18n", "t",
]
