"""Connector-ID lookup and nested override regression tests."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/share/pinout/python'))

from pinout_connector import ConnectorDatabase
from pinout_device import DeviceError
from pinout_render import ConnectorPinout


class ConnectorOverrideTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.base = {
            'id': 'header', 'name': 'GPIO header',
            'dimensions': {'width': 2, 'height': 20},
            'pins': {'26': {'color': '#00ff00', 'gpiod_label': 'PIN_26'},
                     '1': {'name': '3V3', 'color': '#ffff00'}},
        }
        self.path = self.directory / 'base-file.jsonnet'
        self.path.write_text(json.dumps(self.base), encoding='utf-8')
        self.database = ConnectorDatabase(self.directory)
        self.device = {'model': 'Test Board'}

    def test_explicit_id_is_independent_of_filename(self):
        self.assertEqual(self.database.load_connector(self.device, 'header', 0), self.base)
        with self.assertRaisesRegex(DeviceError, 'no matching ID'):
            self.database.load_connector(self.device, 'base-file', 0)

    def test_default_id_is_filename_stem(self):
        del self.base['id']
        self.path.write_text(json.dumps(self.base), encoding='utf-8')
        connector = self.database.load_connector(self.device, 'base-file', 0)
        self.assertEqual(connector['id'], 'base-file')

    def test_pin_override_retains_color_and_disables_gpio_matching(self):
        entry = {'id': 'header', 'pins': {'26': {'name': 'ADC_IN0', 'gpiod_label': None}}}
        original = deepcopy(entry)
        connector = self.database.load_connector(self.device, entry, 0)
        self.assertEqual(connector['pins']['26'], {
            'name': 'ADC_IN0', 'color': '#00ff00', 'gpiod_label': None,
        })
        rows = list(ConnectorPinout(connector).rows(color=True))
        self.assertIn('\x1b[38;2;0;255;0m(26) ADC_IN0\x1b[0m', rows[12])
        self.assertEqual(entry, original)
        self.assertEqual(self.database.load_connector(self.device, 'header', 1), self.base)

    def test_nested_dimensions_and_new_pin_fields_merge(self):
        connector = self.database.load_connector(self.device, {
            'id': 'header', 'name': 'Alternate header', 'dimensions': {'height': 21},
            'pins': {'42': {'name': 'LAST'}, '1': {'name': 'SUPPLY'}},
        }, 0)
        self.assertEqual(connector['dimensions'], {'width': 2, 'height': 21})
        self.assertEqual(connector['pins']['1'], {'name': 'SUPPLY', 'color': '#ffff00'})
        self.assertEqual(connector['pins']['42'], {'name': 'LAST'})

    def test_invalid_resolved_pin_bounds_fail(self):
        with self.assertRaisesRegex(DeviceError, 'pin number must be from 1 to 20'):
            self.database.load_connector(self.device, {
                'id': 'header', 'dimensions': {'height': 10},
            }, 0)

    def test_invalid_base_cannot_be_repaired_by_override(self):
        self.base['dimensions']['width'] = 3
        self.path.write_text(json.dumps(self.base), encoding='utf-8')
        with self.assertRaisesRegex(DeviceError, 'dimensions.width'):
            self.database.load_connector(self.device, {
                'id': 'header', 'dimensions': {'width': 2},
            }, 0)

    def test_duplicate_default_and_explicit_ids_report_both_files(self):
        other = self.directory / 'header.jsonnet'
        definition = deepcopy(self.base)
        del definition['id']
        other.write_text(json.dumps(definition), encoding='utf-8')
        with self.assertRaises(DeviceError) as caught:
            self.database.load_connector(self.device, 'header', 0)
        for text in ('duplicate connector id', str(self.path), str(other)):
            self.assertIn(text, str(caught.exception))

    def test_invalid_entries_and_partial_fields_fail(self):
        entries = (None, {}, {'id': None}, {'id': ''}, {'id': 'header', 'unknown': 1},
                   {'id': 'header', 'dimensions': {'width': 3}},
                   {'id': 'header', 'name': None}, {'id': 'header', 'pins': []},
                   {'id': 'header', 'pins': {'01': {}}},
                   {'id': 'header', 'pins': {'26': {'number': 26}}},
                   {'id': 'header', 'pins': {'26': {'color': None}}})
        for entry in entries:
            with self.subTest(entry=entry):
                with self.assertRaises(DeviceError):
                    self.database.load_connector(self.device, entry, 0)

    def test_empty_pin_override_preserves_inherited_fields(self):
        connector = self.database.load_connector(self.device, {'id': 'header', 'pins': {'26': {}}}, 0)
        self.assertEqual(connector, self.base)


if __name__ == '__main__':
    unittest.main()
