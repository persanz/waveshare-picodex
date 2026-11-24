"""Compile/upload as .mpy; simulated gestures, real SD/LCD/animation."""
import gc,time,machine,hashlib
from machine import Pin
power=Pin(28,Pin.OUT,value=1)
gc.threshold(1024)
from lcd import LCD_1inch54
gc.collect()
lcd=LCD_1inch54()
import frame_app
real_i2c=machine.I2C
class Bus:
    n=0
    def __init__(self,*a,**kw): self.bus=real_i2c(*a,**kw)
    def writeto_mem(self,*a): return self.bus.writeto_mem(*a)
    def readfrom_mem(self,addr,reg,n):
        global held_hash
        if addr==0x15 and reg==2:
            Bus.n+=1
            if Bus.n==41: held_hash=hashlib.sha256(lcd.buffer).digest()
            if Bus.n>115: raise KeyboardInterrupt
            down=41<=Bus.n<=63 or 71<=Bus.n<=73
            return bytes([int(down),0,120,0,120])
        if addr==0x6b and reg==0x35:return bytes(6)
        return self.bus.readfrom_mem(addr,reg,n)
frames=0
first=last=0
free=999999
restored=False
saw_description=False
held_hash=None
real_show=lcd.show
def capture():
    global frames,first,last,free,restored,saw_description
    now=time.ticks_ms()
    if 1<=Bus.n<=40:
        frames+=1
        if not first:first=now
        last=now
        free=min(free,gc.mem_free())
    if 55<=Bus.n<=70:saw_description=True
    if Bus.n==71:
        restored=restored or hashlib.sha256(lcd.buffer).digest()==held_hash
    real_show()
lcd.show=capture
frame_app.I2C=Bus
try:
    frame_app.start(lcd,power,Pin(24,Pin.IN,Pin.PULL_UP),initial_index=37)
except KeyboardInterrupt:
    assert frames>=10,frames
    assert saw_description
    assert restored,'Animation frame not restored after description'
    print('PASS: animated Pikachu, pause/read/return; frames',frames,
          'fps',round((frames-1)*1000/time.ticks_diff(last,first),2),'min_free_heap',free)
