"""Optional Pikachu player: one small row buffer, no second framebuffer."""
import struct
import deflate
import time

class Player:
    def __init__(self, lcd, path='/sd/waveshare_pokemon_frame/pikachu_animation.dat'):
        self.file = open(path, 'rb')
        try:
            magic, self.width, self.height, self.count = struct.unpack('<4sHHH', self.file.read(10))
            if magic != b'PKA3' or not (1 <= self.width <= 192 and 1 <= self.height <= 64 and 1 <= self.count <= 256):
                raise ValueError('Invalid Pikachu animation')
            self.file.seek(0, 2)
            if self.file.tell() < 10+self.count*4:
                raise ValueError('Incomplete Pikachu animation')
            self.lcd = lcd
            self.screen = memoryview(lcd.buffer)
            self.row = bytearray(self.width*2)
            self.x = (240-self.width)//2
            self.y = (216-self.height*3)//2
            self.frame = 0
            self.due = time.ticks_ms()
            self.first = True
        except Exception:
            self.file.close()
            raise

    def step(self, now):
        if time.ticks_diff(now, self.due) < 0:
            return False
        if self.frame == 0:
            self.file.seek(10)
        delay, size = struct.unpack('<HH', self.file.read(4))
        end = self.file.tell()+size
        if not size:
            raise ValueError('Empty animation frame')
        stream = deflate.DeflateIO(self.file, deflate.RAW, 9)
        if not 60 <= delay <= 2000:
            raise ValueError('Invalid frame duration')
        if self.first:
            self.lcd.fill_rect(0, 0, 240, 216, 0)
            self.first = False
        length = len(self.row)
        for y in range(self.height):
            if stream.readinto(self.row) != len(self.row):
                raise OSError('Incomplete animation row')
            for dy in (0, 1, 2):
                pos = ((self.y+y*3+dy)*240+self.x)*2
                self.screen[pos:pos+length] = self.row
        del stream
        self.file.seek(end)
        self.lcd.show()
        self.frame = (self.frame+1) % self.count
        self.due = time.ticks_add(now, delay)
        return True

    def close(self):
        self.file.close()
