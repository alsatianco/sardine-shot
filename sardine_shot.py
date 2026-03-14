import os
import sys
import time
import datetime
import threading
import queue
import configparser
import webbrowser
import winreg
import pystray
from PIL import Image, ImageGrab, ImageDraw
import tkinter as tk
from tkinter import messagebox, filedialog

# ---------------------------------------------------------------------------
# About info — fill these in before distributing
# ---------------------------------------------------------------------------
AUTHOR_NAME   = "Duc Nguyen"
LINKEDIN_URL  = "https://www.linkedin.com/in/ducnd87"
GITHUB_URL    = "https://github.com/alsatianco/sardine-shot"
APP_VERSION   = "1.0.0"
# ---------------------------------------------------------------------------


# --- Configuration ---
def _get_base_dir():
    """Return directory of the exe (frozen) or script (dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(_get_base_dir(), 'config.ini')
    config.read(config_path)
    save_folder = os.path.expanduser(config.get(
        'Settings', 'save_folder',
        fallback=os.path.join(os.path.expanduser('~'), 'Pictures', 'Screenshots'),
    ))
    interval    = config.getint('Settings', 'interval',     fallback=30)
    retain_days = config.getint('Settings', 'retain_days',  fallback=5)
    # start_with_windows: None means key is missing (first run)
    if config.has_option('Settings', 'start_with_windows'):
        start_with_windows = config.getboolean('Settings', 'start_with_windows')
    else:
        start_with_windows = None
    return save_folder, interval, retain_days, start_with_windows


def _save_config(save_folder, interval, retain_days, start_with_windows):
    config = configparser.ConfigParser()
    config_path = os.path.join(_get_base_dir(), 'config.ini')
    config.read(config_path)
    if not config.has_section('Settings'):
        config.add_section('Settings')
    config.set('Settings', 'save_folder', save_folder)
    config.set('Settings', 'interval',    str(interval))
    config.set('Settings', 'retain_days', str(retain_days))
    config.set('Settings', 'start_with_windows', str(start_with_windows).lower())
    with open(config_path, 'w') as f:
        config.write(f)


SAVE_FOLDER, INTERVAL, RETAIN_DAYS, START_WITH_WINDOWS = _load_config()
os.makedirs(SAVE_FOLDER, exist_ok=True)


# --- Windows autostart via registry ---
_REGISTRY_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
_REGISTRY_APP = 'SardineShot'


def _get_exe_path():
    """Return the path to use for the autostart registry entry."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return f'"{sys.executable}" "{os.path.abspath(__file__)}"'


