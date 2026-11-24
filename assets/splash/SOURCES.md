# Splash image sources

- International Pokémon logo: https://commons.wikimedia.org/wiki/File:International_Pok%C3%A9mon_logo.svg — Nintendo / Creatures / Game Freak; Commons lists PD-textlogo with trademark restrictions.
- Poké Ball icon: https://commons.wikimedia.org/wiki/File:Pok%C3%A9_Ball_icon.svg — Andreuvv, CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).

The icon and logo were downloaded, resized and composed on a new background for this splash. The composed artwork is distributed under CC BY-SA 4.0, with the original logo/trademark status retained. Source SVG files are preserved here. Rebuild with build_boot_splash.py; boot_splash.dat is 240×240 big-endian RGB565 for the display driver. Loading.... is drawn by firmware.

## Animated Poké Ball (startup and shutdown)

- **Pokeball**, Zel-Duh (2013): https://www.deviantart.com/zel-duh/art/Pokeball-349366267
- Original 260×250, 15-frame GIF retained as `zel-duh-pokeball.gif`, obtained through DeviantArt's public oEmbed response for that exact artwork.
- `build_pokeball.py` composites transparency over black, resizes to 128×123, retains every frame and original duration, and writes big-endian RGB565 to `pokeball.dat`. No new rights or permissive license are asserted over this GIF; copyright remains with its artist.
- The current splash uses the Pokémon logo over black and this separate GIF, rather than the former composed CC BY-SA icon splash. The old CC BY-SA icon SVG remains for attribution/history and the procedural ball is retained as a shutdown fallback.
