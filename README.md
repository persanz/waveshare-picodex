# Waveshare PICODEX

A standalone, offline Pokémon picture book for the **Waveshare
RP2350-Touch-LCD-1.54**, running MicroPython 1.29. A Pokémon logo and Poké Ball splash shows `Loading....` for five seconds,
then opens the first Pokémon: **no launcher, no app selection, no Virtual Pokemon**.

Includes 1,538 high-resolution 240 × 240 artwork entries, Spanish descriptions,
touch and button controls, motion shuffle, charging display and shutdown screen.

## Controls

- **Left/right third of the screen:** previous/next Pokémon.
- **Left/right hardware button, short press:** previous/next Pokémon.
- **Hold the centre of the artwork for about one second:** read its description.
- **Tap a description:** advance a page; tap the final page to return to the
  exact same artwork. Movement pauses while reading.
- **Hold the right button for two seconds:** return to the first Pokémon.
- **Move gently:** choose a different random Pokémon. Let the device settle
  before shaking again; continuous shaking does not repeatedly change it.
- **Hold the left button for about two seconds:** show `GOODBYE!` and switch off
  on battery. USB can keep the device powered after its screen goes black.

Power-on starts from the first entry. There is no menu to return to, no pet
state or care meters. The startup splash leads straight into PICODEX.

## Files and setup

This is a separate project derived from
[persanz/waveshare-pokemon-frame](https://github.com/persanz/waveshare-pokemon-frame),
commit `75f1b3cf5468c2704ef5b6ba3272d236e745763c`. The source project remains unchanged.

Use MicroPython **1.29, mpy format v6.3**. The board must have a FAT-formatted
microSD card. Place the included `pokemon_hd.dat` on the card at:

```text
/waveshare_pokemon_frame/pokemon_hd.dat
```

The original folder name is retained so an existing artwork SD card can be
reused unchanged. The firmware mounts it at `/sd`.

Copy these files to the board root:

```text
main.py
boot_splash.mpy
boot_splash.dat
lcd.mpy
frame_app.mpy
dex_description.mpy
power_screen.mpy
charge_overlay.mpy
shutdown_screen.mpy
sdcard.mpy
pokemon_order.bin
pokemon_dex.bin
pokemon_descriptions_es.bin
```

The `lcd.py` source is the preserved Waveshare board driver from the original
project's local board backup. Its compiled module is supplied too. An existing
working `lcd.py` on the board can remain; the firmware uses its `LCD_1inch54` API.
The artwork archive belongs on the SD card, not in the board's internal flash.

Find the port with `uv tool run mpremote connect list`. Back up the current board
files before replacing them. A hardware reset clears an existing watchdog;
interrupt startup before transferring large files. Stage files under temporary
names and verify their SHA-256 checksums before renaming them to activate a set
of changes. Activate `main.py` last, then reset the board.

This repository does not automatically install itself or remove files from an
existing two-app board. The old launcher and companion modules are unused by the
new `main.py`; they do not need to be deleted to run this version.

## Build and checks

The matching `.mpy` firmware modules are included. Rebuild on the host with:

```sh
for module in boot_splash lcd frame_app dex_description power_screen charge_overlay shutdown_screen sdcard; do
  uv tool run --from mpy-cross mpy-cross "$module.py"
done
python3 -m unittest discover -s tests -v
python3 validate_assets.py
```

`main.py` remains source. Allocate the 115,200-byte display buffer before loading
the app; `gc.threshold(1024)` and compiled modules are important for heap space.
The display uses byte-swapped RGB565 (for example red is `0x00f8`).

Rebuild the Spanish binary database from its included JSON with:

```sh
python3 build_descriptions.py
```

The JSON retains per-entry translation provenance. Artwork archive format:
32-bit entry count, then 16-byte entries `(art_id, offset, compressed_size,
name_offset)`; bodies are raw DEFLATE with a 1 KiB window, yielding 115,200 bytes
of RGB565 data. `pokemon_order.bin` maps National Pokédex order to archive indices;
`pokemon_dex.bin` maps alternate-form IDs to displayed species numbers.

Hardware regression scripts in `tests/hardware_description_*.py` use simulated
inputs with a real board, LCD and SD card. Compile and upload them as `.mpy`
modules before importing them. Host tests do not substitute for physical touch,
button, SD-card and power checks. The standalone firmware has been installed on the board. Simulated-input
on-board checks passed for byte-identical description return and shutdown
control flow despite failing touch reads. Physical power cutoff requires owner
handling.

## Charging display and known limitations

The shared charging overlay is retained from the source project. It shows a
large voltage-derived percentage in a red/orange/green ring. Tap anywhere to
return to the exact previous artwork or description page. It saves a temporary
framebuffer in internal flash instead of allocating a second one in RAM.

**Open issue inherited from the source:** the screen can also appear during a
battery-only power-on. GPIO17 is a board-specific indication, not a dedicated
VBUS sensor. A recorded USB cable cycle showed high/low/high, but the 700 ms
startup rule is not a reliable proof of external power. Dismissal lasts while
high; 1,500 ms low re-arms it. Further battery-only startup measurements are
needed. No GPIO is guessed or repurposed in this derivative.

`power_screen.py` retains temporary boot logging to `/bootlog.csv`: at most once
per 250 ms during the first 15 seconds after module load, with an approximately
1,500-byte cap. It writes flash and should be removed when the startup issue is
resolved. The diagnostic log is not part of the repository.

GPIO29 uses the original 3:1 divider and nominal 3.3 V ADC reference. The display
curve maps the observed approximately 4.02 V plateau to 100%; that is an empirical
display adjustment, not a multimeter calibration or proof of full charge. Other
curve points are also estimated. Invalid readings show `--%`. An absent battery
with a plausible charger voltage cannot reliably be identified. USB presence
alone never sets the percentage to 100%.

Description return restores a flash-backed artwork snapshot, avoiding the
previous low-memory decompression failure. Power handling precedes touch
rendering, and shared I2C reads have a 50 ms timeout.

## Rebuild the startup splash

The original splash assets and attribution are in `assets/splash/`. To rebuild:

```sh
uv run --with pillow --with resvg-py python build_boot_splash.py
```

The splash reuses the existing framebuffer and its module is unloaded before
PICODEX imports, preserving heap space for artwork. Missing or incomplete
splash data is logged and PICODEX still starts. On-board startup verification
confirmed a 5,003 ms splash followed by the first artwork, with no menu.

## Sources and rights

Artwork and names originate from PokeAPI's official-artwork collection. Spanish
text and translation provenance are retained from the source project. The SD
and Waveshare display driver sources retain their existing notices. No new
license grant is asserted over upstream material. Pokémon artwork, names and
trademarks belong to their respective owners.
