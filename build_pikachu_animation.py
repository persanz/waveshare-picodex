"""Convert the included source GIF to row-streamable RGB565 frames (host only)."""
from pathlib import Path
import struct
import zlib
from PIL import Image
ROOT = Path(__file__).resolve().parent

def build():
    image = Image.open(ROOT/'assets/animated/pikachu.gif')
    width, height = image.size
    output = ROOT/'pikachu_animation.dat'
    with output.open('wb') as f:
        f.write(struct.pack('<4sHHH', b'PKA3', width*3, height, image.n_frames))
        for i in range(image.n_frames):
            image.seek(i)
            rgba = image.convert('RGBA')
            rgb = Image.new('RGB', image.size, 'black')
            rgb.paste(rgba, mask=rgba.getchannel('A'))
            rgb = rgb.resize((width*3, height), Image.Resampling.NEAREST)
            raw = bytearray()
            for r,g,b in rgb.get_flattened_data():
                value = ((r>>3)<<11)|((g>>2)<<5)|(b>>3)
                raw.extend(struct.pack('>H', value))
            compressor = zlib.compressobj(9, zlib.DEFLATED, -9)
            packed = compressor.compress(raw)+compressor.flush()
            f.write(struct.pack('<HH',max(60,image.info.get('duration',100)),len(packed)))
            f.write(packed)
    print(image.n_frames, 'frames,',width,'x',height,output.stat().st_size,'bytes')

if __name__ == '__main__':
    build()
