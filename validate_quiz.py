"""Validate every derived silhouette against the original archive's entry IDs/names."""
from pathlib import Path
import struct, zlib
ROOT = Path(__file__).resolve().parent

def validate():
    with (ROOT/'pokemon_hd.dat').open('rb') as source, (ROOT/'quiz.dat').open('rb') as quiz:
        count=struct.unpack('<I',source.read(4))[0]
        assert struct.unpack('<I',quiz.read(4))[0]==count
        for i in range(count):
            source.seek(4+i*16); original=struct.unpack('<IIII',source.read(16))
            quiz.seek(4+i*16); number,offset,size,name=struct.unpack('<IIII',quiz.read(16))
            assert number==original[0], i
            assert offset>=4+16*count and name==offset+size, i
            quiz.seek(offset); raw=zlib.decompress(quiz.read(size),-10)
            assert len(raw)==115200, i
            # Solid foreground and blue background both exist above the footer.
            assert b'\x08\xe5' in raw[:216*480], i
            assert b'\x8e\x9d' in raw[:216*480], i
            source.seek(original[3]); quiz.seek(name)
            def read_name(f):
                result=bytearray()
                while True:
                    b=f.read(1)
                    if not b or b==b'\0': return bytes(result)
                    result.extend(b)
            assert read_name(source)==read_name(quiz), i
    assert (ROOT/'landing.dat').stat().st_size==115200
    print('PASS:',count,'silhouettes decompress with matching IDs/names and valid landing image')

if __name__=='__main__':validate()
