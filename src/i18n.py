import os

import os
import json

CONFIG_FILE = os.path.expanduser("~/.config/squircle_masker_lang.json")

def get_saved_lang():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("lang")
        except Exception:
            pass
    return None

def set_lang(lang_code):
    global CURRENT_LANG
    CURRENT_LANG = lang_code
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"lang": lang_code}, f)
    except Exception:
        pass

# Detect system language or default to English
_sys_lang = os.environ.get('LANG', 'en').split('_')[0]
CURRENT_LANG = get_saved_lang() or (_sys_lang if _sys_lang in ['en', 'vi'] else 'en')

LOCALES = {
    "en": {
        "title": "Squircle Icon Masker v1.1",
        "description": "Select applications to mask (Squircle)\\nEnable (Check) = macOS frame | Disable = Original icon",
        "mask_col": "Mask",
        "icon_col": "Icon",
        "app_col": "Application",
        "bg_col": "Background",
        "loading": "Loading list...",
        "loaded": "Loaded {count} applications.",
        "processing": "Processing {app}...",
        "unmasked": "Unmasked {icon}",
        "masked": "Masked {icon}",
        "restored_theme": "Restored theme icon: {icon}",
        "set_original": "Set to original icon: {icon}",
        "mask_cropped": "Cropped icon to circle: {icon}",
        "opt_theme": "From Theme",
        "opt_masked": "Auto Squircle",
        "opt_cropped": "Cropped Circle",
        "opt_original": "Original",
        "opt_custom": "Custom Icon",
        "select_custom_icon": "Select Custom Icon",
        "select_bg_mode": "Select Background Mode",
        "bg_white": "White Background",
        "bg_gray": "Gray Background",
        "bg_custom_color": "Custom Color",
        "bg_auto": "Auto",
        "select_color": "Select Background Color",
        "image_files": "Image files",
        "set_custom": "Set to custom icon: {icon}",
        "err_not_found": "Error: Original image not found for {icon}",
        "err_convert": "Error: conversion failed for {icon}",
        "err_theme_not_found": "Error: Theme directory not found {theme_dir}",
        "fixing_desktop": "Fixing .desktop files with absolute paths...",
        "fixed_icon": " -> Fixed Icon in {file}",
        "masking_app": "Masking: {app}...",
        "skip_not_found": "  -> Original image not found for {app}, skipping.",
        "skip_err_convert": "  -> Error converting image with ImageMagick, skipping.",
        "success_create": "  -> Successfully created: {app}.svg",
        "reloading_cache": "\nReloading icon cache...",
        "refreshing_cache": "Refreshing icon cache...",
        "refresh_done": "Done! Cache refreshed.",
        "done_msg": "Done! Please press Alt+F2, type 'r' and Enter (if on X11) or restart your machine to see changes."
    },
    "vi": {
        "title": "Squircle Icon Masker v1.2.1",
        "description": "Chọn ứng dụng để bọc viền (Squircle)\nBật (Tích) = Bọc khung macOS | Tắt = Trả về icon gốc",
        "mask_col": "Bọc khung",
        "icon_col": "Icon",
        "app_col": "Ứng dụng",
        "bg_col": "Nền",
        "loading": "Đang tải danh sách...",
        "loaded": "Đã tải {count} ứng dụng.",
        "processing": "Đang xử lý {app}...",
        "unmasked": "Đã tháo khung cho {icon}",
        "masked": "Đã bọc khung cho {icon}",
        "restored_theme": "Đã khôi phục icon theme: {icon}",
        "set_original": "Đã đặt về icon gốc: {icon}",
        "mask_cropped": "Đã cắt icon thành hình tròn: {icon}",
        "opt_theme": "Từ Theme",
        "opt_masked": "Tự Bo",
        "opt_cropped": "Cắt Tròn",
        "opt_original": "Mặc Định",
        "opt_custom": "Tùy Chỉnh",
        "select_custom_icon": "Chọn Icon Tùy Chỉnh",
        "select_bg_mode": "Chọn Kiểu Nền",
        "bg_white": "Nền Trắng",
        "bg_gray": "Nền Xám",
        "bg_custom_color": "Nền Tự Chọn Màu",
        "bg_auto": "Tự Động",
        "select_color": "Chọn Màu Nền",
        "image_files": "Tệp hình ảnh",
        "set_custom": "Đã đặt về icon tùy chỉnh: {icon}",
        "err_not_found": "Lỗi: Không tìm thấy ảnh gốc của {icon}",
        "err_convert": "Lỗi: convert thất bại cho {icon}",
        "err_theme_not_found": "Lỗi: Không tìm thấy thư mục theme {theme_dir}",
        "fixing_desktop": "Đang sửa các file .desktop dùng đường dẫn tuyệt đối...",
        "fixed_icon": " -> Đã sửa Icon trong {file}",
        "masking_app": "Đang bọc khung cho: {app}...",
        "skip_not_found": "  -> Không tìm thấy ảnh gốc cho {app}, bỏ qua.",
        "skip_err_convert": "  -> Lỗi khi convert ảnh bằng ImageMagick, bỏ qua.",
        "success_create": "  -> Đã tạo thành công: {app}.svg",
        "reloading_cache": "\nĐang tải lại icon cache...",
        "refreshing_cache": "Đang tải lại icon cache...",
        "refresh_done": "Hoàn tất! Đã tải lại cache.",
        "done_msg": "Hoàn tất! Vui lòng nhấn Alt+F2, gõ 'r' và Enter (nếu dùng X11) hoặc khởi động lại máy để thấy sự thay đổi."
    }
}

def t(key, **kwargs):
    # Use English as fallback if language is not supported
    lang = CURRENT_LANG if CURRENT_LANG in LOCALES else "en"
    text = LOCALES[lang].get(key, LOCALES["en"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text
