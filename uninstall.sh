#!/usr/bin/env bash

APP_DIR="$HOME/.local/share/SquircleMasker"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Uninstalling Squircle Masker..."

# 1. Remove app directory
rm -rf "$APP_DIR"

# 2. Remove binary symlinks
rm -f "$BIN_DIR/squircle-masker"
rm -f "$BIN_DIR/squircle-masker-cli"

# 3. Remove .desktop file
rm -f "$DESKTOP_DIR/squircle-masker.desktop"

# Update application cache
update-desktop-database "$DESKTOP_DIR" 2>/dev/null

echo "Uninstallation successful!"
