"""Connector numbering offsets, inherited pin keys, and schema validation."""

from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/share/pinout/python'))

from check_config import validate_configuration
from pinout_connector import ConnectorDatabase
from pinout_device import DeviceError
from pinout_render import ConnectorPinout


class StartingNumberTests(unittest.TestCase):
    def test_absolute_definitions_print_the_full_offset_range(self):
        pinout = ConnectorPinout({
            'name': 'Secondary', 'dimensions': {'width': 2, 'height': 13},
            'starting_num': 27,
            'pins': {'27': {'name': 'GND'}, '28': {'gpiod_label': 'LINE_B'},
                     '52': {'name': 'END', 'color': '#ff0000'}},
        }, gpio_labels={'LINE_B'})
        rows = list(pinout.rows())
        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[0], 'GND (27) (28) LINE_B')
        self.assertEqual(rows[-1], '    (51) (52) END')
        self.assertEqual([int(number) for row in rows for number in re.findall(r'\(\s*(\d+)\)', row)],
                         list(range(27, 53)))
        colored = list(pinout.rows(color=True))
        self.assertIn('\x1b[38;2;255;0;0m(52) END\x1b[0m', colored[-1])
        self.assertEqual([re.sub(r'\x1b\[[0-9;]*m', '', row) for row in colored], rows)

    def test_single_column_crosses_a_digit_boundary(self):
        rows = list(ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 1, 'height': 3},
            'starting_num': 9, 'pins': {'9': {'name': 'A'}, '11': {'name': 'LAST'}},
        }).rows())
        self.assertEqual(rows, ['   A ( 9)', '     (10)', 'LAST (11)'])

    def test_even_start_retains_left_to_right_position_order(self):
        self.assertEqual(list(ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 2, 'height': 2}, 'starting_num': 2,
        }).rows()), [' (2) (3)', ' (4) (5)'])

    def test_parentheses_align_across_three_digit_numbers(self):
        rows = list(ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 2, 'height': 2}, 'starting_num': 98,
        }).rows())
        self.assertEqual(rows, [' ( 98) ( 99)', ' (100) (101)'])
        for delimiter in ('(', ')'):
            self.assertEqual([i for i, char in enumerate(rows[0]) if char == delimiter],
                             [i for i, char in enumerate(rows[1]) if char == delimiter])

    def test_missing_offset_pins_leave_their_slots_and_skip_gpio(self):
        lines = MagicMock()
        rows = list(ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 2, 'height': 2}, 'starting_num': 27,
            'pins': {'27': {'missing': True, 'gpiod_label': 'HIDDEN', 'color': '#ff0000'},
                     '28': {'name': 'RIGHT'}, '29': {'name': 'LEFT'}, '30': {'missing': True}},
        }, gpio_labels=lines).rows(color=True))
        self.assertEqual(rows, ['          (28) RIGHT', 'LEFT (29)'])
        lines.__contains__.assert_not_called()

    def test_keys_must_be_within_the_displayed_range(self):
        for number in ('26', '53'):
            with self.subTest(number=number):
                with self.assertRaisesRegex(DeviceError, 'pin number must be from 27 to 52'):
                    ConnectorPinout({
                        'name': 'Header', 'dimensions': {'width': 2, 'height': 13},
                        'starting_num': 27, 'pins': {number: {}},
                    })

    def test_starting_number_must_be_a_positive_integer(self):
        for value in (None, 0, -1, True, False, 1.5, '27', [], {}):
            with self.subTest(starting_num=value):
                with self.assertRaisesRegex(DeviceError, 'starting_num must be a positive integer'):
                    ConnectorPinout({
                        'name': 'Header', 'dimensions': {'width': 1, 'height': 1},
                        'starting_num': value,
                    })


class StartingNumberOverrideTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / 'src/share/pinout/connectors'
        self.directory.mkdir(parents=True)
        self.path = self.directory / 'header.jsonnet'
        self.base = {
            'id': 'header', 'name': 'Header', 'dimensions': {'width': 2, 'height': 13},
            'pins': {'1': {'name': 'SUPPLY', 'color': '#ffff00'},
                     '2': {'gpiod_label': 'PIN_2', 'color': '#00ff00'},
                     '26': {'name': 'END', 'color': '#666666', 'missing': True}},
        }
        self.path.write_text(json.dumps(self.base), encoding='utf-8')
        self.database = ConnectorDatabase(self.directory)
        self.device = {'model': 'Test Board'}

    def test_repeated_base_id_rebases_before_merging_absolute_keys(self):
        entry = {'id': 'header', 'name': 'Secondary', 'starting_num': 27,
                 'pins': {'27': {'name': 'GND'}, '52': {'name': 'LAST', 'missing': False}}}
        original = deepcopy(entry)
        first, second = self.database.load({
            'model': 'Test Board', 'connectors': ['header', entry],
        })
        self.assertEqual(first, self.base)
        self.assertEqual(set(second['pins']), {'27', '28', '52'})
        self.assertEqual(second['pins']['27'], {'name': 'GND', 'color': '#ffff00'})
        self.assertEqual(second['pins']['28']['gpiod_label'], 'PIN_2')
        self.assertEqual(second['pins']['52'], {
            'name': 'LAST', 'color': '#666666', 'missing': False,
        })
        rows = list(ConnectorPinout(second, gpio_labels={'PIN_2'}).rows())
        self.assertIn('(27) (28) PIN_2', rows[0])
        self.assertIn('(51) (52) LAST', rows[-1])
        self.assertIn('( 1)', next(ConnectorPinout(first).rows()))
        self.assertEqual(entry, original)
        self.assertEqual(self.database.load_connector(self.device, 'header', 2), self.base)
        self.assertEqual(json.loads(self.path.read_text()), self.base)

    def test_offset_base_inherits_start_and_can_shift_back_to_one(self):
        self.base['starting_num'] = 27
        self.base['pins'] = {str(int(key) + 26): value for key, value in self.base['pins'].items()}
        self.path.write_text(json.dumps(self.base), encoding='utf-8')
        inherited = self.database.load_connector(self.device, {'id': 'header', 'pins': {'28': {'name': 'B'}}}, 0)
        self.assertEqual(inherited['starting_num'], 27)
        self.assertEqual(inherited['pins']['28']['gpiod_label'], 'PIN_2')
        restored = self.database.load_connector(self.device, {'id': 'header', 'starting_num': 1}, 1)
        self.assertEqual(set(restored['pins']), {'1', '2', '26'})
        self.assertEqual(restored['starting_num'], 1)
        self.assertTrue(restored['pins']['26']['missing'])
        self.assertEqual(self.database.load_connector(self.device, 'header', 2), self.base)

    def test_old_number_override_is_rejected_after_rebase(self):
        with self.assertRaisesRegex(DeviceError, 'pin number must be from 27 to 52'):
            self.database.load_connector(self.device, {
                'id': 'header', 'starting_num': 27, 'pins': {'1': {'name': 'WRONG'}},
            }, 0)

    def test_schema_allows_start_in_base_and_partial_override(self):
        shutil.copytree(ROOT / 'schemas', self.root / 'schemas')
        devices = self.root / 'src/share/pinout/devices'
        devices.mkdir()
        (devices / 'board.jsonnet').write_text(json.dumps({
            'models': ['Test Board'], 'connectors': ['header', {'id': 'header', 'starting_num': 27}],
        }), encoding='utf-8')
        self.assertEqual(validate_configuration(self.root), [])
        self.base['starting_num'] = 27
        self.base['pins'] = {str(int(key) + 26): value for key, value in self.base['pins'].items()}
        self.path.write_text(json.dumps(self.base), encoding='utf-8')
        self.assertEqual(validate_configuration(self.root), [])

    def test_schema_and_runtime_reject_invalid_override_start(self):
        shutil.copytree(ROOT / 'schemas', self.root / 'schemas')
        devices = self.root / 'src/share/pinout/devices'
        devices.mkdir()
        for value in (None, 0, -1, True, 1.5, '27'):
            with self.subTest(starting_num=value):
                entry = {'id': 'header', 'starting_num': value}
                with self.assertRaisesRegex(DeviceError, 'starting_num must be a positive integer'):
                    self.database.load_connector(self.device, entry, 0)
                (devices / 'board.jsonnet').write_text(json.dumps({
                    'models': ['Test Board'], 'connectors': [entry],
                }), encoding='utf-8')
                self.assertTrue(validate_configuration(self.root))


if __name__ == '__main__':
    unittest.main()
