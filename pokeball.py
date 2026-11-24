"""Stream preconverted GIF rows into the existing LCD framebuffer."""
import time
import struct


def play(lcd, y, duration):
    """Loop the original frame timings for duration ms, using no second framebuffer."""
    with open('/pokeball.dat', 'rb') as f:
        header = f.read(10)
        if len(header) != 10:
            raise OSError('Incomplete Pokeball header')
        magic, width, height, count = struct.unpack('<4sHHH', header)
        if magic != b'PBL1' or width != 128 or height != 123 or not 1 <= count <= 256:
            raise OSError('Invalid Pokeball data')
        view = memoryview(lcd.buffer)
        x = (240 - width) // 2
        started = time.ticks_ms()
        frame = 0
        while time.ticks_diff(time.ticks_ms(), started) < duration:
            if frame == count:
                f.seek(10)
                frame = 0
            timing = f.read(2)
            if len(timing) != 2:
                raise OSError('Incomplete Pokeball timing')
            delay = struct.unpack('<H', timing)[0]
            frame_start = time.ticks_ms()
            for row in range(height):
                offset = ((y + row) * 240 + x) * 2
                if f.readinto(view[offset:offset + width * 2]) != width * 2:
                    raise OSError('Incomplete Pokeball frame')
            lcd.show()
            frame += 1
            while (time.ticks_diff(time.ticks_ms(), frame_start) < delay and
                   time.ticks_diff(time.ticks_ms(), started) < duration):
                time.sleep_ms(5)
