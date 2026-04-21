#!/usr/bin/env bash

APP_DIR="$HOME/.local/share/SquircleMasker"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Installing Squircle Masker..."

# 1. Create directories (remove old directory if exists for a clean install)
# Kill app if running to avoid update errors
pkill -9 -f "SquircleMasker.py" || true
pkill -9 -f "squircle-masker" || true
sleep 0.5
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# 2. Copy source code to user system directory
cp -r src SquircleMasker.py mask_icons.py "$APP_DIR/"
chmod +x "$APP_DIR/SquircleMasker.py"
chmod +x "$APP_DIR/mask_icons.py"

# 3. Create symlink to enable direct terminal command execution
ln -sf "$APP_DIR/SquircleMasker.py" "$BIN_DIR/squircle-masker"
ln -sf "$APP_DIR/mask_icons.py" "$BIN_DIR/squircle-masker-cli"

# 4. Create .desktop file for App Menu visibility
cat <<EOF > "$DESKTOP_DIR/squircle-masker.desktop"
[Desktop Entry]
Version=1.0
Name=Squircle Masker
Comment=Apply macOS-style squircle masks to icons
Exec=$APP_DIR/SquircleMasker.py
Icon=preferences-desktop-theme
Terminal=false
Type=Application
Categories=Utility;Settings;
EOF

chmod +x "$DESKTOP_DIR/squircle-masker.desktop"

# Update application cache
update-desktop-database "$DESKTOP_DIR" 2>/dev/null

echo "Installation successful!"
echo "You can open 'Squircle Masker' from the App Launcher."
echo "Or run 'squircle-masker' / 'squircle-masker-cli' in the terminal."
