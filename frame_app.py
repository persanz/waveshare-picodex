import time
from machine import Pin, SPI, I2C

def start(lcd, power, button, mode='home'):
    import os
    import struct
    import deflate
    import sdcard
    import random

    WHITE = 0xffff
    ORANGE = 0x20fd
    BLACK = 0x0000
    DATA = '/sd/waveshare_pokemon_frame/pokemon_hd.dat'
    MOTION_COOLDOWN = 1500
    MOTION_THRESHOLD = 2200  # gentler shakes for children
    W = 240  # sprite canvas / screen width
    # Landscape is achieved via MADCTL (main.py) so art and text rotate together.
    LANDSCAPE = False
    pokedex_index = 0
    quiz_hidden = True


    def message(a, b):
        lcd.fill(0)
        lcd.text(a, max(0, (240-len(a)*8)//2), 100, WHITE)
        lcd.text(b, max(0, (240-len(b)*8)//2), 120, ORANGE)
        lcd.show()


    def draw_goodbye():
        from shutdown_screen import animate
        animate(lcd)


    def read_name(f, name_offset):
        f.seek(name_offset)
        name = b''
        for _ in range(80):
            c = f.read(1)
            if not c or c == b'\0':
                break
            name += c
        try:
            return name.decode('utf-8')
        except Exception:
            return ''


    current_art_id = 0
    current_name = ''
    description_open = False
    description_page = 0
    description_pages = 1

    def cache_artwork():
        # Save artwork without allocating a second framebuffer.
        # A second framebuffer will not fit in the MicroPython heap.
        with open('/picodex-return.tmp', 'wb') as f:
            f.write(lcd.buffer)

    def restore_artwork():
        nonlocal description_open
        with open('/picodex-return.tmp', 'rb') as f:
            if f.readinto(lcd.buffer) != len(lcd.buffer):
                raise OSError('Incomplete artwork snapshot')
        lcd.show()
        description_open = False
        os.remove('/picodex-return.tmp')

    def home_button():
        lcd.fill_rect(88, 0, 64, 18, BLACK)
        lcd.text('INICIO', 96, 5, WHITE)
        if mode == 'quiz' and not quiz_hidden:
            lcd.fill_rect(176, 0, 64, 18, BLACK)
            lcd.text('OTRO >', 184, 5, ORANGE)

    def show_home():
        nonlocal mode, pokedex_index, description_open, touch_used
        if mode == 'picodex':
            pokedex_index = index
        mode = 'home'
        touch_used = True  # consume a pending touch release after a button-home gesture
        if description_open:
            try:
                os.remove('/picodex-return.tmp')
            except OSError:
                pass
        description_open = False
        import gc
        gc.collect()
        try:
            with open('/landing.dat', 'rb') as f:
                if f.readinto(lcd.buffer) != 115200:
                    raise OSError('Incomplete landing page')
            lcd.show()
        except OSError as e:
            print('Landing artwork unavailable:', e)
            lcd.fill(BLACK)
            lcd.text('PICODEX', 80, 110, ORANGE)
            lcd.text('QUIEN ES ESTE POKEMON?', 32, 185, WHITE)
            lcd.show()
        print('Landing page ready')

    def select_mode(choice):
        nonlocal mode, index, quiz_hidden, previous, motion_samples, motion_armed, still_samples
        mode = choice
        index = pokedex_index
        quiz_hidden = True
        if mode == 'quiz':
            index = random.randrange(count)
        previous = None
        motion_samples = 0
        motion_armed = False
        still_samples = 0
        show_sprite(index)

    def quiz_step():
        nonlocal index, quiz_hidden
        if quiz_hidden:
            quiz_hidden = False
        else:
            candidate = random.randrange(count - 1) if count > 1 else 0
            if count > 1 and candidate >= index:
                candidate += 1
            index = candidate
            quiz_hidden = True
        show_sprite(index)

    def show_sprite(index):
        nonlocal current_art_id, current_name, description_open
        # Release description-rendering garbage before allocating the decoder.
        import gc
        gc.collect()
        # The order file maps Pokédex order to entries in the artwork archive.
        with open('/pokemon_order.bin', 'rb') as order:
            order.seek(2 + index * 2)
            index = struct.unpack('<H', order.read(2))[0]
        hidden = mode == 'quiz' and quiz_hidden
        with open('/sd/waveshare_pokemon_frame/quiz.dat' if hidden else DATA, 'rb') as f:
            f.seek(4 + index * 16)
            number, offset, size, name_offset = struct.unpack('<IIII', f.read(16))
            current_art_id = number
            f.seek(offset)
            stream = deflate.DeflateIO(f, deflate.RAW, 10)
            lcd.fill(0)
            screen = memoryview(lcd.buffer)
            source = bytearray(W * 2)
            for row in range(W):
                if row % 24 == 0:
                    gc.collect()
                if stream.readinto(source) != W * 2:
                    raise OSError('Incomplete sprite')
                start = row * W * 2
                screen[start:start + W * 2] = source
            stream.close()
            del stream, source, screen
            gc.collect()
            name = read_name(f, name_offset).upper()
            current_name = name
        # Release decoder buffers and the file cache before importing the footer.
        gc.collect()
        if not hidden:
            import pokemon_footer
            number = pokemon_footer.draw(lcd, number, name)
            import sys
            del sys.modules['pokemon_footer']
            del pokemon_footer
            gc.collect()
        home_button()
        lcd.show()
        description_open = False
        if hidden:
            print('Quiz silhouette', index)
            return
        print('Quiz reveal' if mode == 'quiz' else 'Displaying Pokemon', number, name)


    try:
        spi = SPI(0, baudrate=1000000, sck=Pin(18), mosi=Pin(19), miso=Pin(20))
        card = sdcard.SDCard(spi, Pin(23, Pin.OUT), baudrate=5000000)
        os.mount(card, '/sd')
        with open(DATA, 'rb') as f:
            count = struct.unpack('<I', f.read(4))[0]
        if not count:
            raise OSError('No images')
        with open('/pokemon_order.bin', 'rb') as order:
            if struct.unpack('<H', order.read(2))[0] != count:
                raise OSError('Artwork order mismatch')
    except Exception as e:
        print('SD setup error:', e)
        message('SD CARD ERROR', 'Reconnect the card')
        while True:
            time.sleep(1)

    imu = None
    for attempt in range(5):
        try:
            imu = I2C(1, sda=Pin(6), scl=Pin(7), freq=50000, timeout=50000)
            for reg, val in ((2, 0x60), (3, 0x23), (4, 0x53), (5, 0), (6, 0x11), (7, 0), (8, 3)):
                imu.writeto_mem(0x6b, reg, bytes([val]))
            break
        except OSError as e:
            print('Motion sensor try %d failed:' % (attempt + 1), e)
            time.sleep_ms(200)
    if imu is None:
        print('Motion sensor error')
        message('SENSOR ERROR', 'Restart device')
        return
    print('Motion sensor ready')

    # The touch controller shares I2C1 with the motion sensor.
    touch_ready = False
    try:
        touch_reset = Pin(16, Pin.OUT)
        touch_reset.value(0)
        time.sleep_ms(100)
        touch_reset.value(1)
        time.sleep_ms(100)
        if imu.readfrom_mem(0x15, 0xA7, 1)[0] == 0xB6:
            imu.writeto_mem(0x15, 0xFE, b'\x01')  # disable auto-sleep
            imu.writeto_mem(0x15, 0xFA, b'\x41')  # touch point mode
            touch_ready = True
            print('Touch controller ready')
    except OSError as e:
        print('Touch unavailable:', e)

    index = 0  # always start from the first Pokémon on every power-on
    last_motion = time.ticks_add(time.ticks_ms(), -MOTION_COOLDOWN)
    last_sample = time.ticks_ms()
    previous = None
    motion_samples = 0          # consecutive samples above threshold
    motion_armed = True
    still_samples = 0
    MOTION_NEEDED = 2          # two samples (~200ms); reject isolated bumps
    try:
        if mode == 'home':
            show_home()
        elif mode == 'quiz':
            select_mode('quiz')
        else:
            show_sprite(index)
    except Exception as e:
        print('Image error:', e)
        message('IMAGE ERROR', 'Check SD files')

    # Hardware watchdog: if the main loop ever blocks (e.g. a hung I2C read on
    # battery), the board resets instead of freezing forever.
    try:
        from machine import WDT
        wdt = WDT(timeout=8000)
    except Exception:
        wdt = None

    # Two buttons used: LEFT=GPIO24(previous + power on/off on long), RIGHT=GPIO25
    # (next + first on long). Middle und GPIO16 is unused.
    left_btn = Pin(24, Pin.IN, Pin.PULL_UP)
    right_btn = Pin(25, Pin.IN, Pin.PULL_UP)

    def _debounce(pin, prev):
        v = pin.value()
        if v != prev:
            time.sleep_ms(5)
            v = pin.value()
        return v

    shutdown = False          # standby (screen off) mode
    left_prev = 1
    right_prev = 1
    left_down_since = None
    right_down_since = None
    touch_down = False
    touch_since = 0
    touch_x = 0
    touch_y = 0
    touch_used = False
    both_since = None
    both_used = False

    while True:
        try:
            if wdt is not None:
                wdt.feed()
            left = _debounce(left_btn, left_prev)
            right = _debounce(right_btn, right_prev)
            now = time.ticks_ms()

            # A deliberate two-button hold returns home from any page.
            # Handle it before individual buttons so it cannot also power off.
            if not left and not right:
                if both_since is None:
                    both_since = now
                if not both_used and time.ticks_diff(now, both_since) >= 600:
                    show_home()
                    both_used = True
                left_down_since = right_down_since = None
                left_prev, right_prev = left, right
                time.sleep_ms(50)
                continue
            if both_since is not None:
                left_down_since = right_down_since = None
                left_prev, right_prev = left, right
                if left and right:
                    both_since = None
                    both_used = False
                time.sleep_ms(50)
                continue

            # Left button: short press -> previous; long press -> power off
            if left != left_prev:
                if left == 0:
                    left_down_since = now
                else:
                    if left_down_since is not None:
                        if time.ticks_diff(now, left_down_since) < 1500:
                            if not shutdown:
                                if mode == 'home':
                                    select_mode('picodex')
                                elif mode == 'quiz':
                                    quiz_step()
                                else:
                                    index = (index - 1) % count
                                    show_sprite(index)
                                previous = None
                                motion_samples = 0
                    left_down_since = None
                left_prev = left
            else:
                if left == 0 and left_down_since is not None:
                    if time.ticks_diff(now, left_down_since) >= 1500:
                        # Power-off cycle: show goodbye frame, then cut battery power.
                        try:
                            lcd.bl.duty_u16(32768)
                            draw_goodbye()
                        except Exception:
                            pass
                        lcd.bl.duty_u16(0)
                        lcd.fill(0)
                        lcd.show()
                        print('POWER OFF')
                        power.value(0)
                        while True:
                            if wdt is not None:
                                wdt.feed()
                            time.sleep_ms(100)

            # Right button: short press -> next; long press -> first Pokémon
            if right != right_prev:
                if right == 0:
                    right_down_since = now
                else:
                    if right_down_since is not None and not shutdown:
                        if time.ticks_diff(now, right_down_since) < 1500:
                            if mode == 'home':
                                select_mode('quiz')
                            elif mode == 'quiz':
                                quiz_step()
                            else:
                                index = (index + 1) % count
                                show_sprite(index)
                            previous = None
                            motion_samples = 0
                    right_down_since = None
                right_prev = right
            else:
                if right == 0 and right_down_since is not None and not shutdown:
                    if mode == 'picodex' and time.ticks_diff(now, right_down_since) >= 2000:
                        index = 0
                        show_sprite(index)
                        previous = None
                        motion_samples = 0
                        right_down_since = None

            if touch_ready and not shutdown:
                try:
                    point = imu.readfrom_mem(0x15, 0x02, 5)
                    touching = bool(point[0] & 0x0f)
                    was_touching = touch_down
                    touch_down = touching
                    if touching:
                        x = ((point[1] & 0x0f) << 8) | point[2]
                        y = ((point[3] & 0x0f) << 8) | point[4]
                        if not was_touching:
                            touch_since = now
                            touch_x, touch_y = x, y
                            touch_used = False
                            if description_open:
                                if description_page+1 < description_pages:
                                    description_page += 1
                                    from dex_description import show as next_page
                                    description_pages = next_page(lcd, current_art_id, current_name, description_page)
                                    import sys
                                    del sys.modules['dex_description']
                                    del next_page
                                else:
                                    restore_artwork()
                                touch_used = True
                        if mode == 'picodex' and not touch_used and 80 <= touch_x < 160 and 40 <= touch_y < 200:
                            if not (80 <= x < 160 and 40 <= y < 200):
                                touch_used = True
                            elif time.ticks_diff(now, touch_since) >= 800:
                                import gc
                                gc.collect()
                                cache_artwork()
                                from dex_description import show as show_description
                                description_page = 0
                                description_pages = show_description(lcd, current_art_id, current_name)
                                import sys
                                del sys.modules['dex_description']
                                del show_description
                                gc.collect()
                                description_open = True
                                touch_used = True
                                previous = None
                                motion_samples = 0
                    elif was_touching and not touch_used and not description_open:
                        if 80 <= touch_x < 160 and touch_y < 24 and mode != 'home':
                            show_home()
                            previous = None
                            motion_samples = 0
                        elif mode == 'home':
                            if 82 <= touch_y <= 149:
                                select_mode('picodex')
                            elif 157 <= touch_y <= 224:
                                select_mode('quiz')
                        elif mode == 'quiz':
                            quiz_step()
                        elif 0 <= touch_x < 80 or 160 <= touch_x < 240:
                            index = (index + (-1 if touch_x < 120 else 1)) % count
                            show_sprite(index)
                            previous = None
                            motion_samples = 0
                except OSError:
                    touch_down = False

            # Sustained movement chooses a different random artwork entry.
            # One change per shake; re-arm after half a second of calm.
            if mode == 'picodex' and not shutdown and not description_open and not touch_down and left and right and time.ticks_diff(now, last_sample) >= 100:
                last_sample = now
                try:
                    xyz = struct.unpack('<hhh', imu.readfrom_mem(0x6b, 0x35, 6))
                    delta = sum(abs(xyz[i] - previous[i]) for i in range(3)) if previous is not None else 0
                    previous = xyz
                    if not motion_armed:
                        still_samples = still_samples+1 if delta < 1000 else 0
                        if still_samples >= 5:
                            motion_armed = True
                            still_samples = 0
                        motion_samples = 0
                    else:
                        motion_samples = motion_samples + 1 if delta > MOTION_THRESHOLD else 0
                        if count > 1 and motion_samples >= MOTION_NEEDED and time.ticks_diff(now, last_motion) >= MOTION_COOLDOWN:
                            motion_armed = False
                            still_samples = 0
                            candidate = random.randrange(count - 1)
                            if candidate >= index:
                                candidate += 1
                            last_motion = now
                            previous = None
                            motion_samples = 0
                            show_sprite(candidate)
                            index = candidate
                            last_motion = time.ticks_ms()
                            print('PICODEX shuffled')
                except OSError as e:
                    previous = None
                    motion_samples = 0
                    print('PICODEX motion/read error:', e)
            elif mode != 'picodex' or shutdown or description_open or touch_down or not left or not right:
                previous = None
                motion_samples = 0

            time.sleep_ms(50)
        except Exception as e:
            # Never let a transient error kill the frame; log and keep going.
            print('loop err:', e)
            previous = None
            motion_samples = 0
            left_prev = left_btn.value()
            right_prev = right_btn.value()
            time.sleep_ms(100)
