"""Missing physical pins preserve connector numbering and layout positions."""

from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/share/pinout/python'))

from pinout_device import DeviceError
from pinout_render import ConnectorPinout


class MissingPinTests(unittest.TestCase):
    def test_missing_left_and_right_pins_leave_their_positions_blank(self):
        pinout = ConnectorPinout({
            'name': 'Keyed header', 'dimensions': {'width': 2, 'height': 2},
            'pins': {'1': {'missing': True, 'name': 'NOT PRINTED'},
                     '2': {'name': 'RIGHT'}, '3': {'name': 'LEFT'},
                     '4': {'missing': True, 'name': 'NOT PRINTED'}},
        })
        self.assertEqual(list(pinout.rows()), ['         (2) RIGHT', 'LEFT (3)'])

    def test_missing_single_column_pins_keep_their_rows(self):
        pinout = ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 1, 'height': 3},
            'pins': {'1': {'missing': True}, '2': {'name': 'MIDDLE'},
                     '3': {'missing': True}},
        })
        self.assertEqual(list(pinout.rows()), ['', 'MIDDLE (2)', ''])

    def test_completely_missing_row_does_not_renumber_later_pins(self):
        pinout = ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 2, 'height': 2},
            'pins': {'1': {'missing': True}, '2': {'missing': True},
                     '3': {'name': 'A'}, '4': {'name': 'B'}},
        })
        self.assertEqual(list(pinout.rows()), ['', 'A (3) (4) B'])

    def test_missing_pins_skip_gpio_queries_and_color_output(self):
        lines = MagicMock()
        pinout = ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 2, 'height': 1},
            'pins': {'1': {'missing': True, 'name': 'HIDDEN',
                           'gpiod_label': 'LINE_A', 'color': '#ff0000'}},
        }, gpio_labels=lines)
        self.assertEqual(list(pinout.rows(color=True)), ['     (2)'])
        lines.__contains__.assert_not_called()

    def test_false_and_unspecified_missing_flags_print_normally(self):
        pinout = ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 2, 'height': 1},
            'pins': {'1': {'name': 'A', 'missing': False}, '2': {'name': 'B'}},
        })
        self.assertEqual(list(pinout.rows()), ['A (1) (2) B'])

    def test_missing_highest_pin_does_not_change_number_field_width(self):
        rows = list(ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 1, 'height': 10},
            'pins': {'10': {'missing': True}},
        }).rows())
        self.assertEqual(rows[0], ' ( 1)')
        self.assertEqual(rows[-2], ' ( 9)')
        self.assertEqual(rows[-1], '')

    def test_missing_must_be_boolean(self):
        for value in (None, 0, 1, 'true', [], {}):
            with self.subTest(value=value):
                with self.assertRaisesRegex(DeviceError, 'missing must be a boolean'):
                    ConnectorPinout({
                        'name': 'Header', 'dimensions': {'width': 1, 'height': 1},
                        'pins': {'1': {'missing': value}},
                    })


if __name__ == '__main__':
    unittest.main()
