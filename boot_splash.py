"""Five-second startup screen, using the already allocated LCD framebuffer."""
import time


def show(lcd):
    import gc
    gc.collect()
    try:
        with open('/boot_splash.dat', 'rb') as f:
            if f.readinto(lcd.buffer) != 115200:
                raise OSError('Incomplete splash image')
    except OSError as e:
        print('Boot splash unavailable:', e)
        return
    lcd.fill_rect(0, 215, 240, 25, 0)
    lcd.text('Loading....', (240 - len('Loading....') * 8) // 2, 222, 0xffff)
    lcd.show()
    started = time.ticks_ms()
    print('Boot splash displayed')
    try:
        import pokeball
        pokeball.play(lcd, 94, 5000)
    except Exception as e:
        print('Boot animation unavailable:', e)
    finally:
        import sys
        sys.modules.pop('pokeball', None)
    while time.ticks_diff(time.ticks_ms(), started) < 5000:
        time.sleep_ms(20)
    print('Boot splash complete:', time.ticks_diff(time.ticks_ms(), started), 'ms')
