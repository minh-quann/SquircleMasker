"""GTK 3 GUI application for SquircleMasker."""

import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf
from threading import Thread

from ..config.settings import THEME_DIR
from ..core.storage import (
    get_custom_icon_path, set_custom_icon_path,
    get_custom_bg_mode, set_custom_bg_mode
)
from ..core.resolver import find_original_icon
from ..core.processor import generate_masked_svg, generate_cropped_svg, generate_custom_svg
from ..core.sync import sync_all_theme_icons, refresh_icon_cache
from ..config import i18n
from ..config.i18n import t

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

        # ListStore: State(str), AppName(str), IconName(str), CustomPath(str),
        #            Pixbuf(GdkPixbuf), BgMode(str), CustomColor(str), Selected(bool)
        self.liststore = Gtk.ListStore(str, str, str, str, GdkPixbuf.Pixbuf, str, str, bool)
        self.filter = self.liststore.filter_new()
        self.filter.set_visible_func(self.filter_func)

        treeview = Gtk.TreeView(model=self.filter)
        treeview.set_enable_search(False)  # Disable default GTK treeview search to prevent popup bugs
        treeview.connect("row-activated", self.on_row_activated)
        self.treeview = treeview

        # Checkbox Column
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = Gtk.TreeViewColumn("", renderer_toggle, active=7)
        treeview.append_column(column_toggle)

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

        # Batch Action Bar
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_margin_start(5)
        action_box.set_margin_end(5)

        btn_select_all = Gtk.Button(label=t("select_all"))
        btn_select_all.connect("clicked", self.on_select_all)
        action_box.pack_start(btn_select_all, False, False, 0)

        btn_deselect_all = Gtk.Button(label=t("deselect_all"))
        btn_deselect_all.connect("clicked", self.on_deselect_all)
        action_box.pack_start(btn_deselect_all, False, False, 0)

        action_box.pack_start(Gtk.Label(label="  " + t("apply_selected")), False, False, 0)

        self.batch_combo = Gtk.ComboBoxText()
        self.batch_combo.append("theme", t("opt_theme"))
        self.batch_combo.append("masked", t("opt_masked"))
        self.batch_combo.append("cropped", t("opt_cropped"))
        self.batch_combo.append("original", t("opt_original"))
        self.batch_combo.append("custom", t("opt_custom"))
        self.batch_combo.set_active(0)
        action_box.pack_start(self.batch_combo, False, False, 0)

        btn_apply = Gtk.Button(label=t("apply"))
        btn_apply.connect("clicked", self.on_batch_apply)
        action_box.pack_start(btn_apply, False, False, 0)

        btn_upload = Gtk.Button(label=t("upload_custom_icon"))
        btn_upload.connect("clicked", self.on_upload_custom_clicked)
        action_box.pack_start(btn_upload, False, False, 0)

        btn_change_bg = Gtk.Button(label=t("change_bg"))
        btn_change_bg.connect("clicked", self.on_change_bg_clicked)
        action_box.pack_start(btn_change_bg, False, False, 0)

        vbox.pack_start(action_box, False, False, 0)

        # Status bar with spinner
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_box.set_halign(Gtk.Align.CENTER)

        self.spinner = Gtk.Spinner()
        status_box.pack_start(self.spinner, False, False, 0)

        self.status_label = Gtk.Label(label=t("loading"))
        status_box.pack_start(self.status_label, False, False, 0)

        vbox.pack_start(status_box, False, False, 0)

        self.load_apps()

    # ── Cell Renderers ──────────────────────────────────────────────

    def render_combo_text(self, column, cell, model, iter, data):
        """Render translated text for the state combo column."""
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
        """Render the background mode combo cell - editable for all icon states."""
        cell.set_property("editable", True)
        cell.set_property("sensitive", True)

        bg_mode = model[iter][5] or "white"
        bg_text_map = {
            "white": t("bg_white"),
            "gray": t("bg_gray"),
            "custom_color": t("bg_custom_color"),
            "auto": t("bg_auto"),
        }
        cell.set_property("text", bg_text_map.get(bg_mode, t("bg_white")))

    # ── Checkbox & Batch Handlers ───────────────────────────────────

    def on_cell_toggled(self, widget, path):
        """Toggle checkbox selection for a single row."""
        filter_iter = self.filter.get_iter(path)
        real_iter = self.filter.convert_iter_to_child_iter(filter_iter)
        self.liststore[real_iter][7] = not self.liststore[real_iter][7]

    def on_select_all(self, widget):
        """Select all rows."""
        for row in self.liststore:
            row[7] = True

    def on_deselect_all(self, widget):
        """Deselect all rows."""
        for row in self.liststore:
            row[7] = False

    def on_row_activated(self, treeview, path, column):
        """Handle double click on a row to upload/change custom icon image."""
        filter_iter = self.filter.get_iter(path)
        real_iter = self.filter.convert_iter_to_child_iter(filter_iter)
        app_name = self.liststore[real_iter][1]
        icon_name = self.liststore[real_iter][2]
        old_state = self.liststore[real_iter][0]
        self._handle_custom_icon_selection(real_iter, app_name, icon_name, old_state)

    def on_upload_custom_clicked(self, widget):
        """Upload custom icon for checked apps or currently selected row."""
        selected_iters = [self.liststore.get_iter(i) for i, row in enumerate(self.liststore) if row[7]]
        if not selected_iters:
            selection = self.treeview.get_selection()
            model, filter_iter = selection.get_selected()
            if filter_iter:
                real_iter = self.filter.convert_iter_to_child_iter(filter_iter)
                selected_iters = [real_iter]

        if not selected_iters:
            return

        self._handle_batch_custom_icon_selection(selected_iters)

    def on_change_bg_clicked(self, widget):
        """Open background mode dialog to change background for checked rows or selected row."""
        selected_iters = [self.liststore.get_iter(i) for i, row in enumerate(self.liststore) if row[7]]
        if not selected_iters:
            selection = self.treeview.get_selection()
            model, filter_iter = selection.get_selected()
            if filter_iter:
                real_iter = self.filter.convert_iter_to_child_iter(filter_iter)
                selected_iters = [real_iter]

        if not selected_iters:
            return

        self._show_change_bg_dialog(selected_iters)

    def _show_change_bg_dialog(self, selected_iters):
        """Show background mode radio dialog & optional color chooser, then apply background."""
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

        radios[0].set_active(True)
        bg_dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        bg_dialog.show_all()

        bg_response = bg_dialog.run()
        if bg_response != Gtk.ResponseType.OK:
            bg_dialog.destroy()
            return

        selected_bg_mode = "white"
        for radio in radios:
            if radio.get_active():
                selected_bg_mode = radio._mode_id
                break
        bg_dialog.destroy()

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
                return
            color_dialog.destroy()

        self.status_label.set_text(t("batch_processing", count=len(selected_iters)))
        self.spinner.start()

        thread = Thread(
            target=self._apply_bg_change_batch,
            args=(selected_iters, selected_bg_mode, custom_color)
        )
        thread.daemon = True
        thread.start()

    def _apply_bg_change_batch(self, selected_iters, bg_mode, custom_color):
        """Background thread: apply background mode change to selected icons."""
        for real_iter in selected_iters:
            icon_name = self.liststore[real_iter][2]
            app_name = self.liststore[real_iter][1]
            state = self.liststore[real_iter][0]

            target_state = state if state in ("custom", "masked", "cropped") else "custom"

            GLib.idle_add(self.update_status, f"{app_name}...")
            GLib.idle_add(self._update_bg_liststore_state, real_iter, target_state, bg_mode, custom_color)
            self._process_single_icon(
                icon_name, target_state, real_iter,
                bg_mode=bg_mode, custom_color=custom_color, skip_refresh=True
            )

        refresh_icon_cache()
        GLib.idle_add(self._on_process_done)

    def _update_bg_liststore_state(self, real_iter, target_state, bg_mode, custom_color):
        """Update liststore state and custom background mode on main thread."""
        icon_name = self.liststore[real_iter][2]
        set_custom_bg_mode(icon_name, bg_mode, custom_color)
        self.liststore[real_iter][0] = target_state
        self.liststore[real_iter][5] = bg_mode
        self.liststore[real_iter][6] = custom_color or ""

    def _handle_batch_custom_icon_selection(self, selected_iters):
        """Open file chooser dialog directly to select custom icon image file for batch."""
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

            self.status_label.set_text(t("batch_processing", count=len(selected_iters)))
            self.spinner.start()

            thread = Thread(
                target=self._process_batch,
                args=(selected_iters, "custom"),
                kwargs={
                    "custom_path": custom_path,
                    "bg_mode": "white",
                    "custom_color": None
                }
            )
            thread.daemon = True
            thread.start()
        else:
            dialog.destroy()

    def on_batch_apply(self, widget):
        """Apply the selected masking mode to all checked rows."""
        selected_iters = []
        for i, row in enumerate(self.liststore):
            if row[7]:
                selected_iters.append(self.liststore.get_iter(i))

        if not selected_iters:
            return

        new_state = self.batch_combo.get_active_id()
        if not new_state:
            return

        if new_state == "custom":
            self._handle_batch_custom_icon_selection(selected_iters)
            return

        self.status_label.set_text(t("batch_processing", count=len(selected_iters)))
        self.spinner.start()

        thread = Thread(target=self._process_batch, args=(selected_iters, new_state))
        thread.daemon = True
        thread.start()

    def _process_batch(self, selected_iters, new_state, custom_path=None, bg_mode="white", custom_color=None):
        """Background thread: process all selected icons and refresh cache once."""
        for real_iter in selected_iters:
            icon_name = self.liststore[real_iter][2]
            app_name = self.liststore[real_iter][1]
            GLib.idle_add(self.update_status, f"{app_name}...")
            GLib.idle_add(self._update_liststore_state, real_iter, new_state, custom_path, bg_mode, custom_color)
            self._process_single_icon(icon_name, new_state, real_iter, bg_mode=bg_mode, custom_color=custom_color, skip_refresh=True)

        refresh_icon_cache()
        GLib.idle_add(self._on_process_done)

    def _update_liststore_state(self, real_iter, new_state, custom_path=None, bg_mode="white", custom_color=None):
        """Update the liststore state on the main thread."""
        icon_name = self.liststore[real_iter][2]
        if new_state == "custom" and custom_path:
            set_custom_icon_path(icon_name, custom_path)
            set_custom_bg_mode(icon_name, bg_mode, custom_color)
            self.liststore[real_iter][3] = custom_path
            self.liststore[real_iter][5] = bg_mode
            self.liststore[real_iter][6] = custom_color or ""
        else:
            # Clear custom icon path for any state other than custom
            set_custom_icon_path(icon_name, None)
            self.liststore[real_iter][3] = ""
            if new_state in ("masked", "cropped"):
                set_custom_bg_mode(icon_name, bg_mode, custom_color)
                self.liststore[real_iter][5] = bg_mode
                self.liststore[real_iter][6] = custom_color or ""

        self.liststore[real_iter][0] = new_state

    # ── Filter & Language ───────────────────────────────────────────

    def filter_func(self, model, iter, data):
        """Filter apps by search query matching name or icon name."""
        query = self.search_entry.get_text().lower()
        if not query:
            return True
        name = model[iter][1].lower()
        icon = model[iter][2].lower()
        return query in name or query in icon

    def on_language_changed(self, combo):
        """Handle language switch - restarts the window to refresh UI."""
        lang = combo.get_active_id()
        if lang and lang != i18n.CURRENT_LANG:
            i18n.set_lang(lang)
            self.destroy()
            new_win = SquircleApp()
            new_win.connect("destroy", Gtk.main_quit)
            new_win.show_all()

    def on_search_changed(self, entry):
        self.filter.refilter()

    # ── Icon Loading ────────────────────────────────────────────────

    def get_icon_state(self, icon_name):
        """Determine the current masking state of an icon from file markers."""
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
        """Scan .desktop files to populate the application list."""
        apps_dict = {}
        dirs = [
            "/usr/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
            "/var/lib/snapd/desktop/applications"
        ]
        for d in dirs:
            if not os.path.exists(d):
                continue
            for f in os.listdir(d):
                if not f.endswith(".desktop"):
                    continue
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
            custom_path = get_custom_icon_path(icon_id) or ""
            out_path = os.path.join(THEME_DIR, f"{icon_id}.svg")
            pixbuf = None
            if os.path.exists(out_path) and not os.path.islink(out_path):
                pixbuf = self.load_icon_pixbuf_from_file(out_path)
            if not pixbuf:
                pixbuf = self.load_icon_pixbuf(info["icon"])
            bg_mode, custom_color = get_custom_bg_mode(icon_id) if info["state"] == "custom" else ("white", None)
            self.liststore.append([
                info["state"], info["name"], info["icon"], custom_path,
                pixbuf, bg_mode, custom_color or "", False
            ])

        self.status_label.set_text(t("loaded", count=len(self.liststore)))

    # ── Combo Change Handlers ───────────────────────────────────────

    def on_bg_combo_changed(self, widget, path, text):
        """Handle background mode change from the inline combo column for any state."""
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

        state = self.liststore[real_iter][0]
        # Target state: if currently theme/original, default to custom/masked
        target_state = state if state in ("custom", "masked", "cropped") else "masked"

        app_name = self.liststore[real_iter][1]
        icon_name = self.liststore[real_iter][2]

        custom_color = None
        if new_bg_mode == "custom_color":
            color_dialog = Gtk.ColorChooserDialog(
                title=t("select_color"),
                parent=self
            )
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

        self.liststore[real_iter][0] = target_state
        self.liststore[real_iter][5] = new_bg_mode
        self.liststore[real_iter][6] = custom_color or ""

        set_custom_bg_mode(icon_name, new_bg_mode, custom_color)

        self.status_label.set_text(t("processing", app=app_name))
        self.spinner.start()

        thread = Thread(
            target=self._process_single_icon,
            args=(icon_name, target_state, real_iter),
            kwargs={"bg_mode": new_bg_mode, "custom_color": custom_color}
        )
        thread.daemon = True
        thread.start()

    def on_combo_changed(self, widget, path, text):
        """Handle masking mode change from the inline combo column."""
        text_to_id = {
            t("opt_theme"): "theme",
            t("opt_masked"): "masked",
            "cropped": "cropped",
            t("opt_cropped"): "cropped",
            t("opt_original"): "original",
            t("opt_custom"): "custom"
        }
        new_state = text_to_id.get(text)
        if not new_state:
            return

        filter_iter = self.filter.get_iter(path)
        real_iter = self.filter.convert_iter_to_child_iter(filter_iter)

        app_name = self.liststore[real_iter][1]
        icon_name = self.liststore[real_iter][2]
        old_state = self.liststore[real_iter][0]

        if new_state == "custom":
            self._handle_custom_icon_selection(real_iter, app_name, icon_name, old_state)
        else:
            # Clear custom path when switching away from custom mode
            set_custom_icon_path(icon_name, None)
            self.liststore[real_iter][3] = ""

            bg_mode = self.liststore[real_iter][5] or "white"
            custom_color = self.liststore[real_iter][6] or None

            self.liststore[real_iter][0] = new_state
            self.status_label.set_text(t("processing", app=app_name))
            self.spinner.start()

            thread = Thread(
                target=self._process_single_icon,
                args=(icon_name, new_state, real_iter),
                kwargs={"bg_mode": bg_mode, "custom_color": custom_color}
            )
            thread.daemon = True
            thread.start()

    def _handle_custom_icon_selection(self, real_iter, app_name, icon_name, old_state):
        """Open file chooser dialog directly to select custom icon image file."""
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

            selected_bg_mode = self.liststore[real_iter][5] or "white"
            custom_color = self.liststore[real_iter][6] or None

            set_custom_icon_path(icon_name, custom_path)
            self.liststore[real_iter][3] = custom_path
            self.liststore[real_iter][0] = "custom"
            self.liststore[real_iter][5] = selected_bg_mode
            self.liststore[real_iter][6] = custom_color or ""

            set_custom_bg_mode(icon_name, selected_bg_mode, custom_color)

            self.status_label.set_text(t("processing", app=app_name))
            self.spinner.start()

            thread = Thread(
                target=self._process_single_icon,
                args=(icon_name, "custom", real_iter),
                kwargs={"bg_mode": selected_bg_mode, "custom_color": custom_color}
            )
            thread.daemon = True
            thread.start()
        else:
            dialog.destroy()
            self.liststore[real_iter][0] = old_state

    # ── Icon Processing ─────────────────────────────────────────────

    def _process_single_icon(self, icon_name, state, real_iter, bg_mode="white", custom_color=None, skip_refresh=False):
        """Process a single icon masking operation in a background thread."""
        try:
            if state == "theme":
                sync_all_theme_icons(icon_name, "theme")
                GLib.idle_add(self.update_status, t("restored_theme", icon=icon_name))

            elif state == "original":
                orig_path = find_original_icon(icon_name)
                if not orig_path:
                    GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                    return
                sync_all_theme_icons(icon_name, "original", orig_path=orig_path)
                GLib.idle_add(self.update_status, t("set_original", icon=icon_name))

            elif state == "custom":
                custom_path = get_custom_icon_path(icon_name)
                if not custom_path or not os.path.exists(custom_path):
                    GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                    GLib.idle_add(self._revert_combo, real_iter, "theme", not skip_refresh)
                    return
                svg_content = generate_custom_svg(custom_path, bg_mode, custom_color)
                sync_all_theme_icons(icon_name, "custom", svg_content=svg_content)
                GLib.idle_add(self.update_status, t("set_custom", icon=icon_name))

            elif state == "masked":
                orig_path = find_original_icon(icon_name)
                if not orig_path:
                    GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                    GLib.idle_add(self._revert_combo, real_iter, "theme", not skip_refresh)
                    return
                svg_content = generate_masked_svg(orig_path, bg_mode, custom_color)
                sync_all_theme_icons(icon_name, "masked", svg_content=svg_content)
                GLib.idle_add(self.update_status, t("masked", icon=icon_name))

            elif state == "cropped":
                orig_path = find_original_icon(icon_name)
                if not orig_path:
                    GLib.idle_add(self.update_status, t("err_not_found", icon=icon_name))
                    GLib.idle_add(self._revert_combo, real_iter, "theme", not skip_refresh)
                    return
                svg_content = generate_cropped_svg(orig_path, bg_mode, custom_color)
                sync_all_theme_icons(icon_name, "cropped", svg_content=svg_content)
                GLib.idle_add(self.update_status, t("mask_cropped", icon=icon_name))

        except Exception:
            GLib.idle_add(self.update_status, t("err_convert", icon=icon_name))
            GLib.idle_add(self._revert_combo, real_iter, "theme", not skip_refresh)
            return

        if skip_refresh:
            GLib.idle_add(self._reload_pixbuf, real_iter)
            return

        GLib.idle_add(self.update_status, t("refreshing_cache"))
        refresh_icon_cache()
        GLib.idle_add(self._on_process_done, real_iter)

    # ── UI State Updates ────────────────────────────────────────────

    def update_status(self, msg):
        """Update status bar label text."""
        self.status_label.set_text(msg)

    def _reload_pixbuf(self, real_iter=None):
        """Reload pixbuf for a single icon without stopping spinner (used for batch)."""
        if real_iter is not None:
            try:
                icon_name = self.liststore[real_iter][2]
                out_path = os.path.join(THEME_DIR, f"{icon_name}.svg")
                new_pixbuf = None
                if os.path.exists(out_path) and not os.path.islink(out_path):
                    new_pixbuf = self.load_icon_pixbuf_from_file(out_path)
                if not new_pixbuf:
                    theme = Gtk.IconTheme.get_default()
                    theme.rescan_if_needed()
                    new_pixbuf = self.load_icon_pixbuf(icon_name)
                if new_pixbuf:
                    self.liststore[real_iter][4] = new_pixbuf
            except Exception:
                pass

    def _on_process_done(self, real_iter=None):
        """Stop spinner, reload pixbuf, and update status."""
        self.spinner.stop()
        self._reload_pixbuf(real_iter)
        self.status_label.set_text(t("refresh_done"))

    def _revert_combo(self, real_iter, val, stop_spinner=True):
        """Revert combo state on error."""
        self.liststore[real_iter][0] = val
        if stop_spinner:
            self.spinner.stop()


def run_gui():
    """Launch the SquircleMasker GUI application."""
    win = SquircleApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    run_gui()
