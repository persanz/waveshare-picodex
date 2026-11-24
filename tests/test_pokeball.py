"""Validate streamed pixels, loop timing and damaged-asset handling on the host."""
import io
from pathlib import Path
import struct
import types
import unittest
from unittest.mock import patch
import pokeball

ROOT = Path(__file__).resolve().parents[1]

class PokeballTests(unittest.TestCase):
    def run_player(self, data, duration=2100):
        ticks = [0]
        def sleep(ms): ticks[0] += ms
        clock = types.SimpleNamespace(ticks_ms=lambda: ticks[0],
            ticks_diff=lambda a,b:a-b, sleep_ms=sleep)
        frames = []
        lcd = types.SimpleNamespace(buffer=bytearray(b'\x55'*115200))
        def show():
            frames.append(bytes(lcd.buffer))
            ticks[0] += 10  # real SPI transfer consumes part of the frame interval
        lcd.show = show
        with patch.object(pokeball, 'time', clock), patch('builtins.open', return_value=io.BytesIO(data)):
            pokeball.play(lcd, 49, duration)
        return ticks[0], frames

    def test_gif_pixels_preserve_text_and_loop_at_original_timing(self):
        data = (ROOT/'pokeball.dat').read_bytes()
        magic,w,h,n = struct.unpack('<4sHHH', data[:10])
        self.assertEqual((magic,w,h,n),(b'PBL1',128,123,15))
        elapsed, frames = self.run_player(data)
        self.assertGreaterEqual(elapsed,2100)
        self.assertLess(elapsed,2120)
        self.assertGreater(len(frames),n)
        self.assertEqual(frames[0],frames[n])
        self.assertGreater(len(set(frames)), 1)
        first = data[12:12+w*h*2]
        for row in range(240):
            result = frames[0][row*480:(row+1)*480]
            if 49 <= row < 49+h:
                self.assertEqual(result[:112], b'\x55'*112)
                self.assertEqual(result[112:368],first[(row-49)*256:(row-48)*256])
                self.assertEqual(result[368:],b'\x55'*112)
            else:
                self.assertEqual(result,b'\x55'*480)

    def test_rejects_truncated_and_invalid_assets(self):
        data = (ROOT/'pokeball.dat').read_bytes()
        for bad in (data[:3],b'BAD!'+data[4:],data[:100]):
            with self.subTest(length=len(bad)), self.assertRaises(OSError):
                self.run_player(bad)
