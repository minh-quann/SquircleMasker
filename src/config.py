import os

# Current theme icon directory
THEME_DIR = os.path.expanduser("~/.local/share/icons/MacTahoe-dark/apps/scalable")

# Standard SVG template for MacTahoe-dark (Dark gray squircle) - Used by CLI
SVG_TEMPLATE_STATIC = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="64" height="64">
  <defs>
    <linearGradient id="bg" x1="32" x2="32" y1="4" y2="60" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#323131"/>
      <stop offset="1" stop-color="#141414"/>
    </linearGradient>
  </defs>
  <path fill="url(#bg)" d="M20.26 4c-5.782 0-9.743 1.725-12.321 4.535C5.374 11.331 4 15.34 4 19.876v24.248c0 4.538 1.374 8.545 3.939 11.341C10.517 58.275 14.479 60 20.26 60h23.549c5.782 0 9.743-1.724 12.321-4.535C58.695 52.67 60 49.03 60 44.125V20.786c0-5.935-1.305-9.456-3.87-12.252C53.552 5.725 49.59 4 43.809 4H25.494z"/>
  <image xlink:href="data:image/png;base64,{b64}" width="38" height="38" x="13" y="13" preserveAspectRatio="xMidYMid meet"/>
</svg>"""

# Dynamic SVG template (Gradient depends on image) - Used by GUI
SVG_TEMPLATE_DYNAMIC = """<!-- SquircleMasker -->
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="64" height="64">
  <defs>
    <linearGradient id="bg" x1="32" x2="32" y1="4" y2="60" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{color_top}"/>
      <stop offset="1" stop-color="{color_bottom}"/>
    </linearGradient>
  </defs>
  <path fill="url(#bg)" d="M20.26 4c-5.782 0-9.743 1.725-12.321 4.535C5.374 11.331 4 15.34 4 19.876v24.248c0 4.538 1.374 8.545 3.939 11.341C10.517 58.275 14.479 60 20.26 60h23.549c5.782 0 9.743-1.724 12.321-4.535C58.695 52.67 60 49.03 60 44.125V20.786c0-5.935-1.305-9.456-3.87-12.252C53.552 5.725 49.59 4 43.809 4H25.494z"/>
  <image xlink:href="data:image/png;base64,{b64}" width="42" height="42" x="11" y="11" preserveAspectRatio="xMidYMid meet"/>
</svg>"""

# List of apps to mask: { "icon-name-to-save": "original-image-path-or-app-name" }
APPS_TO_MASK = {
    # Flatpak apps or regular apps missing from the theme
    "com.usebottles.bottles": "com.usebottles.bottles",
    "rquickshare": "rquickshare",
    "net.cozic.RQuickShare": "net.cozic.RQuickShare", # RQuickShare name can be one of these two
    
    # Custom shortcut apps
    "coccoc-browser": "coccoc-browser",
    "com.coccoc.Browser": "coccoc-browser",
    "antigravity": "antigravity",
    "rog-control-center": "rog-control-center",
}
