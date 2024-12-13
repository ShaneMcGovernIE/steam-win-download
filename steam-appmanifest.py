#!/usr/bin/env python3

"""
steam_appmanifest.py
Generates Steam app manifests, now with:
1) A freely resizable GUI.
2) A toggleable list of owned games.
3) A search box to filter games by name in real time.
"""

import os
import sys
import re
import requests
import xml.etree.ElementTree as ET

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

STEAM_MANIFEST_TEMPLATE = """\
"AppState"
{{
    "AppID"        "{app_id}"
    "Universe"      "1"
    "name"          "{app_name}"
    "StateFlags"    "4"
    "installdir"    "{app_name}"
    "LastUpdated"   "0"
    "UpdateResult"  "0"
    "SizeOnDisk"    "0"
    "buildid"       "0"
    "LastOwner"     "0"
    "BytesToDownload"   "0"
    "BytesDownloaded"   "0"
    "BytesToStage"      "0"
    "BytesStaged"       "0"
}}
"""

class SteamAppManifest(Gtk.Window):
    def __init__(self):
        super().__init__(title="Steam App Manifest")
        self.set_border_width(10)
        self.set_resizable(True)
        self.set_default_size(600, 400)

        # We'll store (toggled, app_id, name) in a ListStore for the TreeView
        self.games_store = Gtk.ListStore(bool, str, str)

        # Create a filter model from the main store
        self.search_text = ""
        self.filtered_store = self.games_store.filter_new()
        self.filtered_store.set_visible_func(self.game_filter)

        # Main Vertical Box
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(main_vbox)

        # Row0: Steam Profile ID entry and Refresh button
        row0_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_vbox.pack_start(row0_box, False, False, 0)

        row0_label = Gtk.Label(label="https://steamcommunity.com/id/")
        self.profile_entry = Gtk.Entry()
        row0_btn_refresh = Gtk.Button(label="Refresh")
        row0_btn_refresh.connect("clicked", self.on_refresh_click)

        row0_box.pack_start(row0_label, False, False, 0)
        row0_box.pack_start(self.profile_entry, True, True, 0)
        row0_box.pack_start(row0_btn_refresh, False, False, 0)

        # Row1: Instruction label
        row1_label = Gtk.Label(label="Restart Steam for the changes to take effect.")
        main_vbox.pack_start(row1_label, False, False, 0)

        # Row2: Steam Library Path
        row2_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_vbox.pack_start(row2_box, False, False, 0)

        row2_label = Gtk.Label(label="Steam Library Path:")
        self.library_entry = Gtk.Entry()
        self.library_entry.set_text(self.get_default_steam_path())
        row2_box.pack_start(row2_label, False, False, 0)
        row2_box.pack_start(self.library_entry, True, True, 0)

        # Row3: Search box
        row3_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_vbox.pack_start(row3_box, False, False, 0)

        row3_label = Gtk.Label(label="Search games:")
        self.search_entry = Gtk.Entry()
        self.search_entry.connect("changed", self.on_search_changed)

        row3_box.pack_start(row3_label, False, False, 0)
        row3_box.pack_start(self.search_entry, True, True, 0)

        # Row4: Scrolled Window containing a TreeView of toggles and game names
        scrolled_win = Gtk.ScrolledWindow()
        scrolled_win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        main_vbox.pack_start(scrolled_win, True, True, 0)

        self.treeview = Gtk.TreeView(model=self.filtered_store)
        # Create a toggle renderer
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_toggle_toggled)

        col_toggle = Gtk.TreeViewColumn("Select", renderer_toggle, active=0)
        self.treeview.append_column(col_toggle)

        # We'll hide the app_id in the UI, but store it in the model at column 1
        renderer_text = Gtk.CellRendererText()
        col_name = Gtk.TreeViewColumn("Game Name", renderer_text, text=2)
        self.treeview.append_column(col_name)

        scrolled_win.add(self.treeview)

        # Row5: Manual, Download, and Quit buttons
        row5_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_vbox.pack_start(row5_box, False, False, 0)

        row5_manual = Gtk.Button(label="Manual")
        row5_manual.connect("clicked", self.on_manual_click)

        row5_download = Gtk.Button(label="Download")
        row5_download.connect("clicked", self.on_download_click)

        row5_quit = Gtk.Button(label="Quit")
        row5_quit.connect("clicked", Gtk.main_quit)

        row5_box.pack_start(row5_manual, False, False, 0)
        row5_box.pack_start(row5_download, False, False, 0)
        row5_box.pack_start(row5_quit, False, False, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def get_default_steam_path(self):
        """
        Attempt to auto-detect the default Steam library path.
        """
        home = os.path.expanduser("~")
        if sys.platform.startswith("win"):
            # This is a naive guess, the user may have installed Steam elsewhere
            return "C:\\Program Files (x86)\\Steam\\steamapps"
        elif sys.platform.startswith("darwin"):
            # macOS default
            return os.path.join(home, "Library", "Application Support", "Steam", "steamapps")
        else:
            # Linux default
            return os.path.join(home, ".local", "share", "Steam", "steamapps")

    def on_refresh_click(self, button):
        """
        Called when the Refresh button is clicked.
        Fetch the public Steam profile, parse for owned games, and populate the toggle list.
        """
        profile_id = self.profile_entry.get_text().strip()
        if not profile_id:
            self.show_message("Please enter a profile ID.")
            return

        url = f"https://steamcommunity.com/id/{profile_id}/games?tab=all&xml=1"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            self.show_message(f"Failed to fetch the profile: {e}")
            return

        # Clear the store each time Refresh is clicked, so we do not accumulate duplicates
        self.games_store.clear()

        try:
            root = ET.fromstring(response.text)
            games_xml = root.iter('game')
        except ET.ParseError as e:
            self.show_message(f"Failed to parse the XML: {e}")
            return

        for game in games_xml:
            app_id = game.find('appID').text if game.find('appID') is not None else None
            name = game.find('name').text if game.find('name') is not None else None
            if app_id and name:
                # Add the game to the ListStore with toggled=False by default
                self.games_store.append([False, app_id, name])

        # After refreshing, re-run the filter so the user sees the correct results
        self.filtered_store.refilter()

    def on_search_changed(self, entry):
        """
        Callback triggered when the user types in the search box.
        Updates the search string and refilters the list.
        """
        self.search_text = entry.get_text().strip().lower()
        self.filtered_store.refilter()

    def game_filter(self, store, iter_, data=None):
        """
        The visible_func for the filter. Shows rows where the game name matches the search text.
        """
        toggled, app_id, game_name = store[iter_]
        # If no search text, show everything
        if not self.search_text:
            return True
        # Otherwise, show if self.search_text is a substring of game_name (case-insensitive)
        return self.search_text in game_name.lower()

    def on_toggle_toggled(self, cell_renderer, path):
        """
        Toggle the checkbox in the TreeView (the underlying store is self.games_store).
        """
        # Convert path in filtered_store to an iter in the filtered model
        filtered_iter = self.filtered_store.get_iter(path)
        # Map this to the underlying store's iter
        real_iter = self.filtered_store.convert_iter_to_child_iter(filtered_iter)
        current_state = self.games_store[real_iter][0]
        self.games_store[real_iter][0] = not current_state

    def on_manual_click(self, button):
        """
        The Manual button could open a help page, or do something else.
        """
        self.show_message("Manual button clicked. Provide instructions here if needed.")

    def on_download_click(self, button):
        """
        Creates manifests only for the toggled (True) games in the underlying store.
        """
        steam_path = self.library_entry.get_text()
        if not os.path.isdir(steam_path):
            self.show_message("Please provide a valid Steam library path.")
            return

        created_count = 0
        for row in self.games_store:
            toggled, app_id, game_name = row
            if toggled:
                manifest_content = STEAM_MANIFEST_TEMPLATE.format(app_id=app_id, app_name=game_name)
                manifest_path = os.path.join(steam_path, f"appmanifest_{app_id}.acf")
                try:
                    with open(manifest_path, 'w', encoding='utf-8') as f:
                        f.write(manifest_content)
                    created_count += 1
                except OSError as e:
                    self.show_message(f"Error creating manifest for {game_name}: {e}")

        self.show_message(f"Successfully created {created_count} manifest files.")

    def show_message(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

def main():
    app = SteamAppManifest()
    Gtk.main()

if __name__ == "__main__":
    main()
