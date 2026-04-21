import os
import subprocess
import base64
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from threading import Thread

from .config import THEME_DIR, SVG_TEMPLATE_DYNAMIC
from .utils import find_original_icon, get_smart_colors

class SquircleApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Squircle Icon Masker")
        self.set_default_size(500, 600)
        self.set_border_width(10)
        
        if not os.path.exists(THEME_DIR):
            os.makedirs(THEME_DIR, exist_ok=True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        lbl = Gtk.Label(label="Select applications to mask (Squircle)\\nEnable (Check) = macOS frame | Disable = Original icon")
        lbl.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(lbl, False, False, 0)
        
        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect("search-changed", self.on_search_changed)
        vbox.pack_start(self.search_entry, False, False, 0)
        
        # ListStore: Masked(bool), AppName(str), IconName(str), OriginalPath(str)
        self.liststore = Gtk.ListStore(bool, str, str, str)
        self.filter = self.liststore.filter_new()
        self.filter.set_visible_func(self.filter_func)
        
        treeview = Gtk.TreeView(model=self.filter)
        
        # Toggle Column
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = Gtk.TreeViewColumn("Mask", renderer_toggle, active=0)
        treeview.append_column(column_toggle)
        
        # Image Column
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_pixbuf.set_property("stock-size", Gtk.IconSize.DND)
        column_pixbuf = Gtk.TreeViewColumn("Icon", renderer_pixbuf, icon_name=2)
        treeview.append_column(column_pixbuf)
        
        # Text Column
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Application", renderer_text, text=1)
        treeview.append_column(column_text)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        vbox.pack_start(scroll, True, True, 0)
        
        self.status_label = Gtk.Label(label="Loading list...")
        vbox.pack_start(self.status_label, False, False, 0)
        
        self.load_apps()
        
    def filter_func(self, model, iter, data):
        query = self.search_entry.get_text().lower()
        if not query:
            return True
        name = model[iter][1].lower()
        icon = model[iter][2].lower()
        return query in name or query in icon

    def on_search_changed(self, entry):
        self.filter.refilter()
        
    def load_apps(self):
        apps_dict = {}
        dirs = [
            "/usr/share/applications", 
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
            "/var/lib/snapd/desktop/applications"
        ]
        for d in dirs:
            if not os.path.exists(d): continue
            for f in os.listdir(d):
                if not f.endswith(".desktop"): continue
                path = os.path.join(d, f)
                name = None
                icon = None
                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    for line in file:
                        if line.startswith("Name=") and not name:
                            name = line.strip().split("=", 1)[1]
                        if line.startswith("Icon=") and not icon:
                            icon = line.strip().split("=", 1)[1]
                if name and icon:
                    # Ignore absolute path icons from picture
                    if icon.startswith("/") and "Pictures" in icon:
                        # Fix the .desktop on the fly
                        pass
                    
                    # Ensure icon name is just the name if it's absolute but we want to map it
                    icon_id = os.path.basename(icon).split('.')[0] if icon.startswith("/") else icon
                    
                    if icon_id not in apps_dict:
                        masked_path = os.path.join(THEME_DIR, f"{icon_id}.svg")
                        is_masked = os.path.exists(masked_path)
                        apps_dict[icon_id] = {"name": name, "icon": icon_id, "masked": is_masked}
                        
        for icon_id, info in sorted(apps_dict.items(), key=lambda x: x[1]['name']):
            self.liststore.append([info["masked"], info["name"], info["icon"], ""])
            
        self.status_label.set_text(f"Loaded {len(self.liststore)} applications.")

    def on_cell_toggled(self, widget, path):
        # path is relative to the filter, we need to convert it to liststore iter
        filter_iter = self.filter.get_iter(path)
        real_iter = self.filter.convert_iter_to_child_iter(filter_iter)
        
        current_val = self.liststore[real_iter][0]
        new_val = not current_val
        app_name = self.liststore[real_iter][1]
        icon_name = self.liststore[real_iter][2]
        
        self.liststore[real_iter][0] = new_val
        
        self.status_label.set_text(f"Processing {app_name}...")
        
        # Run process in background to not freeze GUI
        thread = Thread(target=self.process_mask, args=(icon_name, new_val, real_iter))
        thread.daemon = True
        thread.start()
        
    def process_mask(self, icon_name, mask, real_iter):
        out_path = os.path.join(THEME_DIR, f"{icon_name}.svg")
        
        if not mask:
            # Unmask
            if os.path.exists(out_path):
                os.remove(out_path)
            GLib.idle_add(self.update_status, f"Unmasked {icon_name}")
        else:
            # Mask
            orig_path = find_original_icon(icon_name)
            if not orig_path:
                GLib.idle_add(self.update_status, f"Error: Original image not found for {icon_name}")
                GLib.idle_add(self.revert_toggle, real_iter, False)
                return
                
            cmd = ["magick", orig_path, "-background", "none", "-resize", "128x128", "png:-"]
            try:
                png_data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                b64 = base64.b64encode(png_data).decode('utf-8')
                
                # Calculate smart background color
                color_top, color_bot = get_smart_colors(png_data)
                
                svg_content = SVG_TEMPLATE_DYNAMIC.replace("{b64}", b64).replace("{color_top}", color_top).replace("{color_bottom}", color_bot)
                with open(out_path, "w") as f:
                    f.write(svg_content)
                GLib.idle_add(self.update_status, f"Masked {icon_name}")
            except Exception as e:
                GLib.idle_add(self.update_status, f"Error: conversion failed for {icon_name}")
                GLib.idle_add(self.revert_toggle, real_iter, False)
                return

        # Update cache
        subprocess.run("gtk-update-icon-cache ~/.local/share/icons/MacTahoe-dark/ 2>/dev/null", shell=True)
        
    def update_status(self, msg):
        self.status_label.set_text(msg)
        
    def revert_toggle(self, real_iter, val):
        self.liststore[real_iter][0] = val

def run_gui():
    win = SquircleApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    run_gui()
