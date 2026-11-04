"""Detection and command-line regression tests."""

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

DATA = Path(__file__).resolve().parents[1] / 'src/share/pinout'
sys.path.insert(0, str(DATA / 'python'))

from pinout_cli import main
from pinout_device import DeviceDatabase, DeviceDetector, DeviceError


class PinoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.devices = self.root / 'devices'
        self.devices.mkdir()
        (self.devices / 'board.jsonnet').write_text(
            '{ model: "Test Board" }', encoding='utf-8'
        )
        self.database = DeviceDatabase(self.devices)
        self.model = self.root / 'model'
        self.product = self.root / 'product_name'
        self.detector = DeviceDetector(self.database, self.model, self.product)

    def test_device_tree_match_strips_nul_and_has_priority(self):
        self.model.write_bytes(b'Test Board\x00')
        with patch.object(Path, 'read_text', autospec=True,
                          side_effect=Path.read_text) as read:
            self.assertEqual(self.detector.detect()['model'], 'Test Board')
            self.assertEqual(read.call_count, 1)

    def test_dmi_fallback_when_device_tree_unmatched_or_missing(self):
        self.product.write_text('Test Board\n', encoding='utf-8')
        for value in ('Other Board', None):
            with self.subTest(model=value):
                if value is None:
                    self.model.unlink(missing_ok=True)
                else:
                    self.model.write_text(value, encoding='utf-8')
                self.assertEqual(self.detector.detect()['model'], 'Test Board')

    def test_missing_or_unknown_models_fail(self):
        with self.assertRaisesRegex(DeviceError, 'Unable to identify this device'):
            self.detector.detect()
        self.model.write_text('Unknown', encoding='utf-8')
        self.product.write_text('Also unknown', encoding='utf-8')
        with self.assertRaisesRegex(DeviceError, 'Unknown'):
            self.detector.detect()

    def test_unsupported_dmi_error_is_readable(self):
        self.product.write_text('30HBA07MCW\n', encoding='utf-8')
        with self.assertRaises(DeviceError) as caught:
            self.detector.detect()
        self.assertEqual(str(caught.exception), (
            'Unsupported device: no installed definition matches the detected model.\n'
            '  Device-tree model: unavailable (not present)\n'
            "  DMI product name: '30HBA07MCW' (unsupported)"
        ))

    def test_unavailable_model_reasons(self):
        for content, reason in ((b'\x00\n', 'empty value'),
                                (b'\xff', 'invalid UTF-8')):
            with self.subTest(reason=reason):
                self.model.write_bytes(content)
                with self.assertRaisesRegex(DeviceError, reason):
                    self.detector.detect()
        with patch.object(Path, 'read_text', side_effect=PermissionError()):
            with self.assertRaisesRegex(DeviceError, 'permission denied'):
                self.detector.detect()

    def test_invalid_jsonnet_reports_filename(self):
        (self.devices / 'broken.jsonnet').write_text('{', encoding='utf-8')
        with self.assertRaisesRegex(DeviceError, 'broken.jsonnet'):
            DeviceDatabase(self.devices)

    def test_cli_description_and_error_exit(self):
        output, error = io.StringIO(), io.StringIO()
        with patch('pinout_cli.DeviceDetector') as detector:
            detector.return_value.detect.return_value = {'model': 'Test Board'}
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(self.root, []), 0)
            detector.return_value.detect.side_effect = DeviceError('No match')
            with contextlib.redirect_stderr(error):
                self.assertEqual(main(self.root, []), 1)
        self.assertEqual(output.getvalue(), 'Description        : Test Board\n')
        self.assertEqual(error.getvalue(), 'pinout: error: No match\n')

    def test_repository_definitions_evaluate(self):
        database = DeviceDatabase(DATA / 'devices')
        self.assertIn('Radxa ROCK 4C+', database.models)

    def test_source_launcher_help(self):
        launcher = DATA.parents[1] / 'bin/pinout'
        result = subprocess.run([sys.executable, '-B', str(launcher), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('usage: pinout', result.stdout)
        self.assertIn('--help', result.stdout)


if __name__ == '__main__':
    unittest.main()
