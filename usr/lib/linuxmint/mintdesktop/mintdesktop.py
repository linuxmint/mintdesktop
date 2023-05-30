#!/usr/bin/python3

import gettext
import os
import shutil
import subprocess

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository import Gio
from subprocess import Popen

from xapp.GSettingsWidgets import *

gettext.install("mintdesktop", "/usr/share/linuxmint/locale")

class SidePage:

    def __init__(self, notebook_index, name, icon):
        self.notebook_index = notebook_index
        self.name = name
        self.icon = icon

class MintDesktop:

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
        wm = widget.get_model()[act][0]
        print(wm)
        self.show_hide_options(wm)

    def show_hide_options(self, wm):
        if self.marco_section is not None:
            self.marco_section.hide()
        self.metacity_section.hide()
        self.mutter_section.hide()
        self.xfwm4_section.hide()
        self.compiz_section.hide()
        if "marco" in wm:
            self.marco_section.show()
        elif "metacity" in wm:
            self.metacity_section.show()
        elif "mutter" in wm:
            self.mutter_section.show()
        elif "xfwm4" in wm:
            self.xfwm4_section.show()
        elif "compiz" in wm and os.path.exists("/usr/bin/ccsm"):
            self.compiz_section.show()
            self.compiz_reset_button.set_sensitive(os.path.exists(self.compiz_path))

    def help_button_clicked(self, widget):
        Popen(["xdg-open", "help:mintdesktop"])

    def xfwm4_settings_button_clicked(self, widget):
        Popen(["xfwm4-settings"])

    def xfwm4_tweaks_button_clicked(self, widget):
        Popen(["xfwm4-tweaks-settings"])

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
        side_applications = SidePage(3, _("Applications"), "applications-other")

        self.compiz_path = os.path.expanduser('~/.config/compiz-1')

        self.de_is_mate = False
        if os.getenv("XDG_CURRENT_DESKTOP") == "MATE":
            self.de_is_mate = True
            self.sidePages = [side_desktop_options, side_windows, side_interface, side_applications]
        else:
            self.sidePages = [side_windows, side_applications]

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

        # Desktop icons page
        if self.de_is_mate:
            vbox = self.builder.get_object("vbox_desktop_icons")
            page = SettingsPage()
            vbox.pack_start(page, True, True, 0)
            section = page.add_section(_("Desktop icons"), _("Select the items you want to see on the desktop:"))
            section.add_row(GSettingsSwitch(_("Computer"), "org.mate.caja.desktop", "computer-icon-visible"))
            section.add_row(GSettingsSwitch(_("Home"), "org.mate.caja.desktop", "home-icon-visible"))
            section.add_row(GSettingsSwitch(_("Network"), "org.mate.caja.desktop", "network-icon-visible"))
            section.add_row(GSettingsSwitch(_("Trash"), "org.mate.caja.desktop", "trash-icon-visible"))
            section.add_row(GSettingsSwitch(_("Mounted Volumes"), "org.mate.caja.desktop", "volumes-visible"))
            page.show_all()

        # WM page
        size_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        vbox = self.builder.get_object("vbox_wm")
        page = SettingsPage()
        vbox.pack_start(page, True, True, 0)

        section = page.add_section(_("Window Manager"))

        wm_key = "mate-window-manager"
        if not self.de_is_mate:
            wm_key = "xfce-window-manager"
        options = []
        compton = os.path.exists("/usr/bin/compton")
        picom = os.path.exists("/usr/bin/picom")
        if os.path.exists("/usr/bin/marco"):
            options.append(["marco", _("Marco")])
            options.append(["marco-composite", _("Marco + Compositing")])
            if compton:
                options.append(["marco-compton", _("Marco + Compton")])
            if picom:
                options.append(["marco-picom", _("Marco + Picom")])
        if os.path.exists("/usr/bin/metacity"):
            options.append(["metacity", _("Metacity")])
            options.append(["metacity-composite", _("Metacity + Compositing")])
            if compton:
                options.append(["metacity-compton", _("Metacity + Compton")])
            if picom:
                options.append(["metacity-picom", _("Metacity + Picom")])
        if os.path.exists("/usr/bin/xfwm4"):
            options.append(["xfwm4", _("Xfwm4")])
            options.append(["xfwm4-composite", _("Xfwm4 + Compositing")])
            if compton:
                options.append(["xfwm4-compton", _("Xfwm4 + Compton")])
            if picom:
                options.append(["xfwm4-picom", _("Xfwm4 + Picom")])
        if os.path.exists("/usr/bin/openbox"):
            options.append(["openbox", _("Openbox")])
            if compton:
                options.append(["openbox-compton", _("Openbox + Compton")])
            if picom:
                options.append(["openbox-picom", _("Openbox + Picom")])
        if os.path.exists("/usr/bin/mutter"):
            options.append(["mutter", _("Mutter")])
        if os.path.exists("/usr/bin/compiz"):
            options.append(["compiz", _("Compiz")])
        if os.path.exists("/usr/bin/awesome"):
            options.append(["awesome", _("Awesome")])
        combo = GSettingsComboBox(_("Window Manager"), "com.linuxmint.desktop", wm_key, options, size_group=size_group)
        combo.set_tooltip_text(_("Click on the help button for more information about window managers.\nUse the 'wm-recovery' command to switch back to the default window manager.\nUse the 'wm-detect' command to check which window manager is running."))
        combo.content_widget.connect("changed", self.wm_changed)
        section.add_row(combo)

        button_options = []
        button_options.append([":minimize,maximize,close", _("Traditional style (Right)")])
        button_options.append(["close,minimize,maximize:", _("Mac style (Left)")])

        csd_button_options = []
        csd_button_options.append(["menu:minimize,maximize,close", _("Traditional style (Right)")])
        csd_button_options.append(["close,minimize,maximize:menu", _("Mac style (Left)")])

        if self.de_is_mate:
            options = []
            options.append([0, _("Auto")])
            options.append([1, _("Normal")])
            options.append([2, _("Double (HiDPI)")])
            section.add_row(GSettingsComboBox(_("User interface scaling"), "org.mate.interface", "window-scaling-factor", options, size_group=size_group))

            self.marco_section = page.add_section(_("Marco settings"))
            self.marco_section.add_row(GSettingsSwitch(_("Use system font in titlebar"), "org.mate.Marco.general", "titlebar-uses-system-font"))
            self.marco_section.add_row(GSettingsSwitch(_("Don't show window content while dragging them"), "org.mate.Marco.general", "reduced-resources"))
            self.marco_section.add_row(GSettingsComboBox(_("Buttons layout:"), "org.mate.Marco.general", "button-layout", button_options, size_group=size_group))
            self.marco_section.add_row(GSettingsComboBox(_("Buttons layout (CSD windows):"), "org.mate.interface", "gtk-decoration-layout", csd_button_options, size_group=size_group))
        else:
            self.marco_section = None

        self.metacity_section = page.add_section(_("Metacity settings"))
        self.metacity_section.add_row(GSettingsSwitch(_("Use system font in titlebar"), "org.gnome.desktop.wm.preferences", "titlebar-uses-system-font"))
        self.metacity_section.add_row(GSettingsComboBox(_("Buttons layout:"), "org.gnome.desktop.wm.preferences", "button-layout", button_options, size_group=size_group))

        self.mutter_section = page.add_section(_("Mutter settings"))
        if os.path.exists("/usr/bin/mutter"):
            self.mutter_section.add_row(GSettingsSwitch(_("Use system font in titlebar"), "org.gnome.desktop.wm.preferences", "titlebar-uses-system-font"))
            self.mutter_section.add_row(GSettingsSwitch(_("Place new windows in the center of the screen"), "org.gnome.mutter", "center-new-windows"))
            self.mutter_section.add_row(GSettingsSwitch(_("Automatically maximize nearly screen sized windows"), "org.gnome.mutter", "auto-maximize"))
            self.mutter_section.add_row(GSettingsSwitch(_("Enable edge tiling when dropping windows on screen edges"), "org.gnome.mutter", "edge-tiling"))
            self.mutter_section.add_row(GSettingsComboBox(_("Buttons layout:"), "org.gnome.desktop.wm.preferences", "button-layout", button_options, size_group=size_group))

        self.xfwm4_section = page.add_section(_("Xfwm4 settings"))
        self.xfwm4_settings_button = Gtk.Button(label=_("Configure Xfwm4"))
        self.xfwm4_settings_button.connect("clicked", self.xfwm4_settings_button_clicked)
        self.xfwm4_section.add_row(self.xfwm4_settings_button)
        self.xfwm4_tweaks_button = Gtk.Button(label=_("Tweak Xfwm4"))
        self.xfwm4_tweaks_button.connect("clicked", self.xfwm4_tweaks_button_clicked)
        self.xfwm4_section.add_row(self.xfwm4_tweaks_button)

        self.compiz_section = page.add_section(_("Compiz settings"))
        button = Gtk.Button(label=_("Configure Compiz"))
        button.connect("clicked", self.compiz_settings_button_clicked)
        self.compiz_section.add_row(button)
        self.compiz_reset_button = Gtk.Button(label=_("Reset Compiz settings"))
        self.compiz_reset_button.connect("clicked", self.compiz_reset_button_clicked)
        self.compiz_section.add_row(self.compiz_reset_button)

        page.show_all()
        wm_info = subprocess.getoutput("wmctrl -m").lower()
        self.show_hide_options(wm_info)

        # Interface page
        if self.de_is_mate:
            size_group = Gtk.SizeGroup()
            size_group.set_mode(Gtk.SizeGroupMode.HORIZONTAL)

            vbox = self.builder.get_object("vbox_interface")
            page = SettingsPage()
            vbox.pack_start(page, True, True, 0)

            section = page.add_section(_("Icons"))
            section.add_row(GSettingsSwitch(_("Show icons on menus"), "org.mate.interface", "menus-have-icons"))
            section.add_row(GSettingsSwitch(_("Show icons on buttons"), "org.mate.interface", "buttons-have-icons"))

            section = page.add_section(_("Toolbars"))

            options = []
            options.append(["both", _("Text below items")])
            options.append(["both-horiz", _("Text beside items")])
            options.append(["icons", _("Icons only")])
            options.append(["text", _("Text only")])
            section.add_row(GSettingsComboBox(_("Buttons labels:"), "org.mate.interface", "toolbar-style", options, size_group=size_group))

            options = []
            options.append(["small-toolbar", _("Small")])
            options.append(["large-toolbar", _("Large")])
            section.add_row(GSettingsComboBox(_("Icon size:"), "org.mate.interface", "toolbar-icons-size", options, size_group=size_group))

            page.show_all()

            # Ensure MATE loads the WM we set here
            settings = Gio.Settings("com.linuxmint.desktop")
            source = Gio.SettingsSchemaSource.get_default()
            if source.lookup('org.mate.session.required-components', True):
                settings = Gio.Settings("org.mate.session.required-components")
                settings.set_string("windowmanager", "mint-window-manager")


        # Applications page
        size_group = Gtk.SizeGroup()
        size_group.set_mode(Gtk.SizeGroupMode.HORIZONTAL)

        vbox = self.builder.get_object("vbox_applications")
        page = SettingsPage()
        vbox.pack_start(page, True, True, 0)

        section = page.add_section()

        options = [("default", _("Let applications decide")),
                   ("prefer-light", _("Prefer light mode")),
                   ("prefer-dark", _("Prefer dark mode"))]
        widget = GSettingsComboBox(_("Dark mode"), "org.x.apps.portal", "color-scheme", options, size_group=size_group)
        widget.set_tooltip_text(_("This setting only affects applications which support dark mode"))
        section.add_row(widget)

        page.show_all()

        # Ensure Xfce loads the WM we set here
        legacy_xfce_path = os.path.expanduser('~/.config/autostart/Compiz.desktop')
        if os.path.exists(legacy_xfce_path):
            os.unlink(legacy_xfce_path)
        os.system('mkdir -p ~/.config/autostart/')
        os.system('cp /usr/share/linuxmint/mintdesktop/xfce-autostart-wm.desktop ~/.config/autostart/')

        self.builder.get_object("help_button").connect("clicked", self.help_button_clicked)

        self.window.show()
        self.window.connect("key-release-event", self._on_key_released)

if __name__ == "__main__":
    MintDesktop()
    Gtk.main()
