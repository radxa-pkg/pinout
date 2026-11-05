"""Multiple model strings select one shared device configuration."""

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/share/pinout/python'))

from pinout_cli import main
from pinout_device import DeviceDatabase, DeviceDetector, DeviceError


class DeviceModelsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.devices = self.root / 'devices'
        self.devices.mkdir()
        (self.root / 'connectors').mkdir()
        (self.root / 'connectors/header.jsonnet').write_text(
            '{name: "Shared header", dimensions: {width: 1, height: 1}, '
            'pins: {"1": {name: "GND"}}}', encoding='utf-8',
        )
        self.definition = {'models': ['Board A', 'Board B'], 'connectors': ['header']}
        self.path = self.devices / 'shared.jsonnet'
        self.path.write_text(json.dumps(self.definition), encoding='utf-8')
        self.model = self.root / 'model'
        self.product = self.root / 'product_name'

    def test_all_models_index_the_same_configuration(self):
        database = DeviceDatabase(self.devices)
        self.assertEqual(set(database.models), {'Board A', 'Board B'})
        self.assertIs(database.models['Board A'], database.models['Board B'])
        self.assertEqual(database.models['Board A'], self.definition)

    def test_detection_preserves_exact_match_and_shared_definition(self):
        database = DeviceDatabase(self.devices)
        detector = DeviceDetector(database, self.model, self.product)
        self.product.write_text('Board A\n', encoding='utf-8')
        for name in ('Board B', 'Board A', 'Board B'):
            with self.subTest(model=name):
                self.model.write_bytes(name.encode() + b'\x00')
                device = detector.detect()
                self.assertEqual(device['model'], name)
                self.assertEqual(device['connectors'], ['header'])
                self.assertEqual(device['models'], ['Board A', 'Board B'])
                self.assertNotIn('model', database.models[name])

    def test_dmi_fallback_matches_an_alias(self):
        self.model.write_text('Unknown DT model', encoding='utf-8')
        self.product.write_text('Board B\n', encoding='utf-8')
        detector = DeviceDetector(DeviceDatabase(self.devices), self.model, self.product)
        self.assertEqual(detector.detect()['model'], 'Board B')

    def test_model_matching_is_exact(self):
        self.model.write_text('board a', encoding='utf-8')
        with self.assertRaisesRegex(DeviceError, 'Unsupported device'):
            DeviceDetector(DeviceDatabase(self.devices), self.model, self.product).detect()

    def test_cli_prints_only_matched_model_for_each_alias(self):
        for name in self.definition['models']:
            with self.subTest(model=name):
                self.model.write_text(name, encoding='utf-8')
                output = io.StringIO()
                with patch('pinout_cli.DeviceDetector', side_effect=lambda database:
                           DeviceDetector(database, self.model, self.product)):
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(main(self.root, ['--monochrome']), 0)
                self.assertEqual(output.getvalue(),
                                 f'Description        : {name}\n\nShared header:\nGND (1)\n')

    def test_models_must_be_a_nonempty_array_of_nonempty_strings(self):
        for models in (None, '', 'Board A', {}, [], [None], [1], [''], [' '], ['Board A', '']):
            with self.subTest(models=models):
                self.path.write_text(json.dumps({'models': models}), encoding='utf-8')
                with self.assertRaisesRegex(DeviceError, 'models'):
                    DeviceDatabase(self.devices)

    def test_duplicate_models_in_one_configuration_are_rejected(self):
        self.path.write_text('{models: ["Board A", "Board A"]}', encoding='utf-8')
        with self.assertRaisesRegex(DeviceError, 'duplicate model'):
            DeviceDatabase(self.devices)

    def test_overlapping_model_arrays_are_rejected(self):
        (self.devices / 'second.jsonnet').write_text(
            '{models: ["Board C", "Board B"]}', encoding='utf-8',
        )
        with self.assertRaisesRegex(DeviceError, "duplicate model 'Board B'"):
            DeviceDatabase(self.devices)

    def test_legacy_model_field_is_not_a_models_array(self):
        self.path.write_text('{model: "Board A"}', encoding='utf-8')
        with self.assertRaisesRegex(DeviceError, 'models must be a non-empty array'):
            DeviceDatabase(self.devices)


if __name__ == '__main__':
    unittest.main()
