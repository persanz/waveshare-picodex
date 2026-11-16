"""Standalone PICODEX: allocate the LCD before importing the app."""
import gc
gc.threshold(1024)
from machine import Pin
power = Pin(28, Pin.OUT, value=1)
button = Pin(24, Pin.IN, Pin.PULL_UP)
from lcd import LCD_1inch54
gc.collect()
lcd = LCD_1inch54()
lcd.write_cmd(0x36)
lcd.write_data(0x00)
import boot_splash
boot_splash.show(lcd)
# Unload the splash before artwork decoding: a second framebuffer will not fit.
import sys
del sys.modules['boot_splash']
del boot_splash
gc.collect()
import frame_app
frame_app.start(lcd, power, button)
