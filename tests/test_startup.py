import builtins
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import patch


class StartupTests(unittest.TestCase):
    def test_boots_directly_to_picodex_after_allocating_display(self):
        events = []
        pins = {}
        class Pin:
            OUT, IN, PULL_UP = 1, 2, 3
            def __init__(self, number, *args, **kwargs):
                self.number = number
                pins[number] = self
                events.append(('pin', number, kwargs))
        class LCD:
            def __init__(self): events.append(('display',))
            def write_cmd(self, value): events.append(('command', value))
            def write_data(self, value): events.append(('data', value))
        def start(lcd, power, button):
            self.assertIsInstance(lcd, LCD)
            self.assertIs(power, pins[28])
            self.assertIs(button, pins[24])
            events.append(('start',))
        modules = {
            'machine': types.SimpleNamespace(Pin=Pin),
            'gc': types.SimpleNamespace(threshold=lambda value: events.append(('threshold', value)), collect=lambda: None),
            'lcd': types.SimpleNamespace(LCD_1inch54=LCD),
            'frame_app': types.SimpleNamespace(start=start),
        }
        real_import = builtins.__import__
        def observe(name, *args, **kwargs):
            self.assertNotIn(name, ('boot_menu', 'companion_app', 'companion_state', 'boot_splash'))
            if name == 'frame_app':
                self.assertIn(('display',), events)
                events.append(('app_import',))
            return real_import(name, *args, **kwargs)
        with patch.dict(sys.modules, modules), patch('builtins.__import__', observe):
            runpy.run_path(str(Path(__file__).resolve().parents[1]/'main.py'))
        self.assertEqual(events[0], ('threshold', 1024))
        self.assertIn(('pin', 28, {'value': 1}), events)
        self.assertIn(('command', 0x36), events)
        self.assertIn(('data', 0x00), events)
        self.assertEqual(events[-2:], [('app_import',), ('start',)])
