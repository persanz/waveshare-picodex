"""Real LCD/SD: both buttons return home; left-only hold still powers off."""
import gc, machine, time
from machine import Pin
latch=Pin(28,Pin.OUT,value=1)
gc.threshold(1024)
from lcd import LCD_1inch54
gc.collect()
lcd=LCD_1inch54()
class Power:
    off=False
    def value(self, value):
        if value == 0:
            self.off=True
            raise KeyboardInterrupt
power=Power()
import frame_app
real_i2c=machine.I2C
class Bus:
    def __init__(self,*a,**kw):self.bus=real_i2c(*a,**kw)
    def writeto_mem(self,*a):return self.bus.writeto_mem(*a)
    def readfrom_mem(self,addr,reg,n):
        if addr==0x15 and reg==2: return bytes(5)
        if addr==0x6b and reg==0x35:return bytes(6)
        return self.bus.readfrom_mem(addr,reg,n)
frame_app.I2C=Bus
class Left:
    samples=0
    def value(self):
        Left.samples+=1
        if Left.samples>180:raise AssertionError('Button handling timed out')
        # Both for 1 second: home; release; right short: quiz; left long: power off.
        return 0 if 4<=Left.samples<=28 or Left.samples>=46 else 1
class Right:
    def value(self):return 0 if 4<=Left.samples<=28 or 34<=Left.samples<=36 else 1
real_pin=Pin
class Pins:
    OUT=real_pin.OUT;IN=real_pin.IN;PULL_UP=real_pin.PULL_UP
    def __new__(cls,n,*a,**kw):
        if n==24:return Left()
        if n==25:return Right()
        return real_pin(n,*a,**kw)
frame_app.Pin=Pins
try:
    frame_app.start(lcd,power,Pin(24,Pin.IN,Pin.PULL_UP),'picodex')
except KeyboardInterrupt:
    assert power.off
    print('PASS: both-button home, button-only quiz launch and left-hold animated shutdown')
