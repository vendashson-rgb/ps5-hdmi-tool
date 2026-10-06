# PS5 HDMI Tool

🌐 **[Ler em português](README.md)**

Developed by **DatZero Foundation** — [datzerogames.com.br](https://datzerogames.com.br/)
Lead technician: **Jefferson Honorio**

🔗 **[Project website](https://vendashson-rgb.github.io/ps5-hdmi-tool/)**

![PS5 HDMI Tool main screen](docs/assets/screenshot.png)

## 🎯 What it does

**PS5 HDMI Tool** is a software tool that **patches the `.bin` NOR flash
image of a PS5 Slim motherboard**, making it possible to install a
**Nuvoton (MN864739)** HDMI chip on boards that originally require a
**Realtek (RTD2175P)** HDMI chip — and vice-versa. In short: it's a PS5 Slim
HDMI chip conversion/swap tool via component reuse, an alternative for when
the original Realtek chip is out of stock or hard to source on the
replacement-parts market.

This tool is the **software** side of the process. The physical side (the
actual chip swap via rework/microsoldering) is done with the
**[DatZero Interposer](docs/GUIA_INSTALACAO_INTERPOSER.md)** — see the full
physical installation guide, with tool list and step-by-step photos
(currently Portuguese only). The program and the Interposer are
complementary: the Interposer handles the electrical/physical side of the
HDMI chip (including a dedicated voltage regulator, see the guide), and PS5
HDMI Tool handles the NOR side (reading, writing and converting the board's
firmware for the new chip).

**Related search terms:** PS5 HDMI chip repair, PS5 board no video/no
signal fix, PS5 HDMI chip swap, Realtek RTD2175P out of stock, replace
RTD2175P with MN864739, Nuvoton MN864739 instead of Realtek, CH341A PS5
programmer, PS5 NOR flash read/write, PS5 NOR patch tool, PS5 Slim HDMI
interposer.

**Tested with real hardware:** CH341A reader tested on the bench — NOR read
and write confirmed working correctly (confirmed by the project's creator).

## ⬇️ Download

**[Download the installer (.exe) — latest release](https://github.com/vendashson-rgb/ps5-hdmi-tool/releases/latest)**

Download `PS5_HDMI_Tool_Setup.exe` from the releases page above and run it
— it installs the program and the CH341A reader driver automatically (asks
for administrator permission to do so). No need to install Python or
anything else.

Once installed, the program itself checks on its own (a few seconds after
opening) whether a newer version has been published on GitHub — if so, it
shows a prompt asking whether to download and install it now; if you
accept, it downloads the new installer, opens it, and closes itself, with
nothing to manually download again. A network failure during this check
is silently ignored (it doesn't affect normal use of the program).

A tool to read/write the NOR flash of PS5 Slim boards via a CH341A reader,
verify the read, save automatic backups, show board information (installed
HDMI chip, MAC, identification data) and apply the HDMI chip conversion
patch (Realtek ⇄ Nuvoton/Panasonic).

This tool is the **software** side of the HDMI chip conversion. To do the
physical chip swap on a real board using the **DatZero Interposer**, see
**[docs/GUIA_INSTALACAO_INTERPOSER.md](docs/GUIA_INSTALACAO_INTERPOSER.md)**
(Portuguese only for now) — a guide for advanced bench/microsoldering
technicians, with the tool list, chip-location photos and the full
procedure.

**About the checksum at 0x1C41FE-0x1C41FF:** we discovered it's a fixed
lookup table keyed by (HDMI chip + Wi-Fi module revision), it does not
depend on the MAC — see `NOTES.md`. It's only resolved for combinations
already seen in real samples; for a new combination the program warns and
keeps the old value — in that case, write **only to a bench/test board**,
never to a customer's board, until a real sample confirms the correct
value.

## Program language

The program has three small flags in the top-right corner (🇧🇷/🇺🇸/🇪🇸) —
click one to switch the interface language instantly, no restart needed:
**Portuguese, English or Spanish**. The whole interface (buttons, tabs,
confirmation/error messages and the activity log) is translated — see
`i18n.py`.

## ⚠️ 32-bit vs 64-bit issue (read before running)

The `CH341DLL.dll` used by the CH341A reader only exists in a **32-bit**
version (confirmed: neither Windows nor the driver ship a 64-bit version of
it). If you run this program with a 64-bit Python (the most common one
nowadays), it will fail to load the DLL.

**Solution: install a 32-bit Python, just to run this program.**

1. Go to https://www.python.org/downloads/windows/ (official site).
2. Download the **"Windows installer (32-bit)"** of a 3.11.x version (or
   close to the one you already have).
3. Run the installer. You can install it normally, without uninstalling the
   64-bit Python you already have — both coexist.
4. After installing, open a **new** PowerShell in the program's folder and
   run:
   ```
   py -0p
   ```
   This should list two Python versions, one marked as 32-bit.
5. Run the program specifying the 32-bit version, for example:
   ```
   py -3.11-32 main.py
   ```
   (the exact name depends on what showed up in step 4 -- it may be
   `-3.11-32` or something similar).

If `py -0p` doesn't show any 32-bit version even after installing, let me
know what showed up and I'll help identify the right path to the 32-bit
`python.exe` to run it directly.

## Requirements

1. **Python 3.10+** installed (includes Tkinter by default in the official
   Windows installer).
2. **CH341A reader driver installed.** The driver files are already inside
   this program's `drives/` folder (`CH341WDM.INF/.SYS/.CAT`,
   `CH341W64.SYS`, `CH341DLL.dll`). If NeoProgrammer already works on your
   machine, the driver is already installed and you can skip this step.
   Otherwise:
   - Connect the CH341A reader via USB.
   - Open Device Manager; if it shows up with a yellow warning/question
     mark, right-click → **Update driver** → **Browse my computer for
     drivers** → point to this program's `drives/` folder.
   - See `drives/CH341A_install.png` as a visual reference for the
     installation.
3. **Python libraries** (Pillow for the animations, pyserial for the UART
   tab, hidapi for the controller test tab). Install with:
   ```
   pip install -r requirements.txt
   ```
   (if you're using the 32-bit Python because of `CH341DLL.dll`, see the
   section above, run this command with
   `py -3.11-32 -m pip install -r requirements.txt`).
4. **USB-serial adapter** (optional, only for the "UART Reader" tab)
   connected to the board's debug pins. Check the adapter's voltage before
   connecting.
5. **DualSense controller** (optional, only for the "Controller Test" tab)
   connected via USB cable.

## How to run

```
cd ps5-hdmi-tool
python main.py
```

## Building the installer (to hand the user a one-click install)

The recommended way to deliver the program is the **installer** (not the
standalone `.exe`) — it solves the problem of the CH341A driver not being
auto-detected on another machine: it installs the program AND registers the
driver directly in Windows (via `pnputil`, which ships with Windows),
without the user needing to open Device Manager.

Step by step (after generating the `.exe`, section below):

```
"C:\Users\<you>\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

(first time: install Inno Setup — `winget install JRSoftware.InnoSetup` —
it's free and it's only the build tool, the end user doesn't need it)

This generates `installer_output\PS5_HDMI_Tool_Setup.exe` — that's the
single file you send to the user. When run, it:

1. Asks for administrator permission (normal — needed to install the driver
   and copy to Program Files).
2. Installs the program in `Program Files\PS5 HDMI Tool\`.
3. Registers the CH341A reader's driver in Windows automatically — the next
   time the reader is connected to any USB port, Windows recognizes it on
   its own, no folder pointing needed.
4. Creates a desktop and Start Menu shortcut.
5. Offers to open the program at the end.

**No need to install Python on the user's machine** — the `.exe` already
carries Python embedded (built with PyInstaller, "onedir" mode — a folder
with the `.exe` and its supporting files, not a single `.exe`; onedir
opens much faster than onefile, which has to unpack itself to a temp
folder every single time it runs).

**DualSense controller (the "Controller Test" tab):** no separate driver
needed — it's a standard USB HID device, and Windows has always had native
support for that (same category as keyboard/mouse). Just plug the USB cable
in and use it.

NOR backups (`database/backups/`) now live in
`%LOCALAPPDATA%\PS5 HDMI Tool\` (not next to the `.exe`) — this avoids a
silent permission failure when the program is installed in Program Files
(a regular user doesn't have write permission there without admin rights).

## Building the .exe (used by the installer above, or to test standalone)

Built with PyInstaller, from the same 32-bit Python used to run the program
(it needs to be 32-bit because of `CH341DLL.dll`):

```
py -3.11-32 -m pip install pyinstaller
py -3.11-32 -m PyInstaller PS5_HDMI_Tool.spec
```

(first time, if the `.spec` doesn't exist yet, use the full command:
`py -3.11-32 -m PyInstaller main.py --name "PS5_HDMI_Tool" --onedir --icon images/icon.ico --add-data "images;images" --add-data "drives;drives"`
— do **not** use `--onefile`: it makes the program much slower to open,
since it has to unpack itself to a temp folder every single time)

The final `.exe` lands in `dist/PS5_HDMI_Tool/PS5_HDMI_Tool.exe`, inside a
folder with its supporting files (`_internal/` etc.) — it's that whole
folder that needs to be copied/distributed together, not just the `.exe`
alone. To run it this way directly (without the installer), also copy the
`drives/` folder into `dist/PS5_HDMI_Tool/` — if Windows doesn't
auto-detect the CH341A reader, point Device Manager manually to that
folder. **To deliver to an end user, always prefer the installer** (section
above) — it already takes care of the driver on its own.

The `.exe` runs with just the program's window (`console=False` in the
`.spec`) — no console/black window alongside it. Since there's no console
to show errors on screen, any unhandled exception is automatically logged
to `%LOCALAPPDATA%\PS5 HDMI Tool\crash.log` (see `main.py`) and also shows
an on-screen notice pointing to where to look — so you can still debug
issues even without the visible console.

## Usage flow

1. Connect the CH341A reader with the NOR in the socket/clip.
2. Click **"1. Detect CH341A reader"**. The program reads the flash chip's
   JEDEC ID and identifies whether it's the Winbond W25Q16JV (2 MB)
   expected on PS5 boards — if it's a different Winbond model or a
   different manufacturer, it warns in the log so you can check it's the
   right chip before proceeding.
3. Click **"2. Read NOR"**. The program:
   - Reads the whole NOR twice and compares byte by byte.
   - If the two reads don't match, it warns and **doesn't** save anything —
     redo the reader's contact and try again.
   - If they match, it checks whether the content is actually a PS5 NOR: if
     it comes back 100% blank (0xFF), it warns that there's probably no NOR
     in the socket/clip (bad contact); if it has data but doesn't have a
     PS5 NOR signature, it warns that it's corrupted or a different kind of
     chip. In both cases, it **doesn't** save anything and doesn't treat it
     as a valid read.
   - If they match and it's a valid PS5 NOR, it saves both reads to
     `database/backups/<console_identifier>/DUMP1.bin` and `DUMP2.bin` and
     shows the board's information. Each console has its own subfolder (a
     new read of the same console overwrites the previous
     `DUMP1.bin`/`DUMP2.bin`).
4. Click **"Preview changes"** (step 3) to see the HDMI chip conversion
   patch — this also saves the already-converted result in the same
   console folder, as `REALTEK_FOR_NUVOTON.bin` (or
   `NUVOTON_FOR_REALTEK.bin`, depending on the conversion direction).
4b. **"Use donor file..."** (next to step 3): an alternative for when you
   already have a complete donor `.bin` file (2 MB) from another console,
   already set up with the right HDMI chip and board family — the program
   reuses the information from the console you just read (serial number and
   MAC addresses) and writes it on top of the donor file, keeping the rest
   of it as-is. It shows the detected chip/family from the donor file and
   asks for confirmation before proceeding — check that they match what you
   intend to install. Then just click "Write to NOR" as usual.
5. To write any valid 2 MB `.bin` to the connected NOR — a previously saved
   backup, or a file converted in the "Analyze file (.bin)" tab (chip patch,
   donor file, console type) — use the **"Load .bin file to write..."**
   button. It's available as soon as the reader is detected (no need to
   read the board first). It only checks the size (2 MB) and the PS5 NOR
   signature there; the program then loads the file and shows all its
   information, just like it already does after reading the real board — it
   does **not** write anything yet. The write only happens when you click
   **"4. WRITE TO NOR"**, same as the normal read+preview flow.
6. When you click **"4. WRITE TO NOR"**, if you haven't made any backup in
   this session yet (neither via step 2, nor by loading a file without
   reading the board first), the program warns that, without a backup, the
   write will be irreversible, and offers to make an automatic backup now
   (two reads of the current NOR) before continuing.
7. **"Restore NOR from Backup"**: writes back, with the same double
   confirmation, the last backup made in this session (from step 2, or the
   automatic one offered in step 6). If no backup has been made yet, it
   warns instead of trying to write.

## "Analyze file (.bin)" tab

Does not depend on the CH341A reader being connected. Lets you pick any
2 MB `.bin` saved on the PC (from an old backup, another tool, etc.),
analyzes it right away (HDMI chip, MAC, CFI, etc.) and lets you preview and
save a new file with the patch already applied — without touching any
board.

If the analyzed file is from a board family with a matching donor file
available (e.g. EDM-04X, EDM-05X), the **"Use automatic donor file"**
button becomes enabled: the program already knows which donor file to use
for that family, reuses the serial number and MAC addresses from the opened
file, and writes them on top of the donor file automatically (same logic as
the "Use donor file..." button in the hardware tab, except it picks the
right donor file on its own instead of asking you to select one).

If the file is corrupted or completely blank (a read that captured no data
at all — the program clearly flags this in the log) and the board family
can't be auto-detected because of that, use the **"Regenerate with donor
file..."** button instead: you pick the right donor file manually (by the
model printed on the board itself), and the program writes only the fields
it can actually reuse from the original file on top of it — fields with no
valid data are left exactly as they were in the donor file instead of being
wiped out.

**Convert console type (Disk / Digital / Slim Edition)**: a field the
system uses to decide whether it requires the physical disc drive.
Mainly useful for "Fat" PS5 units (EDM-01X to EDM-03X) with a broken disc
drive — since it's paired with the APU and can't be swapped for another
one, converting the console to "Digital" makes the system stop requiring
it so updates work again. Pick the target type from the dropdown and
click "Convert"; the result needs to be saved ("Save NOR with patch..."
button) and written to a bench/test board before trusting it with a
customer.

## "UART Reader" tab

Captures the raw log from a USB-serial adapter connected to the board's
debug pins, to help pull up error codes on consoles that won't power on.
**It does not interpret or translate the codes** — it only shows the raw
text (automatically coloring lines that look like errors/warnings/success,
by keyword) and lets you save the captured log to `.txt`. Default baud:
115200 (the most common for UART debug) — if nothing readable comes
through, try other values in the baud menu.

**"Read error codes"**: once connected, actively sends the `errlog N`
command (N from 0 to 10) to the console, to query the error codes already
stored without needing to power-cycle and capture the whole boot. **"Clear
error codes on console"** sends `errlog clear` (asks for confirmation —
erases the console's stored history, cannot be undone). Protocol verified
against the source code of [PS5 NOR Modifier](https://github.com/TheCod3rYouTube/PS5NorModifier)
(TheCod3r) — **not yet tested with real hardware in this project**. If
there's no response at all, check the baud rate and pinout before
suspecting the command itself.

Check the adapter's voltage
before connecting (many embedded boards use 3.3V TTL).

## "Controller Test" tab

**Native** DualSense/DualSense Edge controller test (no internet, no
browser — inspired by dualshock-tools.github.io, but read directly via HID
inside the program). Connect the controller via **USB cable**, click
"Detect controller" and then "Connect". Shows in real time:

- Position of both sticks (dot + raw values — useful to detect *drift*).
- A **controller diagram** that lights up green for each
  button/trigger/D-pad/touchpad as it's pressed (triggers show the pressure
  percentage).
- Touchpad (up to 2 finger dots), battery, vibration test and light bar
  test (colors).
- **Stick calibration** (center and range), written directly to the
  controller's memory — the same feature as dualshock-tools.github.io.
  Click "Calibrate center" (release the sticks first) or "Calibrate
  range..." (rotate both sticks in full circles when prompted). Changes
  only become permanent after you click "Save changes permanently" — until
  then you can test and back out without risk.

**Confidence level:** sticks/triggers/buttons/D-pad/vibration/light
bar/calibration were checked directly against the real source code of two
open-source projects (pydualsense and dualshock-tools.github.io, both MIT)
— high confidence, but **not yet tested with a real controller in this
project**. Touchpad and battery are the fields most sensitive to firmware
variation. Test it with your controller and let me know exactly what
worked or came out wrong, so I can adjust the offsets.

## ✅ Tested with real hardware

The CH341A communication layer (`ch341_spi.py`) has been validated on the
bench with a real CH341A reader: **NOR read and write confirmed working
correctly**.

## Project structure

Program code (at the root):
- `nor_parser.py` — interprets the NOR's content (chip, MAC, etc.). Tested against 6 real dumps.
- `nor_patcher.py` — generates the Realtek ⇄ Nuvoton/Panasonic conversion patch.
- `ch341_spi.py` — communication with the CH341A reader (**tested and confirmed with real hardware** — NOR read and write working).
- `uart_reader.py` — serial/UART port capture ("UART Reader" tab). **Not yet tested with a real adapter.**
- `dualsense.py` — raw-HID DualSense controller read/test ("Controller Test" tab). **Not yet tested with a real controller.**
- `gif_anim.py` — GIF animation player used in the interface (lazy loading — only decodes a stage's frames the first time it's actually shown).
- `i18n.py` — interface translations (Portuguese/English/Spanish) and the active-language switcher.
- `version.py` — current version number (single source of truth, used by the update check).
- `updater.py` — checks for and downloads updates via GitHub Releases.
- `gui.py` — graphical interface (Tkinter).
- `main.py` — entry point (`python main.py`).
- `requirements.txt` — Python dependencies (Pillow, pyserial, hidapi).
- `NOTES.md` — map of confirmed offsets and open items.
- `PS5_HDMI_Tool.spec` — PyInstaller recipe to generate `dist/PS5_HDMI_Tool/` (onedir).
- `installer.iss` — Inno Setup recipe to generate the final installer (`installer_output/PS5_HDMI_Tool_Setup.exe`), from the already-built `.exe`.
- `docs/GUIA_INSTALACAO_INTERPOSER.md` — DatZero Interposer physical installation guide (hardware rework, not about the program; Portuguese only for now). `docs/assets/` has the images used in it (tools, interposer, chip location on the board).

Support folders (everything the program needs to run on the user's machine):
- `images/` — logo, icon and all the animations (`.gif`) shown in the interface.
  `images/controller/` has the controller diagram (background + one
  transparent cutout per button) used in the "Controller Test" tab.
  `images/flags/` has the small flags (pt/en/es) for the language switcher.
- `drives/` — the CH341A reader's driver (`CH341WDM.*`, `CH341W64.SYS`) and
  the `CH341DLL.dll` used by the program to talk to the reader. The
  installer registers this driver automatically in Windows (see "Building
  the installer" above) — no separate driver needed for the DualSense
  controller (it's standard USB HID, natively supported by Windows).
- `database/backups/<console_identifier>/` — one subfolder per console (by
  the identifier read from the NOR itself), containing `DUMP1.bin` (1st
  read), `DUMP2.bin` (2nd read, for verification) and, after previewing a
  patch, `REALTEK_FOR_NUVOTON.bin` or `NUVOTON_FOR_REALTEK.bin` (the
  already-converted NOR). Real location at
  `%LOCALAPPDATA%\PS5 HDMI Tool\database\backups\` when installed via the
  installer.

Development scripts (not needed for the end user to run the program, only
for whoever is developing/debugging):
- `dev_tools/test_parser_manual.py` — quick check of the parser against already-collected dumps.
- `dev_tools/verify_patch_against_real.py` — validates the patch against a known real conversion.
- `dev_tools/find_wifi_rev.py` / `dev_tools/search_version.py` — offset research scripts.
- `dev_tools/diag_find_chunk.py` — finds the SPI transfer block size that works with the reader.
- `dev_tools/make_icon.py` — generates `images/icon.ico` from `images/logo.png`.
- `dev_tools/build_flags.py` — generates `images/flags/*.png` (language switcher flags).
- `dev_tools/build_controller_diagram.py` — generates `images/controller/*.png` (controller diagram)
  from the real DualSense SVG used by dualshock-tools.github.io
  (`dev_tools/assets_src/dualsense-controller.svg`, MIT). Only needs to be rerun if the source SVG
  changes — requires `pip install -r dev_tools/requirements-dev.txt` (not a dependency of the final program).
