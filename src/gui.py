import os
import subprocess
import base64
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from threading import Thread

from .config import THEME_DIR, SVG_TEMPLATE_DYNAMIC
from .utils import find_original_icon, get_smart_colors
from . import i18n
from .i18n import t

class SquircleApp(Gtk.Window):
    def __init__(self):
        super().__init__()
        
        # Create HeaderBar
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = t("title")
        self.set_titlebar(hb)
        
        # Language Selector in HeaderBar
        self.lang_combo = Gtk.ComboBoxText()
        self.lang_combo.append("vi", "VN")
        self.lang_combo.append("en", "EN")
        self.lang_combo.set_active_id(i18n.CURRENT_LANG)
        self.lang_combo.connect("changed", self.on_language_changed)
        hb.pack_end(self.lang_combo)
        
        self.set_default_size(550, 650)
        self.set_border_width(10)
        
        if not os.path.exists(THEME_DIR):
            os.makedirs(THEME_DIR, exist_ok=True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        lbl = Gtk.Label(label=t("description"))
        lbl.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(lbl, False, False, 0)
        
        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect("search-changed", self.on_search_changed)
        vbox.pack_start(self.search_entry, False, False, 0)
        
        # Setup ListStore for ComboBox options (1 column to fix GTK bug)
        self.state_model = Gtk.ListStore(str)
        self.state_model.append([t("opt_theme")])
        self.state_model.append([t("opt_masked")])
        self.state_model.append([t("opt_original")])
        
        # ListStore: State(str), AppName(str), IconName(str), OriginalPath(str)
        self.liststore = Gtk.ListStore(str, str, str, str)
        self.filter = self.liststore.filter_new()
        self.filter.set_visible_func(self.filter_func)
        
        treeview = Gtk.TreeView(model=self.filter)
        treeview.set_enable_search(False) # Prevent interactive search box from overriding dropdown
        treeview.set_enable_search(False) # Disable default GTK treeview search to prevent popup bugs
        
        # State Column (Combo)
        renderer_combo = Gtk.CellRendererCombo()
        renderer_combo.set_property("model", self.state_model)
        renderer_combo.set_property("text-column", 0)
        renderer_combo.set_property("has-entry", False)
        renderer_combo.set_property("editable", True)
        renderer_combo.connect("edited", self.on_combo_changed)
        
        column_combo = Gtk.TreeViewColumn(t("mask_col"), renderer_combo, text=0)
        column_combo.set_cell_data_func(renderer_combo, self.render_combo_text)
        treeview.append_column(column_combo)
        
        # Image Column
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_pixbuf.set_property("stock-size", Gtk.IconSize.DND)
        column_pixbuf = Gtk.TreeViewColumn(t("icon_col"), renderer_pixbuf, icon_name=2)
        treeview.append_column(column_pixbuf)
        
        # Text Column
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn(t("app_col"), renderer_text, text=1)
        treeview.append_column(column_text)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        vbox.pack_start(scroll, True, True, 0)
        
        self.status_label = Gtk.Label(label=t("loading"))
        vbox.pack_start(self.status_label, False, False, 0)
        
        self.load_apps()
        
    def render_combo_text(self, column, cell, model, iter, data):
        state_id = model[iter][0]
        text_map = {"theme": t("opt_theme"), "masked": t("opt_masked"), "original": t("opt_original")}
        cell.set_property("text", text_map.get(state_id, state_id))

    def filter_func(self, model, iter, data):
        query = self.search_entry.get_text().lower()
        if not query:
            return True
        name = model[iter][1].lower()
        icon = model[iter][2].lower()
        return query in name or query in icon
        
    def on_language_changed(self, combo):
        lang = combo.get_active_id()
        if lang and lang != i18n.CURRENT_LANG:
            i18n.set_lang(lang)
            self.destroy()
            # Start a new instance to refresh UI
            new_win = SquircleApp()
            new_win.connect("destroy", Gtk.main_quit)
            new_win.show_all()

    def on_search_changed(self, entry):
        self.filter.refilter()
        
    def get_icon_state(self, icon_name):
        out_path = os.path.join(THEME_DIR, f"{icon_name}.svg")
        if os.path.islink(out_path):
            target = os.readlink(out_path)
            if os.path.isabs(target):
                return "original"
            else:
                return "theme"
        if os.path.exists(out_path):
            with open(out_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(100)
                if "<!-- SquircleMasker" in content:
                    return "masked"
            return "theme"
        return "theme"
        
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
                    if icon.startswith("/") and "Pictures" in icon:
                        pass
                    
                    icon_id = os.path.basename(icon).split('.')[0] if icon.startswith("/") else icon
                    
                    if icon_id not in apps_dict:
                        state = self.get_icon_state(icon_id)
                        apps_dict[icon_id] = {"name": name, "icon": icon_id, "state": state}
                        
        for icon_id, info in sorted(apps_dict.items(), key=lambda x: x[1]['name']):
            self.liststore.append([info["state"], info["name"], info["icon"], ""])
            
        self.status_label.set_text(t("loaded", count=len(self.liststore)))

    def on_combo_changed(self, widget, path, text):
        text_to_id = {t("opt_theme"): "theme", t("opt_masked"): "masked", t("opt_original"): "original"}
        new_state = text_to_id.get(text)
        if not new_state: return
        
        filter_iter = self.filter.get_iter(path)
        real_iter = self.filter.convert_iter_to_child_iter(filter_iter)
        
        app_name = self.liststore[real_iter][1]
        icon_name = self.liststore[real_iter][2]
        
        self.liststore[real_iter][0] = new_state
        self.status_label.set_text(t("processing", app=app_name))
        
        thread = Thread(target=self.process_mask, args=(icon_name, new_state, real_iter))
        thread.daemon = True
        thread.start()
        
    def process_mask(self, icon_name, state, real_iter):
        out_path = os.path.join(THEME_DIR, f"{icon_name}.svg")
        bak_path = os.path.join(THEME_DIR, f"{icon_name}.svg.bak")
        
        def backup_theme_icon():
            if os.path.exists(out_path):
                if os.path.islink(out_path):
                    target = os.readlink(out_path)
                    if not os.path.isabs(target): # Theme symlink
                        os.rename(out_path, bak_path)
                else:
                    with open(out_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(100)
                    if "<!-- SquircleMasker" not in content:
                        os.rename(out_path, bak_path)
                        
        if state == "theme":
            if os.path.exists(out_path):
                if os.path.islink(out_path):
                    if os.path.isabs(os.readlink(out_path)):
                        os.remove(out_path)
                else:
                    with open(out_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(100)
                    if "<!-- SquircleMasker" in content:
                        os.remove(out_path)
                        
            if os.path.exists(bak_path):
                os.rename(bak_path, out_path)
            GLib.idle_add(self.update_status, t("restored_theme", icon=icon_name))
            
        elif state == "original":
            backup_theme_icon()
            orig_path = find_original_icon(icon_name)
            if not orig_path:
                if os.path.exists(out_path): os.remove(out_path)
                GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                return
            if os.path.exists(out_path):
                os.remove(out_path)
            try:
                os.symlink(orig_path, out_path)
                GLib.idle_add(self.update_status, t("set_original", icon=icon_name))
            except Exception as e:
                GLib.idle_add(self.update_status, f"Error symlink: {e}")
                
        elif state == "masked":
            backup_theme_icon()
            orig_path = find_original_icon(icon_name)
            if not orig_path:
                GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                # Revert combo state on error
                GLib.idle_add(self.revert_combo, real_iter, "theme")
                return
                
            cmd = ["magick", orig_path, "-background", "none", "-resize", "128x128", "png:-"]
            try:
                png_data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                b64 = base64.b64encode(png_data).decode('utf-8')
                
                color_top, color_bot = get_smart_colors(png_data)
                
                svg_content = SVG_TEMPLATE_DYNAMIC.replace("{b64}", b64).replace("{color_top}", color_top).replace("{color_bottom}", color_bot)
                if "<!-- SquircleMasker" not in svg_content:
                    svg_content = "<!-- SquircleMasker -->\n" + svg_content
                    
                if os.path.exists(out_path):
                    os.remove(out_path)
                with open(out_path, "w") as f:
                    f.write(svg_content)
                GLib.idle_add(self.update_status, t("masked", icon=icon_name))
            except Exception as e:
                GLib.idle_add(self.update_status, t("err_convert", icon=icon_name))
                GLib.idle_add(self.revert_combo, real_iter, "theme")
                return

        subprocess.run("gtk-update-icon-cache ~/.local/share/icons/MacTahoe-dark/ 2>/dev/null", shell=True)
        
    def update_status(self, msg):
        self.status_label.set_text(msg)
        
    def revert_combo(self, real_iter, val):
        self.liststore[real_iter][0] = val

def run_gui():
    win = SquircleApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    run_gui()
