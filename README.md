# Sardine Shot

A lightweight Windows app that runs openly in the system tray and takes periodic screenshots, saving them to a folder of your choice — including a **cloud storage folder** (Dropbox, Google Drive, OneDrive, etc.) so you can check in from anywhere, for free.

## Why I built this

We use **Microsoft Family Safety** to filter content and get basic activity reports on our kid's computer. It works great, but it doesn't have a "take a screenshot every few minutes" feature. We didn't want to install yet another monitoring app with subscriptions, accounts, or bloatware.

So I built this: a tiny, single-file app that just takes screenshots on a schedule and drops them into a folder. The key insight is simple — point the save folder at your **cloud storage folder** and the screenshots sync to your phone or any browser automatically. No extra accounts, no servers, no monthly fees.

If the name seems oddly specific: I had a vacation in **Moalboal**, loved the place, and apparently came back so charmed by the sardines there that even this app ended up named after them.

It is not designed to be stealth software. It sits in the tray, can be paused or quit from the tray menu, and is best used on devices you own or administer with clear notice to the people using them.

## Other legitimate uses

Besides parental monitoring on a family computer, there are a few transparent, practical uses for a tool like this:

- **Shared family PC check-ins**: keep a lightweight visual log on a computer used by multiple family members, especially in common areas.
- **Caregiver or elder-tech support**: with consent, help a parent or relative who struggles with computers by keeping a simple screenshot trail you can review later.
- **Classroom or lab supervision**: on school or training machines, keep a visible record of activity when users have been clearly informed.
- **Kiosk or reception PCs**: verify that a public-facing machine stayed on the expected app or webpage throughout the day.
- **Remote troubleshooting**: capture “what the screen looked like” during an intermittent issue that is hard to reproduce live.
- **Workflow time-lapse / progress log**: create a visual history of a long-running task on screen, such as uploads, renders, dashboards, or unattended jobs.
- **Personal accountability**: keep a record of your own work or study sessions on your own computer without using a cloud monitoring service.
- **Small office shared terminals**: add a lightweight audit trail on front-desk or shared-use PCs without installing a full device management platform.

## Transparency matters

This app makes the most sense when it is used openly:

- on a computer you own, manage, or have permission to administer
- with clear notice to the person using the machine
- as a simple local screenshot tool, not as covert surveillance
- with the tray icon left visible so people know it is running

## Features

- Runs in the **system tray** / systray (notification area) — no main window, no taskbar clutter
- Takes a screenshot every N seconds (configurable)
- Saves screenshots as timestamped `.png` files
- Automatically **deletes old screenshots** after a set number of days (keeps disk space tidy)
- Configure save folder, interval, and retention from the built-in **Settings** window
- Pause / Resume without quitting
- Quit completely from the tray menu when you want to close the app
- Open the screenshots folder directly from the tray icon
- Single `.exe` — no Python installation required on the target machine

## Screenshots

### Tray menu

![Sardine Shot tray menu](screenshots/Screenshot%202026-04-02%20231004.png)

`Pause` temporarily stops taking screenshots but keeps the app running in the tray.
`Quit` closes the app completely.

### Settings window

![Sardine Shot settings window](screenshots/Screenshot%202026-04-02%20231053.png)

## Setup

### Option A — Use the pre-built EXE

1. Download `sardine_shot.exe` from the [Releases](../../releases) page.
2. Place `sardine_shot.exe` and `config.ini` in the same folder.
3. Double-click `sardine_shot.exe` — a camera icon appears in your system tray.
4. Right-click the tray icon and open `Settings` to choose:
  - the save folder
  - the screenshot interval in seconds
  - how many days to retain screenshots
5. Click `Save`. The app updates its configuration immediately.

To make it start automatically with Windows, create a shortcut to the `.exe` and place it in:
```
shell:startup
```
(Press `Win + R`, type `shell:startup`, press Enter.)

### Option B — Run from source

```bash
pip install pillow pystray
python sardine_shot.py
```

## Configuration

You normally do **not** need to edit `config.ini` by hand anymore.
Use the tray icon and open `Settings` to manage the app's configuration in a small form.

The settings window lets you update:

- `save_folder`: where screenshots are stored
- `interval`: how often a screenshot is taken, in seconds
- `retain_days`: how long screenshots are kept before auto-delete

When you click `Save`, the app writes those values into `config.ini` next to the `.exe` or script and applies them immediately.

If you still prefer manual editing, the file format is:

```ini
[Settings]
; Folder where screenshots are saved.
; Point this at your cloud storage folder to sync screenshots automatically.
; Examples:
;   ~/Dropbox/kids-pc
;   ~/Google Drive/My Drive/kids-pc
;   ~/OneDrive/kids-pc
save_folder = ~/Pictures/Screenshots

; Seconds between screenshots (default: 30)
interval = 30

; Days to keep screenshots before auto-deleting (default: 5)
retain_days = 5
```

> **Tip for parents:** Set `save_folder` to a subfolder inside your Dropbox, Google Drive, or OneDrive folder on the child's PC. Screenshots will sync to your phone or any browser within seconds — no setup on your end beyond signing in to the cloud storage app.

## Building the EXE yourself

Requirements: Python 3.x, `pip install pillow pystray pyinstaller`

```powershell
.\build.ps1
```

The output is a single, self-contained `dist\sardine_shot.exe` — no Python needed on the target machine.

## Project structure

```
sardine_shot.py         # Main application
config.ini              # User configuration
sardine_shot.spec       # PyInstaller build spec
build.ps1               # Build script (Windows PowerShell)
```

## Dependencies

| Package | Purpose |
|---|---|
| [Pillow](https://python-pillow.org/) | Screen capture and image saving |
| [pystray](https://github.com/moses-palmer/pystray) | System tray icon and menu |

## License

[MIT](LICENSE)
