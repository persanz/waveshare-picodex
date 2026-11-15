"""Validate the included archive, order, names and Spanish pagination on a host."""
import json
import struct
import zlib
from pathlib import Path
from dex_description import lookup, lines


def main():
    descriptions = json.loads(Path('pokemon_descriptions_es.json').read_text())['pokemon']
    assert len(descriptions) == 1538
    order = Path('pokemon_order.bin').read_bytes()
    dex = Path('pokemon_dex.bin').read_bytes()
    with open('pokemon_hd.dat', 'rb') as archive:
        count, = struct.unpack('<I', archive.read(4))
        assert count == 1538
        assert struct.unpack_from('<H', order)[0] == count
        assert len(order) == 2 + count * 2
        indices = struct.unpack_from('<' + 'H' * count, order, 2)
        assert sorted(indices) == list(range(count))
        records = [struct.unpack('<IIII', archive.read(16)) for _ in range(count)]
        max_pages = 0
        allowed = set('áéíóúÁÉÍÓÚñÑüÜ¡¿°º')
        for number, offset, size, name_offset in records:
            archive.seek(offset)
            raw = zlib.decompress(archive.read(size), -10)
            assert len(raw) == 115200, number
            archive.seek(name_offset)
            name = archive.read(80).split(b'\0', 1)[0].decode('utf-8')
            assert name, number
            if number >= 10000:
                assert len(dex) >= (number - 10000 + 1) * 2, number
                assert struct.unpack_from('<H', dex, (number - 10000)*2)[0] > 0, number
            text = lookup(number, 'pokemon_descriptions_es.bin')
            assert text != 'Descripcion no disponible.', number
            wrapped = list(lines(text, 28))
            assert all(len(line) <= 28 for line in wrapped), number
            assert ''.join(''.join(wrapped).split()) == ''.join(text.split()), number
            assert all(ord(c) < 128 or c in allowed for c in text), number
            max_pages = max(max_pages, (len(wrapped) + 13)//14)
    print('PASS:', count, 'artworks decompress; order, form numbers, names and Spanish descriptions valid; max pages:', max_pages)


if __name__ == '__main__':
    main()
