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
            'pins: {[std.toString(i)]: {name: label} for i in std.range(1, 2)}}', encoding='utf-8',
        )

    def test_evaluates_jsonnet_and_accepts_arbitrary_device_models(self):
        self.assertEqual(validate_configuration(self.root), [])

    def test_schema_error_reports_file_and_property(self):
        self.connector.write_text(json.dumps({
            'name': 'Header', 'dimensions': {'width': 1, 'height': 1},
            'pins': {'1': {'color': 'red'}},
        }), encoding='utf-8')
        errors = '\n'.join(validate_configuration(self.root))
        self.assertIn('connectors/header.jsonnet:#/pins/1/color:', errors)

    def test_checks_unreferenced_connector_files(self):
        (self.data / 'connectors/unused.jsonnet').write_text('{', encoding='utf-8')
        errors = '\n'.join(validate_configuration(self.root))
        self.assertIn('connectors/unused.jsonnet: cannot evaluate Jsonnet', errors)

    def test_missing_connector_reference_fails(self):
        self.connector.unlink()
        errors = '\n'.join(validate_configuration(self.root))
        self.assertIn("connector 'header' is missing", errors)

    def test_runtime_pin_constraints_are_preserved(self):
        for pins, reason in (({'01': {}}, 'does not match'),
                             ({'3': {}}, 'pin number must be from 1 to 2')):
            with self.subTest(pins=pins):
                self.connector.write_text(json.dumps({
                    'name': 'Header', 'dimensions': {'width': 1, 'height': 2}, 'pins': pins,
                }), encoding='utf-8')
                self.assertIn(reason, '\n'.join(validate_configuration(self.root)))

    def test_duplicate_models_fail_without_assuming_a_model_value(self):
        shutil.copy2(self.device, self.device.with_name('duplicate.jsonnet'))
        self.assertIn('duplicate model', '\n'.join(validate_configuration(self.root)))

    def test_partial_override_schema_and_resolved_configuration(self):
        self.device.write_text(json.dumps({
            'model': 'Override Board', 'connectors': [{
                'id': 'header', 'pins': {'2': {'name': 'ADC_IN0', 'gpiod_label': None}},
                'dimensions': {'height': 3},
            }],
        }), encoding='utf-8')
        self.assertEqual(validate_configuration(self.root), [])

    def test_resolved_override_bounds_are_checked(self):
        self.device.write_text(json.dumps({
            'model': 'Override Board', 'connectors': [{'id': 'header', 'pins': {'3': {}}}],
        }), encoding='utf-8')
        self.assertIn('pin number must be from 1 to 2', '\n'.join(validate_configuration(self.root)))

    def test_duplicate_connector_ids_are_checked_even_when_unused(self):
        (self.data / 'connectors/unused.jsonnet').write_text(
            '{id: "header", name: "Other", dimensions: {width: 1, height: 1}}', encoding='utf-8',
        )
        self.assertIn('duplicate connector id', '\n'.join(validate_configuration(self.root)))

    def test_missing_pin_override_uses_boolean_schema(self):
        for value in (True, False, 1, 'true', None):
            with self.subTest(missing=value):
                self.device.write_text(json.dumps({
                    'model': 'Keyed Board', 'connectors': [{'id': 'header', 'pins': {'1': {'missing': value}}}],
                }), encoding='utf-8')
                errors = validate_configuration(self.root)
                if type(value) is bool:
                    self.assertEqual(errors, [])
                else:
                    self.assertTrue(errors)


if __name__ == '__main__':
    unittest.main()
