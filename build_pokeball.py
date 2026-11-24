"""Convert Zel-Duh's supplied GIF to streamed RGB565 frames (no GIF decoder on Pico).
Run: uv run --no-project --with pillow python build_pokeball.py
"""
from pathlib import Path
import struct
from PIL import Image, ImageOps, ImageSequence

ROOT = Path(__file__).resolve().parent
SIZE = (128, 123)

def build():
    source = Image.open(ROOT / 'assets/splash/zel-duh-pokeball.gif')
    with (ROOT / 'pokeball.dat').open('wb') as out:
        out.write(struct.pack('<4sHHH', b'PBL1', *SIZE, source.n_frames))
        for frame in ImageSequence.Iterator(source):
            # Pillow resolves GIF disposal/transparency before resizing each frame.
            image = Image.new('RGBA', source.size, (0, 0, 0, 255))
            image.alpha_composite(frame.convert('RGBA'))
            image = ImageOps.contain(image.convert('RGB'), SIZE, Image.Resampling.LANCZOS)
            canvas = Image.new('RGB', SIZE)
            canvas.paste(image, ((SIZE[0]-image.width)//2, (SIZE[1]-image.height)//2))
            out.write(struct.pack('<H', max(20, frame.info.get('duration', 100))))
            for r, g, b in canvas.getdata():
                out.write(struct.pack('>H', ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)))
            if out.tell() == 10 + 2 + SIZE[0]*SIZE[1]*2:
                canvas.save(ROOT / 'assets/splash/pokeball-preview.png')
    print('Pokeball:', source.n_frames, 'frames,', (ROOT / 'pokeball.dat').stat().st_size, 'bytes')

if __name__ == '__main__':
    build()
