"""Build silhouettes and the landing page from the existing artwork archive.
uv run --no-project --with pillow --with numpy --with scipy --with resvg-py python build_quiz.py
"""
from pathlib import Path
import struct, zlib, io, os
import numpy as np
from scipy.ndimage import binary_fill_holes, binary_closing
from PIL import Image, ImageDraw, ImageFont
import resvg_py
ROOT = Path(__file__).resolve().parent
ASSETS = ROOT/'assets/quiz'

def font(size, bold=False):
    override = os.environ.get('PICODEX_FONT_BOLD' if bold else 'PICODEX_FONT')
    candidates = [override, '/System/Library/Fonts/Supplemental/Arial%s.ttf' % (' Bold' if bold else ''),
                  'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf']
    for path in candidates:
        if not path: continue
        try: return ImageFont.truetype(path,size)
        except OSError: pass
    raise RuntimeError('Set PICODEX_FONT and PICODEX_FONT_BOLD to Unicode TrueType fonts')

def rgb(raw):
    v=np.frombuffer(raw,dtype='>u2').reshape(240,240)
    return np.stack((((v>>11)&31)*255//31,((v>>5)&63)*255//63,(v&31)*255//31),axis=-1).astype('uint8')

def packed(image):
    a=np.array(image.convert('RGB'),dtype=np.uint16)
    return (((a[:,:,0]>>3)<<11)|((a[:,:,1]>>2)<<5)|(a[:,:,2]>>3)).astype('>u2').tobytes()

def silhouette(a):
    # Fill interior black details; external black remains background. No new art source.
    mask=binary_fill_holes(binary_closing(np.max(a,axis=2)>0, iterations=2))
    result=np.empty_like(a);result[:]=(139,208,239);result[mask]=(13,28,47)
    return Image.fromarray(result)

def build():
    ASSETS.mkdir(exist_ok=True)
    entries=[];shadow=None
    with (ROOT/'pokemon_hd.dat').open('rb') as source, (ROOT/'quiz.dat').open('wb') as out:
        count=struct.unpack('<I',source.read(4))[0]
        out.write(struct.pack('<I',count));out.write(bytes(16*count))
        for i in range(count):
            source.seek(4+i*16)
            number,offset,size,name_offset=struct.unpack('<IIII',source.read(16))
            source.seek(offset);a=rgb(zlib.decompress(source.read(size),-10))
            image=silhouette(a)
            if number==25:
                shadow=image.copy()
            draw=ImageDraw.Draw(image)
            draw.rectangle((0,216,239,239),fill=(13,28,47))
            draw.text((120,215),'¿Quién es este Pokémon?',font=font(12,True),fill='white',anchor='mt')
            draw.text((120,230),'Toca para descubrirlo',font=font(9),fill=(255,218,81),anchor='mt')
            encoded=zlib.compressobj(9,zlib.DEFLATED,-10)
            compressed=encoded.compress(packed(image))+encoded.flush()
            start=out.tell();out.write(compressed)
            source.seek(name_offset);name=bytearray()
            while True:
                ch=source.read(1)
                if not ch or ch==b'\0':break
                name.extend(ch)
            name_position=out.tell();out.write(name+b'\0')
            entries.append((number,start,len(compressed),name_position))
            if number==25: image.save(ASSETS/'silhouette-preview.png')
            if i%200==0:print('Built silhouettes',i,'/',count,flush=True)
        out.seek(4)
        for entry in entries:out.write(struct.pack('<IIII',*entry))
    canvas=Image.new('RGB',(240,240),(8,17,31));d=ImageDraw.Draw(canvas)
    logo=Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_path=str(ROOT/'assets/splash/pokemon-logo.svg'),width=600))).convert('RGBA')
    logo.thumbnail((158,55),Image.Resampling.LANCZOS);canvas.paste(logo,((240-logo.width)//2,4),logo)
    d.text((120,62),'ELIGE TU AVENTURA',font=font(11,True),fill=(228,237,248),anchor='mt')
    d.rounded_rectangle((8,82,231,149),radius=12,fill=(21,39,61),outline=(65,106,150),width=1)
    d.rounded_rectangle((8,157,231,224),radius=12,fill=(25,50,67),outline=(62,147,162),width=1)
    # Restore the original red PICODEX icon from the earlier launcher.
    art=Image.open(ASSETS/'picodex-icon.png').convert('RGB').resize((64,64),Image.Resampling.LANCZOS)
    canvas.paste(art,(12,84))
    dark=shadow.resize((64,64),Image.Resampling.LANCZOS);canvas.paste(dark,(12,159))
    d.text((87,97),'PICODEX',font=font(20,True),fill=(255,215,70))
    d.text((88,124),'Explora los Pokémon',font=font(11),fill=(235,244,255))
    d.text((87,170),'¿QUIÉN ES ESTE',font=font(13,True),fill=(255,215,70))
    d.text((87,187),'POKÉMON?',font=font(17,True),fill=(255,215,70))
    d.text((88,209),'Adivina y descubre',font=font(10),fill=(235,244,255))
    d.text((120,230),'Toca una opción para empezar',font=font(10),fill=(191,210,230),anchor='mt')
    canvas.save(ASSETS/'landing-preview.png');(ROOT/'landing.dat').write_bytes(packed(canvas))
    print('Built',count,'silhouettes;', (ROOT/'quiz.dat').stat().st_size,'bytes')

if __name__=='__main__':build()
