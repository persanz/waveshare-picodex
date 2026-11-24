"""Real LCD: verify changing GIF pixels, timing and unloading before PICODEX."""
import gc, time, sys, binascii
from machine import Pin
Pin(28, Pin.OUT, value=1)
gc.threshold(1024)
from lcd import LCD_1inch54
gc.collect()
lcd = LCD_1inch54()
real_show = lcd.show
last = None
changes = 0
frames = 0
minimum = gc.mem_free()
def capture():
    global last, changes, frames, minimum
    checksum = binascii.crc32(lcd.buffer)
    if last is not None and checksum != last:
        changes += 1
    last = checksum
    frames += 1
    minimum = min(minimum, gc.mem_free())
    real_show()
lcd.show = capture
import boot_splash
started = time.ticks_ms()
boot_splash.show(lcd)
elapsed = time.ticks_diff(time.ticks_ms(), started)
assert 5000 <= elapsed < 5500, elapsed
assert frames > 15 and changes > 10, (frames, changes)
assert 'pokeball' not in sys.modules
print('PASS: startup GIF',frames,'frames',changes,'changes',elapsed,'ms; minimum heap',minimum)
