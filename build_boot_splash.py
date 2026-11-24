"""Build the logo background; the GIF player adds the ball at runtime.
Run: uv run --no-project --with pillow --with resvg-py python build_boot_splash.py
"""
from pathlib import Path
from io import BytesIO
import struct
import resvg_py
from PIL import Image

root = Path(__file__).resolve().parent
assets = root / 'assets/splash'
canvas = Image.new('RGB', (240, 240))
logo = Image.open(BytesIO(resvg_py.svg_to_bytes(
    svg_path=str(assets / 'pokemon-logo.svg'), width=864))).convert('RGBA')
logo.thumbnail((216, 78), Image.Resampling.LANCZOS)
canvas.paste(logo, ((240-logo.width)//2, 12), logo)
raw = bytearray()
for r, g, b in canvas.getdata():
    raw.extend(struct.pack('>H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)))
(root / 'boot_splash.dat').write_bytes(raw)
preview = canvas.copy()
preview.paste(Image.open(assets / 'pokeball-preview.png'), (56, 94))
preview.save(assets / 'boot-splash.png')
print('Splash ready:', len(raw), 'bytes')
