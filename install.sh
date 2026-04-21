#!/usr/bin/env bash

APP_DIR="$HOME/.local/share/SquircleMasker"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Đang cài đặt Squircle Masker..."

# 1. Tạo thư mục
mkdir -p "$APP_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# 2. Copy source code vào thư mục hệ thống của user
cp -r src SquircleMasker.py mask_icons.py "$APP_DIR/"
chmod +x "$APP_DIR/SquircleMasker.py"
chmod +x "$APP_DIR/mask_icons.py"

# 3. Tạo symlink để có thể gõ lệnh trực tiếp trong terminal
ln -sf "$APP_DIR/SquircleMasker.py" "$BIN_DIR/squircle-masker"
ln -sf "$APP_DIR/mask_icons.py" "$BIN_DIR/squircle-masker-cli"

# 4. Tạo file .desktop để hiển thị trong Menu ứng dụng
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

# Cập nhật cache ứng dụng
update-desktop-database "$DESKTOP_DIR" 2>/dev/null

echo "✅ Cài đặt thành công!"
echo "👉 Bạn có thể mở 'Squircle Masker' từ Menu ứng dụng (App Launcher)."
echo "👉 Hoặc gõ lệnh 'squircle-masker' / 'squircle-masker-cli' trong terminal."
