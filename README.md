Steam-Win-Download
(Forked from steam-appmanifest by pinkwah)
===========================

This script connects to your public Steam profile, retrieves a list of your owned games, and helps you generate the corresponding Windows appmanifest files for the select games used by Steam. Once downloaded, the Windows version of the select games will appear in your Steam download queue.

# Key Features:

- **Refresh & Retrieve Games:** Enter your Steam Community ID, click "Refresh," and the script fetches all your owned games via the Steam Community XML API.
- **Toggleable Game List:** Each game appears in a list with a toggle. Check the boxes beside the games you want to generate manifests for.
- **Search Functionality:** Easily find games by typing a partial name in the search box. The list filters in real time.
- **Selective Manifest Creation:** Click "Download" to create the `.acf` files only for the toggled (selected) games.
- **Flexible & Resizable GUI:** The window layout can be resized to suit your preference.

With this tool, you can quickly populate your Steam library folder with the appropriate manifest files, helping you manage your Steam installations more efficiently.  


# Changelog

Below is a list of all major changes made from the **original script** to the **new updated version**. The changes are grouped by category for clarity.

---

## 1. GTK and Python Compatibility

- **GTK Version Import**  
  - Added `import gi` and `gi.require_version('Gtk', '3.0')` before importing `Gtk` in the newer scripts, ensuring explicit targeting of GTK 3.

- **Replacement of Deprecated Methods**  
  - Replaced `tree.getiterator('game')` (deprecated) with `tree.iter('game')`.
  - Converted positional GObject constructor calls to keyword-based arguments (e.g., `Gtk.Label(label="...")` instead of `Gtk.Label("...")`).

---

## 2. Overall GUI and Layout Rework

- **Freely Resizable Window**  
  - Removed or changed `set_resizable(False)` and used `self.set_resizable(True)`.  
  - Set a default size with `self.set_default_size(600, 400)` for convenience.

- **Box and Layout Changes**  
  - Replaced the single `Gtk.Box` approach with a structured layout, using multiple boxes and a main vertical container (`Gtk.Box(orientation=Gtk.Orientation.VERTICAL, ...)`).

- **Scrolling Support**  
  - Wrapped the game list in a `Gtk.ScrolledWindow` to better handle long lists.

---

## 3. Toggleable Game List & Manifest Generation

- **New Tree Model**  
  - Added a `Gtk.ListStore(bool, str, str)` or similar to store `(toggled, app_id, game_name)`.
  - Used `Gtk.TreeView` with a `Gtk.CellRendererToggle` column to select which games should have manifest files generated.

- **Manifest Creation Button**  
  - Transitioned from a row-by-row approach (`appmanifest` creation/removal) to a single **Download** button that processes all toggled items at once.

- **Selective Manifests**  
  - Only toggled (checked) games generate `.acf` files when “Download” is clicked.

---

## 4. Search Functionality

- **Search Box**  
  - Added a new search field (`Gtk.Entry`) for filtering game names in real time.

- **Filtered Model**  
  - Implemented a filter model (`Gtk.TreeModelFilter`) with a `visible_func` to dynamically show/hide rows based on the user’s search text.

- **Real-Time Filtering**  
  - Whenever the user types in the search field, the model is refiltered to only display matching games (case-insensitive).

---

## 5. Additional Improvements and Enhancements

- **Profile Fetch**  
  - Switched from `urllib.request` to **`requests`** with a timeout and clearer exception handling.

- **Path Detection**  
  - Implemented a cross-platform check for the default Steam library path, varying by OS (Windows, macOS, Linux).

- **Manual vs. Automated**  
  - Kept a “Manual” button or function but relied primarily on the toggleable list for automatic manifest creation.

- **Message Dialogs**  
  - Used `Gtk.MessageDialog` for error/info messages (e.g., timeouts, invalid Steam path).

- **UK English and Comma Usage**  
  - Adjusted user-facing text to conform to UK spelling, replacing textual hyphens with commas.

---

## 6. Code Structure and Readability

- **Refactored into a Single Class**  
  - Merged separate dialog classes (`DlgToggleApp`, `DlgManual`) into a single-window UI or consolidated logic.

- **Function Splitting**  
  - Defined dedicated functions: `on_refresh_click`, `on_download_click`, `on_search_changed`, `on_toggle_toggled` for modular code.

- **Comments and Documentation**  
  - Updated docstrings and inline comments to reflect the new UI layout and flow.

---