def _set_autostart(enable):
    """Add or remove the app from Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REGISTRY_KEY,
                             0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, _REGISTRY_APP, 0, winreg.REG_SZ,
                              _get_exe_path())
        else:
            try:
                winreg.DeleteValue(key, _REGISTRY_APP)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError:
        pass


# --- State ---
_paused          = False
_stop_event      = threading.Event()
_settings_event  = threading.Event()   # set when settings change to wake the loop
_action_queue    = queue.Queue()


# --- Core logic ---
def delete_old_files(folder, days):
    if not os.path.exists(folder):
        return
    cutoff = time.time() - days * 86400
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)


def screenshot_loop():
    """Takes periodic screenshots using the current global settings."""
    while not _stop_event.is_set():
        if not _paused:
            os.makedirs(SAVE_FOLDER, exist_ok=True)
            delete_old_files(SAVE_FOLDER, RETAIN_DAYS)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath  = os.path.join(SAVE_FOLDER, f"screenshot_{timestamp}.png")
            ImageGrab.grab().save(filepath)
        # Wait INTERVAL seconds; wake immediately if settings change or stop is requested.
        _settings_event.clear()
        start = time.time()
        while not _stop_event.is_set() and not _settings_event.is_set():
            remaining = INTERVAL - (time.time() - start)
            if remaining <= 0:
                break
            _stop_event.wait(min(1.0, remaining))


# --- Tray icon drawing ---
def create_tray_icon():
    img  = Image.new("RGB", (64, 64), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    draw.rectangle([6,  20, 58, 54], fill=(190, 190, 190))   # camera body
    draw.rectangle([20, 13, 34, 21], fill=(190, 190, 190))   # viewfinder bump
    draw.ellipse(  [18, 27, 46, 47], fill=(50,  90,  180))   # lens outer
    draw.ellipse(  [26, 32, 38, 42], fill=(180, 220, 255))   # lens highlight
    return img


# --- Settings window ---
def _show_settings():
    global SAVE_FOLDER, INTERVAL, RETAIN_DAYS, START_WITH_WINDOWS

    win = tk.Tk()
    win.title("Settings")
    win.resizable(False, False)
    win.attributes('-topmost', True)

    FONT      = ('Segoe UI', 9)
    FONT_BOLD = ('Segoe UI', 9, 'bold')
    FONT_HINT = ('Segoe UI', 8)
    PAD       = {'padx': 12, 'pady': 3}
    CLR_ERR   = '#cc0000'
    CLR_HINT  = '#666666'
    CLR_FIELD_ERR = '#ffe0e0'

    # ── Save Folder ──────────────────────────────────────────────────────────
    tk.Label(win, text="Save Folder", font=FONT_BOLD).grid(
        row=0, column=0, sticky='w', **PAD)
    folder_var   = tk.StringVar(value=SAVE_FOLDER)
    folder_entry = tk.Entry(win, textvariable=folder_var, width=44, font=FONT)
    folder_entry.grid(row=0, column=1, **PAD)

    def browse():
        d = filedialog.askdirectory(
            initialdir=folder_var.get() or os.path.expanduser('~'), parent=win)
        if d:
            folder_var.set(d)

    tk.Button(win, text="Browse…", command=browse, font=FONT).grid(
        row=0, column=2, padx=(0, 12))
    tk.Label(win,
             text="Folder where screenshots are saved.\n"
                  r"Example: C:\Users\YourName\Pictures\Screenshots",
             font=FONT_HINT, fg=CLR_HINT, justify='left').grid(
        row=1, column=1, sticky='w', padx=12, pady=(0, 8))

    # ── Interval ─────────────────────────────────────────────────────────────
    tk.Label(win, text="Interval (seconds)", font=FONT_BOLD).grid(
        row=2, column=0, sticky='w', **PAD)
    interval_var   = tk.StringVar(value=str(INTERVAL))
    interval_entry = tk.Entry(win, textvariable=interval_var, width=10, font=FONT)
    interval_entry.grid(row=2, column=1, sticky='w', **PAD)
    tk.Label(win,
             text="How often to take a screenshot. Must be a whole number ≥ 1.\n"
                  "Example: 30",
             font=FONT_HINT, fg=CLR_HINT, justify='left').grid(
        row=3, column=1, sticky='w', padx=12, pady=(0, 8))

    # ── Retain Days ───────────────────────────────────────────────────────────
    tk.Label(win, text="Retain Days", font=FONT_BOLD).grid(
        row=4, column=0, sticky='w', **PAD)
    retain_var   = tk.StringVar(value=str(RETAIN_DAYS))
    retain_entry = tk.Entry(win, textvariable=retain_var, width=10, font=FONT)
    retain_entry.grid(row=4, column=1, sticky='w', **PAD)
    tk.Label(win,
             text="Days to keep screenshots before auto-deleting. Must be a whole number ≥ 1.\n"
                  "Example: 5",
             font=FONT_HINT, fg=CLR_HINT, justify='left').grid(
        row=5, column=1, sticky='w', padx=12, pady=(0, 8))

    # ── Start with Windows ─────────────────────────────────────────────────────
    tk.Label(win, text="Start with Windows", font=FONT_BOLD).grid(
        row=6, column=0, sticky='w', **PAD)
    startup_var = tk.BooleanVar(value=bool(START_WITH_WINDOWS))
    tk.Checkbutton(win, variable=startup_var, font=FONT).grid(
        row=6, column=1, sticky='w', **PAD)
    tk.Label(win,
             text="Automatically launch Sardine Shot when you log in to Windows.",
             font=FONT_HINT, fg=CLR_HINT, justify='left').grid(
        row=7, column=1, sticky='w', padx=12, pady=(0, 8))

    # ── Error area ────────────────────────────────────────────────────────────
    error_var = tk.StringVar()
    tk.Label(win, textvariable=error_var, fg=CLR_ERR, font=FONT,
             wraplength=420, justify='left').grid(
        row=8, column=0, columnspan=3, padx=12, pady=(4, 2))

    # ── Save handler ──────────────────────────────────────────────────────────
    def on_save():
        global SAVE_FOLDER, INTERVAL, RETAIN_DAYS, START_WITH_WINDOWS
        folder_raw   = folder_var.get().strip()
        interval_str = interval_var.get().strip()
        retain_str   = retain_var.get().strip()
        errors = []

        folder = os.path.expanduser(folder_raw)
        if not folder:
            errors.append("• Save Folder cannot be empty.")
            folder_entry.config(bg=CLR_FIELD_ERR)
        else:
            folder_entry.config(bg='white')

        try:
            interval = int(interval_str)
            if interval < 1:
                raise ValueError
            interval_entry.config(bg='white')
        except ValueError:
            errors.append("• Interval must be a whole number ≥ 1  (e.g. 30).")
            interval_entry.config(bg=CLR_FIELD_ERR)
            interval = None

        try:
            retain = int(retain_str)
            if retain < 1:
                raise ValueError
            retain_entry.config(bg='white')
        except ValueError:
            errors.append("• Retain Days must be a whole number ≥ 1  (e.g. 5).")
            retain_entry.config(bg=CLR_FIELD_ERR)
            retain = None

        if errors:
            error_var.set("\n".join(errors))
            return

        error_var.set("")

        if not os.path.exists(folder):
            if messagebox.askyesno(
                    "Create Folder",
                    f"The folder does not exist:\n  {folder}\n\nCreate it now?",
                    parent=win):
                os.makedirs(folder, exist_ok=True)
            else:
                return

        startup = startup_var.get()
        SAVE_FOLDER  = folder
        INTERVAL     = interval
        RETAIN_DAYS  = retain
        START_WITH_WINDOWS = startup
        _save_config(folder, interval, retain, startup)
        _set_autostart(startup)
        _settings_event.set()   # wake the screenshot loop so new settings apply immediately
        win.destroy()

    # ── Buttons ───────────────────────────────────────────────────────────────
    btn_frame = tk.Frame(win)
    btn_frame.grid(row=9, column=0, columnspan=3, pady=(6, 14))
    tk.Button(btn_frame, text="Save",   command=on_save,        width=10, font=FONT).pack(side='left', padx=8)
    tk.Button(btn_frame, text="Cancel", command=win.destroy,    width=10, font=FONT).pack(side='left', padx=8)

    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    w,  h  = win.winfo_width(),       win.winfo_height()
    win.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
    win.mainloop()


# --- About window ---
def _show_about():
    win = tk.Tk()
    win.title("About Sardine Shot")
    win.resizable(False, False)
    win.attributes('-topmost', True)

    FONT = ('Segoe UI', 9)
    frame = tk.Frame(win, padx=32, pady=20)
    frame.pack()

    tk.Label(frame, text="Sardine Shot",
             font=('Segoe UI', 16, 'bold')).pack()
    tk.Label(frame, text=f"Version {APP_VERSION}",
             font=('Segoe UI', 9), fg='#666666').pack(pady=(0, 4))
    tk.Label(frame, text="Automatic periodic screenshot utility — Sardine Shot",
             font=FONT).pack()

    tk.Frame(frame, height=1, bg='#cccccc').pack(fill='x', pady=12)

    tk.Label(frame, text=f"Created by {AUTHOR_NAME}", font=FONT).pack()

    def _link(text, url, color):
        lbl = tk.Label(frame, text=text,
                       font=('Segoe UI', 9, 'underline'),
                       fg=color, cursor='hand2')
        lbl.pack(pady=2)
        lbl.bind('<Button-1>', lambda _e: webbrowser.open(url))

    _link("LinkedIn Profile",   LINKEDIN_URL, '#0077b5')
    _link("GitHub Repository",  GITHUB_URL,   '#1a7f37')

    tk.Frame(frame, height=1, bg='#cccccc').pack(fill='x', pady=12)
    tk.Button(frame, text="Close", command=win.destroy,
              width=10, font=FONT).pack()

    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    w,  h  = win.winfo_width(),       win.winfo_height()
    win.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
    win.mainloop()


# --- Tray callbacks ---
def on_quit(icon, item):
    _stop_event.set()
    icon.stop()
    _action_queue.put(None)   # wake up the main loop so it can exit cleanly


def on_toggle_pause(icon, item):
    global _paused
    _paused = not _paused


def on_open_folder(icon, item):
    os.startfile(SAVE_FOLDER)


def on_settings(icon, item):
    _action_queue.put('settings')


def on_about(icon, item):
    _action_queue.put('about')


def is_paused(item):
    return _paused


def _first_run_prompt():
    """Ask the user about autostart on first run (START_WITH_WINDOWS is None)."""
    global START_WITH_WINDOWS
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    answer = messagebox.askyesno(
        "Sardine Shot",
        "Would you like Sardine Shot to start automatically with Windows?",
        parent=root,
    )
    root.destroy()
    START_WITH_WINDOWS = answer
    _save_config(SAVE_FOLDER, INTERVAL, RETAIN_DAYS, answer)
    _set_autostart(answer)


if __name__ == "__main__":
    # First-run: ask about autostart if the setting doesn't exist yet
    if START_WITH_WINDOWS is None:
        _first_run_prompt()

    # Screenshot worker — reads globals so live settings changes take effect
    threading.Thread(target=screenshot_loop, daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("Pause",       on_toggle_pause, checked=is_paused),
        pystray.MenuItem("Open Folder", on_open_folder),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Settings",    on_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("About",       on_about),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit",        on_quit),
    )
    icon = pystray.Icon("sardine_shot", create_tray_icon(), "Sardine Shot", menu)

    # Run pystray in a background thread; main thread hosts tkinter windows.
    threading.Thread(target=icon.run, daemon=True).start()

    while not _stop_event.is_set():
        try:
            action = _action_queue.get(timeout=0.2)
            if action == 'settings':
                _show_settings()
            elif action == 'about':
                _show_about()
            elif action is None:
                break
        except queue.Empty:
            continue
