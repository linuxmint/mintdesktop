#!/usr/bin/python3

import os
import subprocess
import gettext
import shutil
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository import Gio
from subprocess import Popen

# i18n
gettext.install("mintdesktop", "/usr/share/linuxmint/locale")


class SidePage:

    def __init__(self, notebook_index, name, icon):
        self.notebook_index = notebook_index
        self.name = name
        self.icon = icon


class MintDesktop:

    def set_string(self, schema, key, value):
        settings = Gio.Settings.new(schema)
        settings.set_string(key, value)

    def get_string(self, schema, key):
        settings = Gio.Settings.new(schema)
        return settings.get_string(key)

    def set_bool(self, schema, key, value):
        settings = Gio.Settings.new(schema)
        settings.set_boolean(key, value.get_active())

    def get_bool(self, schema, key):
        settings = Gio.Settings.new(schema)
        return settings.get_boolean(key)

    def init_checkbox(self, schema, key, name):
        source = Gio.SettingsSchemaSource.get_default()
        if source.lookup(schema, True) != None:
            widget = self.builder.get_object(name)
            value = self.get_bool(schema, key)
            widget.set_active(value)
            widget.connect("clicked", lambda x: self.set_bool(schema, key, x))

    def init_combobox(self, schema, key, name):
        source = Gio.SettingsSchemaSource.get_default()
        if source.lookup(schema, True) != None:
            widget = self.builder.get_object(name)
            conf = self.get_string(schema, key)
            index = 0
            for row in widget.get_model():
                if(conf == row[1]):
                    widget.set_active(index)
                    break
                index = index + 1
            widget.connect("changed", lambda x: self.combo_fallback(schema, key, x))

    def combo_fallback(self, schema, key, widget):
        act = widget.get_active()
        value = widget.get_model()[act]
        self.set_string(schema, key, value[1])

    # Change pages
    def side_view_nav(self, param):
        treePaths = param.get_selected_items()
        if (len(treePaths) > 0):
            treePath = treePaths[0]
            index = int("%s" % treePath) #Hack to turn treePath into an int
            target = self.sidePages[index].notebook_index
            self.builder.get_object("notebook1").set_current_page(target)

    def wm_changed(self, widget):
        Popen(["window-manager-launcher"])
        act = widget.get_active()
        wm = widget.get_model()[act][1]
        self.show_hide_options(wm)

    def show_hide_options(self, wm):
        self.builder.get_object("frame_marco").hide()
        self.builder.get_object("frame_metacity").hide()
        self.builder.get_object("frame_compiz").hide()
        if "marco" in wm:
            self.builder.get_object("frame_marco").show()
        elif "metacity" in wm:
            self.builder.get_object("frame_metacity").show()
        elif "compiz" in wm and os.path.exists("/usr/bin/ccsm"):
            self.builder.get_object("frame_compiz").show()
            self.builder.get_object("compiz_reset_button").set_sensitive(os.path.exists(self.compiz_path))

    def help_button_clicked(self, widget):
        Popen(["xdg-open", "help:mintdesktop"])

    def compiz_settings_button_clicked(self, widget):
        Popen(["ccsm"])

    def compiz_reset_button_clicked(self, widget):
        if os.path.exists(self.compiz_path):
            shutil.rmtree(self.compiz_path)
        Popen(["compiz-reset-profile"])

    def _on_key_released(self, window, event):
        if event.keyval != Gdk.KEY_F1:
            return
        self.help_button_clicked(window)

    def close_button_clicked(self, widget):
        Gtk.main_quit()

    ''' Create the UI '''

    def __init__(self):

        # load our glade ui file in
        self.builder = Gtk.Builder()
        self.builder.add_from_file('/usr/share/linuxmint/mintdesktop/main.ui')
        self.window = self.builder.get_object("main_window")
        self.window.connect("destroy", Gtk.main_quit)

        side_desktop_options = SidePage(0, _("Desktop"), "user-desktop")
        side_windows = SidePage(1, _("Windows"), "preferences-system-windows")
        side_interface = SidePage(2, _("Interface"), "preferences-desktop")
        side_terminal = SidePage(3, _("Terminal"), "terminal")

        self.compiz_path = os.path.expanduser('~/.config/compiz-1')

        wm_info = subprocess.getoutput("wmctrl -m")
        self.show_hide_options(wm_info.lower())

        self.xfce = False
        try:
            if "xfce4" in os.environ['XDG_DATA_DIRS']:
                self.xfce = True
        except:
            pass

        if self.xfce:
            self.sidePages = [side_windows, side_terminal]
        else:
            self.sidePages = [side_desktop_options, side_windows, side_interface, side_terminal]

        # create the backing store for the side nav-view.
        theme = Gtk.IconTheme.get_default()
        self.store = Gtk.ListStore(str, GdkPixbuf.Pixbuf)
        for sidePage in self.sidePages:
            img = theme.load_icon(sidePage.icon, 36, 0)
            self.store.append([sidePage.name, img])

        target = self.sidePages[0].notebook_index
        self.builder.get_object("notebook1").set_current_page(target)

        # set up the side view - navigation.
        self.builder.get_object("side_view").set_text_column(0)
        self.builder.get_object("side_view").set_pixbuf_column(1)
        self.builder.get_object("side_view").set_model(self.store)
        self.builder.get_object("side_view").select_path(Gtk.TreePath.new_first())
        self.builder.get_object("side_view").connect("selection_changed", self.side_view_nav)

        # set up larger components.
        self.window.set_title(_("Desktop Settings"))
        self.window.connect("destroy", Gtk.main_quit)

        # i18n
        self.builder.get_object("label_desktop_icons").set_markup("<b>" + _("Desktop icons") + "</b>")
        self.builder.get_object("label_marco").set_markup("<b>" + _("Marco settings") + "</b>")
        self.builder.get_object("label_metacity").set_markup("<b>" + _("Metacity settings") + "</b>")
        self.builder.get_object("label_compiz").set_markup("<b>" + _("Compiz settings") + "</b>")
        self.builder.get_object("compiz_settings_button").set_label(_("Configure Compiz"))
        self.builder.get_object("compiz_reset_button").set_label(_("Reset Compiz settings"))
        self.builder.get_object("label_icons").set_markup("<b>" + _("Icons") + "</b>")
        self.builder.get_object("label_context_menus").set_markup("<b>" + _("Context menus") + "</b>")
        self.builder.get_object("label_toolbars").set_markup("<b>" + _("Toolbars") + "</b>")
        self.builder.get_object("label_terminal").set_markup("<b>" + _("Terminal") + "</b>")
        self.builder.get_object("label_wm").set_markup("<b>" + _("Window Manager") + "</b>")

        self.builder.get_object("caption_desktop_icons").set_markup("<small><i><span foreground=\"#555555\">" + _("Select the items you want to see on the desktop:") + "</span></i></small>")

        self.builder.get_object("checkbox_computer").set_label(_("Computer"))
        self.builder.get_object("checkbox_home").set_label(_("Home"))
        self.builder.get_object("checkbox_network").set_label(_("Network"))
        self.builder.get_object("checkbox_trash").set_label(_("Trash"))
        self.builder.get_object("checkbox_volumes").set_label(_("Mounted Volumes"))

        self.builder.get_object("checkbutton_resources_marco").set_label(_("Don't show window content while dragging them"))
        self.builder.get_object("checkbutton_titlebar_marco").set_label(_("Use system font in titlebar"))
        self.builder.get_object("label_layouts_marco").set_text(_("Buttons layout:"))
        self.builder.get_object("checkbutton_resources_metacity").set_label(_("Don't show window content while dragging them"))
        self.builder.get_object("checkbutton_titlebar_metacity").set_label(_("Use system font in titlebar"))
        self.builder.get_object("label_layouts_metacity").set_text(_("Buttons layout:"))

        self.builder.get_object("checkbox_fortunes").set_label(_("Show fortune cookies"))

        self.builder.get_object("checkbutton_menuicon").set_label(_("Show icons on menus"))
        self.builder.get_object("checkbutton_button_icons").set_label(_("Show icons on buttons"))
        self.builder.get_object("checkbutton_im_menu").set_label(_("Show Input Methods menu in context menus"))
        self.builder.get_object("checkbutton_unicode").set_label(_("Show Unicode Control Character menu in context menus"))

        self.builder.get_object("label_tool_icons").set_text(_("Buttons labels:"))
        self.builder.get_object("label_icon_size").set_text(_("Icon size:"))

        self.builder.get_object("compiz_settings_button").connect("clicked", self.compiz_settings_button_clicked)
        self.builder.get_object("compiz_reset_button").connect("clicked", self.compiz_reset_button_clicked)

        # Ensure MATE loads the WM we set here
        source = Gio.SettingsSchemaSource.get_default()
        if source.lookup('org.mate.session.required-components', True):
            settings = Gio.Settings("org.mate.session.required-components")
            settings.set_string("windowmanager", "mint-window-manager")

        # Ensure Xfce loads the WM we set here
        legacy_xfce_path = os.path.expanduser('~/.config/autostart/Compiz.desktop')
        if os.path.exists(legacy_xfce_path):
            os.unlink(legacy_xfce_path)
        os.system('mkdir -p ~/.config/autostart/')
        os.system('cp /usr/share/linuxmint/mintdesktop/xfce-autostart-wm.desktop ~/.config/autostart/')

        # Desktop page
        self.init_checkbox("org.mate.caja.desktop", "computer-icon-visible", "checkbox_computer")
        self.init_checkbox("org.mate.caja.desktop", "home-icon-visible", "checkbox_home")
        self.init_checkbox("org.mate.caja.desktop", "network-icon-visible", "checkbox_network")
        self.init_checkbox("org.mate.caja.desktop", "trash-icon-visible", "checkbox_trash")
        self.init_checkbox("org.mate.caja.desktop", "volumes-visible", "checkbox_volumes")

        # Window Manager page
        layouts = Gtk.ListStore(str, str)
        layouts.append([_("Traditional style (Right)"), "menu:minimize,maximize,close"])
        layouts.append([_("Mac style (Left)"), "close,minimize,maximize:"])

        self.init_checkbox("org.mate.Marco.general", "reduced-resources", "checkbutton_resources_marco")
        self.init_checkbox("org.mate.Marco.general", "titlebar-uses-system-font", "checkbutton_titlebar_marco")
        self.builder.get_object("combo_wmlayout_marco").set_model(layouts)
        self.init_combobox("org.mate.Marco.general", "button-layout", "combo_wmlayout_marco")

        self.init_checkbox("org.gnome.metacity", "reduced-resources", "checkbutton_resources_metacity")
        self.init_checkbox("org.gnome.desktop.wm.preferences", "titlebar-uses-system-font", "checkbutton_titlebar_metacity")
        self.builder.get_object("combo_wmlayout_metacity").set_model(layouts)
        self.init_combobox("org.gnome.desktop.wm.preferences", "button-layout", "combo_wmlayout_metacity")

        # interface page
        self.init_checkbox("org.mate.interface", "menus-have-icons", "checkbutton_menuicon")
        self.init_checkbox("org.mate.interface", "show-input-method-menu", "checkbutton_im_menu")
        self.init_checkbox("org.mate.interface", "show-unicode-menu", "checkbutton_unicode")
        self.init_checkbox("org.mate.interface", "buttons-have-icons", "checkbutton_button_icons")
        iconSizes = Gtk.ListStore(str, str)
        iconSizes.append([_("Small"), "small-toolbar"])
        iconSizes.append([_("Large"), "large-toolbar"])
        self.builder.get_object("combobox_icon_size").set_model(iconSizes)
        self.init_combobox("org.mate.interface", "toolbar-icons-size", "combobox_icon_size")

        # terminal page
        self.init_checkbox("com.linuxmint.terminal", "show-fortunes", "checkbox_fortunes")

        if "XDG_CURRENT_DESKTOP" in os.environ:
            current_desktop = os.environ["XDG_CURRENT_DESKTOP"]
            if current_desktop == "MATE":
                wm_key = "mate-window-manager"
            else:
                wm_key = "xfce-window-manager"
            print(wm_key)
            settings = Gio.Settings("com.linuxmint.desktop")
            wm = settings.get_string(wm_key)
            wms = Gtk.ListStore(str, str)
            compton = os.path.exists("/usr/bin/compton")
            if os.path.exists("/usr/bin/marco"):
                wms.append([_("Marco"), "marco"])
                wms.append([_("Marco + Compositing"), "marco-composite"])
                if compton:
                    wms.append([_("Marco + Compton"), "marco-compton"])
            if os.path.exists("/usr/bin/metacity"):
                wms.append([_("Metacity"), "metacity"])
                wms.append([_("Metacity + Compositing"), "metacity-composite"])
                if compton:
                    wms.append([_("Metacity + Compton"), "metacity-compton"])
            if os.path.exists("/usr/bin/xfwm4"):
                wms.append([_("Xfwm4"), "xfwm4"])
                wms.append([_("Xfwm4 + Compositing"), "xfwm4-composite"])
                if compton:
                    wms.append([_("Xfwm4 + Compton"), "xfwm4-compton"])
            if os.path.exists("/usr/bin/openbox"):
                wms.append([_("Openbox"), "openbox"])
                if compton:
                    wms.append([_("Openbox + Compton"), "openbox-compton"])
            if os.path.exists("/usr/bin/compiz"):
                wms.append([_("Compiz"), "compiz"])
            if os.path.exists("/usr/bin/awesome"):
                wms.append([_("Awesome"), "awesome"])

            # WMs..
            self.builder.get_object("combo_wm").set_model(wms)
            self.builder.get_object("combo_wm").set_tooltip_text(_("Click on the help button for more information about window managers.\nUse the 'wm-recovery' command to switch back to the default window manager.\nUse the 'wm-detect' command to check which window manager is running."))
            self.init_combobox("com.linuxmint.desktop", wm_key, "combo_wm")
            self.builder.get_object("combo_wm").connect("changed", self.wm_changed)

        # toolbar icon styles
        iconStyles = Gtk.ListStore(str, str)
        iconStyles.append([_("Text below items"), "both"])
        iconStyles.append([_("Text beside items"), "both-horiz"])
        iconStyles.append([_("Icons only"), "icons"])
        iconStyles.append([_("Text only"), "text"])
        self.builder.get_object("combobox_toolicons").set_model(iconStyles)
        self.init_combobox("org.mate.interface", "toolbar-style", "combobox_toolicons")

        self.builder.get_object("help_button").connect("clicked", self.help_button_clicked)
        self.builder.get_object("close_button").connect("clicked", self.close_button_clicked)

        self.window.show()
        self.window.connect("key-release-event", self._on_key_released)

if __name__ == "__main__":
    MintDesktop()
    Gtk.main()
