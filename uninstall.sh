#!/usr/bin/env bash

APP_DIR="$HOME/.local/share/SquircleMasker"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "Đang gỡ cài đặt Squircle Masker..."

# 1. Xóa thư mục cài đặt
rm -rf "$APP_DIR"

# 2. Xóa các symlink lệnh
rm -f "$BIN_DIR/squircle-masker"
rm -f "$BIN_DIR/squircle-masker-cli"

# 3. Xóa file .desktop
rm -f "$DESKTOP_DIR/squircle-masker.desktop"

# Cập nhật cache ứng dụng
update-desktop-database "$DESKTOP_DIR" 2>/dev/null

echo "✅ Đã gỡ cài đặt thành công!"
