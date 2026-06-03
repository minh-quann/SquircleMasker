import os
import subprocess
import base64
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf
from threading import Thread

from .config import THEME_DIR, SVG_TEMPLATE_DYNAMIC
from .utils import find_original_icon, get_smart_colors, get_custom_bg_mode, set_custom_bg_mode
from . import i18n
from .i18n import t

# Default icon size for TreeView display
ICON_SIZE = 32

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
        
        self.set_default_size(700, 650)
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
        self.state_model.append([t("opt_cropped")])
        self.state_model.append([t("opt_original")])
        self.state_model.append([t("opt_custom")])
        
        # Setup ListStore for Background mode ComboBox options
        self.bg_model = Gtk.ListStore(str)
        self.bg_model.append([t("bg_white")])
        self.bg_model.append([t("bg_gray")])
        self.bg_model.append([t("bg_custom_color")])
        self.bg_model.append([t("bg_auto")])
        
        # ListStore: State(str), AppName(str), IconName(str), CustomPath(str), Pixbuf(GdkPixbuf), BgMode(str), CustomColor(str)
        self.liststore = Gtk.ListStore(str, str, str, str, GdkPixbuf.Pixbuf, str, str)
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
        
        # Image Column (uses pixbuf directly to avoid GTK icon theme cache issues)
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(t("icon_col"), renderer_pixbuf, pixbuf=4)
        treeview.append_column(column_pixbuf)
        
        # Text Column
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn(t("app_col"), renderer_text, text=1)
        treeview.append_column(column_text)
        
        # Background Mode Column (Combo) - only editable when state is "custom"
        renderer_bg_combo = Gtk.CellRendererCombo()
        renderer_bg_combo.set_property("model", self.bg_model)
        renderer_bg_combo.set_property("text-column", 0)
        renderer_bg_combo.set_property("has-entry", False)
        renderer_bg_combo.connect("edited", self.on_bg_combo_changed)
        
        column_bg = Gtk.TreeViewColumn(t("bg_col"), renderer_bg_combo, text=5)
        column_bg.set_cell_data_func(renderer_bg_combo, self.render_bg_combo)
        treeview.append_column(column_bg)

        scroll = Gtk.ScrolledWindow()
        scroll.add(treeview)
        vbox.pack_start(scroll, True, True, 0)
        
        # Status bar with spinner
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_box.set_halign(Gtk.Align.CENTER)
        
        self.spinner = Gtk.Spinner()
        status_box.pack_start(self.spinner, False, False, 0)
        
        self.status_label = Gtk.Label(label=t("loading"))
        status_box.pack_start(self.status_label, False, False, 0)
        
        vbox.pack_start(status_box, False, False, 0)
        
        self.load_apps()
        
    def render_combo_text(self, column, cell, model, iter, data):
        state_id = model[iter][0]
        text_map = {
            "theme": t("opt_theme"),
            "masked": t("opt_masked"),
            "cropped": t("opt_cropped"),
            "original": t("opt_original"),
            "custom": t("opt_custom")
        }
        cell.set_property("text", text_map.get(state_id, state_id))

    def render_bg_combo(self, column, cell, model, iter, data):
        """Render the background mode combo cell - only editable when state is custom."""
        state = model[iter][0]
        is_custom = (state == "custom")
        cell.set_property("editable", is_custom)
        cell.set_property("sensitive", is_custom)
        
        if is_custom:
            bg_mode = model[iter][5]
            bg_text_map = {
                "white": t("bg_white"),
                "gray": t("bg_gray"),
                "custom_color": t("bg_custom_color"),
                "auto": t("bg_auto"),
            }
            cell.set_property("text", bg_text_map.get(bg_mode, t("bg_white")))
        else:
            cell.set_property("text", "")

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
                if "<!-- SquircleMaskerCropped" in content:
                    return "cropped"
                if "<!-- SquircleMaskerCustom" in content:
                    return "custom"
                if "<!-- SquircleMasker" in content:
                    return "masked"
            return "theme"
        return "theme"
        
    def load_icon_pixbuf(self, icon_name):
        """Load an icon from GTK theme as a GdkPixbuf."""
        theme = Gtk.IconTheme.get_default()
        try:
            return theme.load_icon(icon_name, ICON_SIZE, Gtk.IconLookupFlags.FORCE_SIZE)
        except Exception:
            try:
                return theme.load_icon("application-x-executable", ICON_SIZE, Gtk.IconLookupFlags.FORCE_SIZE)
            except Exception:
                return None

    def load_icon_pixbuf_from_file(self, file_path):
        """Load an icon directly from a file path, bypassing GTK theme cache."""
        try:
            return GdkPixbuf.Pixbuf.new_from_file_at_size(file_path, ICON_SIZE, ICON_SIZE)
        except Exception:
            return None

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
                        
        from .utils import get_custom_icon_path
        for icon_id, info in sorted(apps_dict.items(), key=lambda x: x[1]['name']):
            custom_path = get_custom_icon_path(icon_id) or ""
            pixbuf = self.load_icon_pixbuf(info["icon"])
            # Load saved bg_mode for custom icons
            bg_mode, custom_color = get_custom_bg_mode(icon_id) if info["state"] == "custom" else ("white", None)
            self.liststore.append([info["state"], info["name"], info["icon"], custom_path, pixbuf, bg_mode, custom_color or ""])
            
        self.status_label.set_text(t("loaded", count=len(self.liststore)))

    def on_bg_combo_changed(self, widget, path, text):
        """Handle background mode change from the inline combo column."""
        bg_text_to_id = {
            t("bg_white"): "white",
            t("bg_gray"): "gray",
            t("bg_custom_color"): "custom_color",
            t("bg_auto"): "auto",
        }
        new_bg_mode = bg_text_to_id.get(text)
        if not new_bg_mode:
            return
        
        filter_iter = self.filter.get_iter(path)
        real_iter = self.filter.convert_iter_to_child_iter(filter_iter)
        
        # Only allow bg changes for custom state
        state = self.liststore[real_iter][0]
        if state != "custom":
            return
        
        app_name = self.liststore[real_iter][1]
        icon_name = self.liststore[real_iter][2]
        
        # If custom_color, show color chooser
        custom_color = None
        if new_bg_mode == "custom_color":
            color_dialog = Gtk.ColorChooserDialog(
                title=t("select_color"),
                parent=self
            )
            # Pre-select the previous custom color if available
            old_custom_color = self.liststore[real_iter][6]
            if old_custom_color:
                from gi.repository import Gdk
                rgba = Gdk.RGBA()
                rgba.parse(old_custom_color)
                color_dialog.set_rgba(rgba)
            
            color_response = color_dialog.run()
            if color_response == Gtk.ResponseType.OK:
                rgba = color_dialog.get_rgba()
                custom_color = "#{:02x}{:02x}{:02x}".format(
                    int(rgba.red * 255),
                    int(rgba.green * 255),
                    int(rgba.blue * 255)
                )
            else:
                color_dialog.destroy()
                return
            color_dialog.destroy()
        
        # Update ListStore
        self.liststore[real_iter][5] = new_bg_mode
        self.liststore[real_iter][6] = custom_color or ""
        
        # Save bg_mode to config
        set_custom_bg_mode(icon_name, new_bg_mode, custom_color)
        
        # Re-process the icon with the new background
        self.status_label.set_text(t("processing", app=app_name))
        self.spinner.start()
        
        thread = Thread(
            target=self.process_mask,
            args=(icon_name, "custom", real_iter),
            kwargs={"bg_mode": new_bg_mode, "custom_color": custom_color}
        )
        thread.daemon = True
        thread.start()

    def on_combo_changed(self, widget, path, text):
        text_to_id = {
            t("opt_theme"): "theme", 
            t("opt_masked"): "masked", 
            "cropped": "cropped", 
            t("opt_cropped"): "cropped", 
            t("opt_original"): "original",
            t("opt_custom"): "custom"
        }
        new_state = text_to_id.get(text)
        if not new_state: return
        
        filter_iter = self.filter.get_iter(path)
        real_iter = self.filter.convert_iter_to_child_iter(filter_iter)
        
        app_name = self.liststore[real_iter][1]
        icon_name = self.liststore[real_iter][2]
        old_state = self.liststore[real_iter][0]
        
        if new_state == "custom":
            # Step 1: Show background mode selection dialog
            bg_dialog = Gtk.Dialog(
                title=t("select_bg_mode"),
                parent=self,
                flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            )
            bg_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            bg_dialog.set_default_size(300, -1)
            
            content_area = bg_dialog.get_content_area()
            content_area.set_spacing(8)
            content_area.set_margin_start(12)
            content_area.set_margin_end(12)
            content_area.set_margin_top(12)
            content_area.set_margin_bottom(12)
            
            # Radio buttons for background mode
            bg_modes = [
                ("white", t("bg_white")),
                ("gray", t("bg_gray")),
                ("custom_color", t("bg_custom_color")),
                ("auto", t("bg_auto")),
            ]
            
            radios = []
            group = None
            for mode_id, mode_label in bg_modes:
                if group is None:
                    radio = Gtk.RadioButton.new_with_label(None, mode_label)
                    group = radio
                else:
                    radio = Gtk.RadioButton.new_with_label_from_widget(group, mode_label)
                radio._mode_id = mode_id
                radios.append(radio)
                content_area.pack_start(radio, False, False, 0)
            
            # Default to white
            radios[0].set_active(True)
            
            bg_dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
            bg_dialog.show_all()
            
            bg_response = bg_dialog.run()
            if bg_response != Gtk.ResponseType.OK:
                bg_dialog.destroy()
                self.liststore[real_iter][0] = old_state
                return
            
            # Get selected background mode
            selected_bg_mode = "white"
            for radio in radios:
                if radio.get_active():
                    selected_bg_mode = radio._mode_id
                    break
            bg_dialog.destroy()
            
            # Step 2: If custom_color, show color chooser
            custom_color = None
            if selected_bg_mode == "custom_color":
                color_dialog = Gtk.ColorChooserDialog(
                    title=t("select_color"),
                    parent=self
                )
                color_response = color_dialog.run()
                if color_response == Gtk.ResponseType.OK:
                    rgba = color_dialog.get_rgba()
                    custom_color = "#{:02x}{:02x}{:02x}".format(
                        int(rgba.red * 255),
                        int(rgba.green * 255),
                        int(rgba.blue * 255)
                    )
                else:
                    color_dialog.destroy()
                    self.liststore[real_iter][0] = old_state
                    return
                color_dialog.destroy()
            
            # Step 3: Open file chooser to select custom icon
            dialog = Gtk.FileChooserDialog(
                title=t("select_custom_icon"),
                parent=self,
                action=Gtk.FileChooserAction.OPEN
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            
            filter_image = Gtk.FileFilter()
            filter_image.set_name(t("image_files"))
            filter_image.add_mime_type("image/png")
            filter_image.add_mime_type("image/jpeg")
            filter_image.add_mime_type("image/svg+xml")
            filter_image.add_pattern("*.png")
            filter_image.add_pattern("*.jpg")
            filter_image.add_pattern("*.jpeg")
            filter_image.add_pattern("*.svg")
            dialog.add_filter(filter_image)
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                custom_path = dialog.get_filename()
                dialog.destroy()
                
                from .utils import set_custom_icon_path
                set_custom_icon_path(icon_name, custom_path)
                self.liststore[real_iter][3] = custom_path
                self.liststore[real_iter][0] = "custom"
                self.liststore[real_iter][5] = selected_bg_mode
                self.liststore[real_iter][6] = custom_color or ""
                
                # Save bg_mode to config
                set_custom_bg_mode(icon_name, selected_bg_mode, custom_color)
                
                self.status_label.set_text(t("processing", app=app_name))
                self.spinner.start()
                
                thread = Thread(
                    target=self.process_mask,
                    args=(icon_name, "custom", real_iter),
                    kwargs={"bg_mode": selected_bg_mode, "custom_color": custom_color}
                )
                thread.daemon = True
                thread.start()
            else:
                dialog.destroy()
                self.liststore[real_iter][0] = old_state
        else:
            if new_state == "original":
                from .utils import set_custom_icon_path
                set_custom_icon_path(icon_name, None)
                self.liststore[real_iter][3] = ""
                
            self.liststore[real_iter][0] = new_state
            self.status_label.set_text(t("processing", app=app_name))
            self.spinner.start()
            
            thread = Thread(target=self.process_mask, args=(icon_name, new_state, real_iter))
            thread.daemon = True
            thread.start()
        
    def sync_all_theme_icons(self, icon_name, state, svg_content=None, orig_path=None):
        base_dirs = [
            os.path.expanduser("~/.local/share/icons/MacTahoe"),
            os.path.expanduser("~/.local/share/icons/MacTahoe-dark")
        ]
        scalable_paths = {
            "light": os.path.expanduser(f"~/.local/share/icons/MacTahoe/apps/scalable/{icon_name}.svg"),
            "dark": os.path.expanduser(f"~/.local/share/icons/MacTahoe-dark/apps/scalable/{icon_name}.svg")
        }
        
        # 1. Backup scalable files if they are the original theme files
        for key, p in scalable_paths.items():
            bak_p = f"{p}.bak"
            if os.path.exists(p) and not os.path.islink(p):
                is_masked = False
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        header = f.read(100)
                    if "<!-- SquircleMasker" in header:
                        is_masked = True
                except Exception:
                    pass
                if not is_masked and not os.path.exists(bak_p):
                    os.rename(p, bak_p)

        # 2. Process scalable files based on state
        if state == "theme":
            for key, p in scalable_paths.items():
                bak_p = f"{p}.bak"
                if os.path.exists(p):
                    if os.path.islink(p):
                        os.remove(p)
                    else:
                        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                            header = f.read(100)
                        if "<!-- SquircleMasker" in header:
                            os.remove(p)
                if os.path.exists(bak_p):
                    os.rename(bak_p, p)
        elif state == "original" and orig_path:
            for key, p in scalable_paths.items():
                if os.path.exists(p):
                    os.remove(p)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                os.symlink(orig_path, p)
        else: # custom, masked, cropped
            if svg_content:
                for key, p in scalable_paths.items():
                    if os.path.exists(p):
                        os.remove(p)
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, "w") as f:
                        f.write(svg_content)

        # 3. Process extra directories (apps/22, categories/32, preferences/32 etc.)
        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                continue
            is_dark = "dark" in base_dir.lower()
            target_scalable = scalable_paths["dark"] if is_dark else scalable_paths["light"]
            
            for root, dirs, files in os.walk(base_dir):
                if "apps/scalable" in root:
                    continue
                for file in files:
                    if file in (f"{icon_name}.svg", f"{icon_name}.png"):
                        full_path = os.path.join(root, file)
                        bak_path = f"{full_path}.bak"
                        
                        if state == "theme":
                            # Restore original icon in extra folders
                            if os.path.islink(full_path):
                                os.remove(full_path)
                            elif os.path.exists(full_path):
                                try:
                                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        header = f.read(100)
                                    if "<!-- SquircleMasker" in header:
                                        os.remove(full_path)
                                except Exception:
                                    pass
                            if os.path.exists(bak_path):
                                os.rename(bak_path, full_path)
                        else:
                            # Backup and symlink to our modified scalable icon
                            if os.path.exists(full_path) and not os.path.islink(full_path):
                                is_masked = False
                                if file.endswith(".svg"):
                                    try:
                                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                            header = f.read(100)
                                        if "<!-- SquircleMasker" in header:
                                            is_masked = True
                                    except Exception:
                                        pass
                                if not is_masked and not os.path.exists(bak_path):
                                    os.rename(full_path, bak_path)
                                    
                            if os.path.exists(full_path):
                                os.remove(full_path)
                            try:
                                # Create absolute symlink pointing to the corresponding scalable SVG
                                os.symlink(target_scalable, full_path)
                            except Exception:
                                pass

    def process_mask(self, icon_name, state, real_iter, bg_mode="white", custom_color=None):
        out_path = os.path.join(THEME_DIR, f"{icon_name}.svg")
        
        if state == "theme":
            self.sync_all_theme_icons(icon_name, "theme")
            GLib.idle_add(self.update_status, t("restored_theme", icon=icon_name))
            
        elif state == "original":
            orig_path = find_original_icon(icon_name)
            if not orig_path:
                GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                return
            self.sync_all_theme_icons(icon_name, "original", orig_path=orig_path)
            GLib.idle_add(self.update_status, t("set_original", icon=icon_name))
                
        elif state == "custom":
            from .utils import get_custom_icon_path
            custom_path = get_custom_icon_path(icon_name)
            if not custom_path or not os.path.exists(custom_path):
                GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                GLib.idle_add(self.revert_combo, real_iter, "theme")
                return
            
            # Convert custom image to PNG and apply squircle mask
            cmd = ["magick", custom_path, "-background", "none", "-resize", "128x128", "png:-"]
            try:
                png_data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                b64 = base64.b64encode(png_data).decode('utf-8')
                
                # Determine background colors based on selected mode
                if bg_mode == "white":
                    color_top = "#ffffff"
                    color_bot = "#f0f0f0"
                elif bg_mode == "gray":
                    color_top = "#e0e0e0"
                    color_bot = "#c0c0c0"
                elif bg_mode == "custom_color" and custom_color:
                    # Use the user-selected color with a slightly darker bottom
                    color_top = custom_color
                    # Darken the bottom color by ~10%
                    r = int(custom_color[1:3], 16)
                    g = int(custom_color[3:5], 16)
                    b_val = int(custom_color[5:7], 16)
                    color_bot = "#{:02x}{:02x}{:02x}".format(
                        max(0, int(r * 0.9)),
                        max(0, int(g * 0.9)),
                        max(0, int(b_val * 0.9))
                    )
                elif bg_mode == "auto":
                    # Auto-detect colors from the icon image
                    color_top, color_bot = get_smart_colors(png_data)
                else:
                    # Fallback to white
                    color_top = "#ffffff"
                    color_bot = "#f0f0f0"
                
                svg_content = SVG_TEMPLATE_DYNAMIC.replace("{b64}", b64).replace("{color_top}", color_top).replace("{color_bottom}", color_bot)
                # Replace the standard marker with the custom marker
                svg_content = svg_content.replace("<!-- SquircleMasker -->", "<!-- SquircleMaskerCustom -->")
                if "<!-- SquircleMaskerCustom" not in svg_content:
                    svg_content = "<!-- SquircleMaskerCustom -->\n" + svg_content
                    
                self.sync_all_theme_icons(icon_name, "custom", svg_content=svg_content)
                GLib.idle_add(self.update_status, t("set_custom", icon=icon_name))
            except Exception as e:
                GLib.idle_add(self.update_status, t("err_convert", icon=icon_name))
                GLib.idle_add(self.revert_combo, real_iter, "theme")
                return
                
        elif state == "masked":
            from .utils import get_custom_icon_path
            orig_path = get_custom_icon_path(icon_name) or find_original_icon(icon_name)
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
                    
                self.sync_all_theme_icons(icon_name, "masked", svg_content=svg_content)
                GLib.idle_add(self.update_status, t("masked", icon=icon_name))
            except Exception as e:
                GLib.idle_add(self.update_status, t("err_convert", icon=icon_name))
                GLib.idle_add(self.revert_combo, real_iter, "theme")
                return
 
        elif state == "cropped":
            from .utils import get_custom_icon_path
            orig_path = get_custom_icon_path(icon_name) or find_original_icon(icon_name)
            if not orig_path:
                GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                GLib.idle_add(self.revert_combo, real_iter, "theme")
                return
                
            cmd = [
                "magick", orig_path, "-background", "none", "-resize", "128x128!",
                "(", "-size", "128x128", "xc:none", "-fill", "white", "-draw", "circle 64,64 64,0", ")",
                "-compose", "DstIn", "-composite", "png:-"
            ]
            try:
                # Execute magick to crop icon into circle shape
                png_data = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                b64 = base64.b64encode(png_data).decode('utf-8')
                
                color_top, color_bot = get_smart_colors(png_data)
                    
                svg_content = f"""<!-- SquircleMaskerCropped -->
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="128" height="128">
  <defs>
    <linearGradient id="bg" x1="64" x2="64" y1="0" y2="128" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{color_top}"/>
      <stop offset="1" stop-color="{color_bot}"/>
    </linearGradient>
  </defs>
  <circle cx="64" cy="64" r="64" fill="url(#bg)"/>
  <image xlink:href="data:image/png;base64,{b64}" width="96" height="96" x="16" y="16" preserveAspectRatio="xMidYMid meet"/>
</svg>"""
                    
                self.sync_all_theme_icons(icon_name, "cropped", svg_content=svg_content)
                GLib.idle_add(self.update_status, t("mask_cropped", icon=icon_name))
            except Exception as e:
                GLib.idle_add(self.update_status, t("err_convert", icon=icon_name))
                GLib.idle_add(self.revert_combo, real_iter, "theme")
                return

        # Refresh GNOME icon cache for both MacTahoe and MacTahoe-dark
        GLib.idle_add(self.update_status, t("refreshing_cache"))
        subprocess.run("gtk-update-icon-cache -f -t ~/.local/share/icons/MacTahoe-dark/ 2>/dev/null", shell=True)
        subprocess.run("gtk-update-icon-cache -f -t ~/.local/share/icons/MacTahoe/ 2>/dev/null", shell=True)
        subprocess.run("touch ~/.local/share/icons", shell=True)
        subprocess.run("touch ~/.local/share/applications", shell=True)
        subprocess.run("update-desktop-database ~/.local/share/applications/ 2>/dev/null", shell=True)
        
        # Toggle Dash to Dock extension to force icon cache refresh
        # (GNOME 50+ disables Shell.Eval, this is the only reliable method)
        import time
        try:
            # Get list of enabled dock extensions to toggle
            result = subprocess.check_output(
                "gnome-extensions list --enabled 2>/dev/null",
                shell=True, text=True
            ).strip()
            dock_extensions = [ext for ext in result.split('\n') 
                             if 'dock' in ext.lower() or 'dash' in ext.lower()]
            for ext in dock_extensions:
                subprocess.run(f"gnome-extensions disable {ext}",
                    shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            if dock_extensions:
                time.sleep(0.5)
            for ext in dock_extensions:
                subprocess.run(f"gnome-extensions enable {ext}",
                    shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception:
            pass
        
        GLib.idle_add(self.on_process_done, real_iter)
        
    def update_status(self, msg):
        self.status_label.set_text(msg)
    
    def on_process_done(self, real_iter=None):
        """Stop spinner, rescan icon theme, and reload pixbuf for the changed icon."""
        self.spinner.stop()
        
        # Reload the pixbuf directly from the output SVG file (bypass GTK theme cache)
        if real_iter is not None:
            try:
                icon_name = self.liststore[real_iter][2]
                out_path = os.path.join(THEME_DIR, f"{icon_name}.svg")
                new_pixbuf = None
                if os.path.exists(out_path) and not os.path.islink(out_path):
                    # Load directly from the generated file
                    new_pixbuf = self.load_icon_pixbuf_from_file(out_path)
                if not new_pixbuf:
                    # Fallback to theme lookup (for theme/original states)
                    theme = Gtk.IconTheme.get_default()
                    theme.rescan_if_needed()
                    new_pixbuf = self.load_icon_pixbuf(icon_name)
                if new_pixbuf:
                    self.liststore[real_iter][4] = new_pixbuf
            except Exception:
                pass
        
        self.status_label.set_text(t("refresh_done"))
        
    def revert_combo(self, real_iter, val):
        self.liststore[real_iter][0] = val
        self.spinner.stop()

def run_gui():
    win = SquircleApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    run_gui()
