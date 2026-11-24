"""Real LCD/SD integration: landing, quiz, navigation and exact description return."""
import gc, machine, binascii, random
from machine import Pin
power = Pin(28, Pin.OUT, value=1)
gc.threshold(1024)
from lcd import LCD_1inch54
gc.collect()
lcd = LCD_1inch54()
hashes = []
real_show = lcd.show
def capture():
    hashes.append(binascii.crc32(lcd.buffer))
    real_show()
lcd.show = capture
import frame_app
real_i2c = machine.I2C
class Bus:
    reads = 0
    def __init__(self, *a, **kw):
        self.bus = real_i2c(*a, **kw)
    def writeto_mem(self, *a): return self.bus.writeto_mem(*a)
    def readfrom_mem(self, addr, reg, n):
        if addr == 0x15 and reg == 2:
            Bus.reads += 1
            t = Bus.reads
            if t > 96: raise KeyboardInterrupt
            for lo, hi, x, y in ((4,6,120,190), (10,12,120,110),
                (16,18,120,110), (22,24,120,110), (28,30,120,8),
                (34,36,120,110), (40,42,210,110), (46,48,120,8),
                (52,54,120,110), (58,80,120,110), (86,88,120,110)):
                if lo <= t <= hi: return bytes((1,0,x,0,y))
            return bytes(5)
        if addr == 0x6b and reg == 0x35:
            if Bus.reads < 34: raise AssertionError('Motion active in quiz/home')
            return bytes(6)
        return self.bus.readfrom_mem(addr, reg, n)
frame_app.I2C = Bus
random.seed(25)
try:
    frame_app.start(lcd, power, Pin(24, Pin.IN, Pin.PULL_UP))
except KeyboardInterrupt:
    assert len(hashes) == 12, len(hashes)
    assert hashes[0] == hashes[5] == hashes[8], 'Landing changed'
    assert hashes[1] != hashes[2] and hashes[3] != hashes[4], 'Answer not revealed'
    assert hashes[1] != hashes[3], 'Question repeated'
    assert hashes[7] == hashes[9] == hashes[11], 'Pokedex/description return changed artwork'
    print('PASS: landing, two quiz rounds, no quiz motion, home, remembered Pokedex and exact description return; heap', gc.mem_free())
