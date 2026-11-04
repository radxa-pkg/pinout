"""Regression tests for configuration validation using isolated fixtures."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from check_config import ROOT, validate_configuration


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / 'schemas', self.root / 'schemas')
        self.data = self.root / 'src/share/pinout'
        (self.data / 'devices').mkdir(parents=True)
        (self.data / 'connectors').mkdir()
        self.device = self.data / 'devices/board.jsonnet'
        self.connector = self.data / 'connectors/header.jsonnet'
        self.device.write_text(json.dumps({
            'model': 'An arbitrary platform model', 'connectors': ['header'],
        }), encoding='utf-8')
        self.connector.write_text(
            'local label = "GND"; {name: "Header", dimensions: {width: 1, height: 2}, '
            'pins: [{number: i, name: label} for i in std.range(1, 2)]}', encoding='utf-8',
        )

    def test_evaluates_jsonnet_and_accepts_arbitrary_device_models(self):
        self.assertEqual(validate_configuration(self.root), [])

    def test_schema_error_reports_file_and_property(self):
        self.connector.write_text(json.dumps({
            'name': 'Header', 'dimensions': {'width': 1, 'height': 1},
            'pins': [{'number': 1, 'color': 'red'}],
        }), encoding='utf-8')
        errors = '\n'.join(validate_configuration(self.root))
        self.assertIn('connectors/header.jsonnet:$.pins[0].color:', errors)

    def test_checks_unreferenced_connector_files(self):
        (self.data / 'connectors/unused.jsonnet').write_text('{', encoding='utf-8')
        errors = '\n'.join(validate_configuration(self.root))
        self.assertIn('connectors/unused.jsonnet: cannot evaluate Jsonnet', errors)

    def test_missing_connector_reference_fails(self):
        self.connector.unlink()
        errors = '\n'.join(validate_configuration(self.root))
        self.assertIn("devices/board.jsonnet: connector 'header' is missing or invalid", errors)

    def test_runtime_pin_constraints_are_preserved(self):
        for pins, reason in (([{'number': 1}, {'number': 1}], 'duplicate pin number'),
                             ([{'number': 3}], 'number must be an integer from 1 to 2')):
            with self.subTest(pins=pins):
                self.connector.write_text(json.dumps({
                    'name': 'Header', 'dimensions': {'width': 1, 'height': 2}, 'pins': pins,
                }), encoding='utf-8')
                self.assertIn(reason, '\n'.join(validate_configuration(self.root)))

    def test_duplicate_models_fail_without_assuming_a_model_value(self):
        shutil.copy2(self.device, self.device.with_name('duplicate.jsonnet'))
        self.assertIn('duplicate model', '\n'.join(validate_configuration(self.root)))


if __name__ == '__main__':
    unittest.main()
