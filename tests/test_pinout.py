"""Detection and command-line regression tests."""

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import _jsonnet

DATA = Path(__file__).resolve().parents[1] / 'src/share/pinout'
sys.path.insert(0, str(DATA / 'python'))

from pinout_cli import main
from pinout_device import DeviceDatabase, DeviceDetector, DeviceError
from pinout_connector import ConnectorDatabase
from pinout_render import ConnectorPinout


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
            detector.return_value.detect.return_value = {'model': 'Test Board', 'connectors': []}
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
        for device in database.models.values():
            connectors = ConnectorDatabase(DATA / 'connectors').load(device)
            self.assertEqual(len(connectors), len(device['connectors']))
            for connector in connectors:
                self.assertEqual(len(list(ConnectorPinout(connector).rows())),
                                 connector['dimensions']['height'])

    def test_connectors_evaluate_in_device_order(self):
        directory = self.root / 'connectors'
        directory.mkdir()
        (directory / 'first.jsonnet').write_text('{name: "First"}', encoding='utf-8')
        (directory / 'second.jsonnet').write_text('{name: "Second"}', encoding='utf-8')
        connectors = ConnectorDatabase(directory).load({
            'model': 'Test Board', 'connectors': ['second', 'first'],
        })
        self.assertEqual(connectors, [{'name': 'Second'}, {'name': 'First'}])

    def test_connector_list_and_names_must_be_valid(self):
        loader = ConnectorDatabase(self.root / 'connectors')
        for value in (None, 'header', {}, [1], [''], ['../header'],
                      ['/header'], ['header.jsonnet'], ['..'], ['a\\b'], ['a\x00b']):
            with self.subTest(connectors=value):
                with self.assertRaisesRegex(DeviceError, 'Test Board.*connectors'):
                    loader.load({'model': 'Test Board', 'connectors': value})
        with self.assertRaisesRegex(DeviceError, 'connectors must be an array'):
            loader.load({'model': 'Test Board'})

    def test_connector_file_failures(self):
        directory = self.root / 'connectors'
        directory.mkdir()
        path = directory / 'header.jsonnet'
        loader = ConnectorDatabase(directory)
        device = {'model': 'Test Board', 'connectors': ['header']}
        for content, reason in ((None, 'missing'), ('{', 'cannot evaluate'),
                                ('error "broken"', 'cannot evaluate'),
                                ('[]', 'must be an object')):
            with self.subTest(content=content):
                if content is not None:
                    path.write_text(content, encoding='utf-8')
                with self.assertRaises(DeviceError) as caught:
                    loader.load(device)
                message = str(caught.exception)
                for expected in ('Test Board', 'header', str(path), reason):
                    self.assertIn(expected, message)

    def test_cli_connector_failure_keeps_device_description(self):
        output, error = io.StringIO(), io.StringIO()
        with patch('pinout_cli.DeviceDetector') as detector:
            detector.return_value.detect.return_value = {
                'model': 'Test Board', 'connectors': ['missing'],
            }
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                self.assertEqual(main(self.root, []), 1)
        self.assertEqual(output.getvalue(), 'Description        : Test Board\n')
        self.assertIn("connector 'missing'", error.getvalue())

    def test_connector_header_requires_a_name(self):
        directory = self.root / 'connectors'
        directory.mkdir()
        path = directory / 'header.jsonnet'
        for content in ('{}', '{name: null}', '{name: 1}', '{name: " "}'):
            with self.subTest(content=content):
                path.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(DeviceError, 'name must be a non-empty string'):
                    ConnectorDatabase(directory).load_connector(
                        {'model': 'Test Board'}, 'header', 0,
                    )

    def test_cli_prints_headers_before_loading_next_and_continues_errors(self):
        directory = self.root / 'connectors'
        directory.mkdir()
        for name, content in (
                ('first', '{name: "First header", dimensions: {width: 1, height: 1}}'),
                ('broken', 'error "broken connector"'),
                ('bad-layout', '{name: "Bad layout", dimensions: {width: 3, height: 1}}'),
                ('unnamed', '{}'),
                ('last', '{name: "Last header", dimensions: {width: 1, height: 1}}')):
            (directory / f'{name}.jsonnet').write_text(content, encoding='utf-8')
        output, error = io.StringIO(), io.StringIO()
        evaluate = _jsonnet.evaluate_file

        def check_output_before_evaluation(path):
            if Path(path).name in ('broken.jsonnet', 'last.jsonnet'):
                self.assertIn('\nFirst header:\n (1)\n', output.getvalue())
            return evaluate(path)

        with patch('pinout_cli.DeviceDetector') as detector:
            device = {'model': 'Test Board', 'connectors': [
                'first', 'missing', None, 'broken', 'bad-layout', 'unnamed', 'last',
            ]}
            detector.return_value.detect.return_value = device
            with patch('_jsonnet.evaluate_file', side_effect=check_output_before_evaluation):
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    self.assertEqual(main(self.root, []), 1)
        self.assertEqual(output.getvalue(), (
            'Description        : Test Board\n\nFirst header:\n (1)\n\nLast header:\n (1)\n'
        ))
        self.assertEqual(error.getvalue().count('pinout: error:'), 5)
        for expected in ('missing', 'connectors[2]', 'broken connector', 'dimensions.width', 'unnamed'):
            self.assertIn(expected, error.getvalue())

    def test_cli_valid_connector_headers_succeed(self):
        directory = self.root / 'connectors'
        directory.mkdir()
        (directory / 'header.jsonnet').write_text(
            '{name: "GPIO header", dimensions: {width: 2, height: 1}, '
            'pins: [{number: 1, name: "3V3"}, {number: 2, name: "5V"}]}',
            encoding='utf-8',
        )
        output, error = io.StringIO(), io.StringIO()
        with patch('pinout_cli.DeviceDetector') as detector:
            detector.return_value.detect.return_value = {
                'model': 'Test Board', 'connectors': ['header'],
            }
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                self.assertEqual(main(self.root, []), 0)
        self.assertEqual(output.getvalue(),
                         'Description        : Test Board\n\nGPIO header:\n3V3 (1) (2) 5V\n')
        self.assertEqual(error.getvalue(), '')

    def test_two_column_sparse_pins_use_connector_numbers(self):
        connector = {
            'name': 'Sparse header', 'dimensions': {'width': 2, 'height': 3},
            'pins': [{'number': 6, 'name': 'RESET'}, {'number': 2, 'name': '5V'},
                     {'number': 1, 'name': '3V3'}, {'number': 5, 'name': 'GND'},
                     {'number': 3, 'gpiod_label': 'GPIO3', 'color': '#ff0000'}],
        }
        self.assertEqual(list(ConnectorPinout(connector).rows()), [
            '3V3 (1) (2) 5V', '    (3) (4)', 'GND (5) (6) RESET',
        ])

    def test_one_column_pins_use_the_left_layout(self):
        connector = {
            'name': 'Single header', 'dimensions': {'width': 1, 'height': 3},
            'pins': [{'number': 3, 'name': 'GND'}, {'number': 1, 'name': '3V3'}],
        }
        self.assertEqual(list(ConnectorPinout(connector).rows()), [
            '3V3 (1)', '    (2)', 'GND (3)',
        ])

    def test_multi_digit_numbers_align_and_restart_for_each_connector(self):
        connector = {'name': 'Header', 'dimensions': {'width': 2, 'height': 6}}
        rows = list(ConnectorPinout(connector).rows())
        self.assertEqual(rows[0], ' ( 1) ( 2)')
        self.assertEqual(rows[4], ' ( 9) (10)')
        self.assertEqual(rows[5], ' (11) (12)')
        for delimiter in ('(', ')'):
            columns = [[index for index, char in enumerate(row) if char == delimiter]
                       for row in rows]
            self.assertTrue(all(column == columns[0] for column in columns))
        self.assertEqual(list(ConnectorPinout(connector).rows()), rows)
        connector['dimensions'] = {'width': 1, 'height': 10}
        rows = list(ConnectorPinout(connector).rows())
        self.assertEqual(rows[0], ' ( 1)')
        self.assertEqual(rows[-1], ' (10)')
        for delimiter in ('(', ')'):
            self.assertEqual(len({row.index(delimiter) for row in rows}), 1)
        connector['dimensions'] = {'width': 1, 'height': 100}
        rows = list(ConnectorPinout(connector).rows())
        self.assertEqual(rows[0], ' (  1)')
        self.assertEqual(rows[9], ' ( 10)')
        self.assertEqual(rows[-1], ' (100)')

    def test_invalid_pin_layouts_report_errors(self):
        valid_dimensions = {'width': 2, 'height': 2}
        for dimensions in (None, [], {'width': 3, 'height': 2},
                           {'width': True, 'height': 2}, {'width': 1, 'height': 0},
                           {'width': 1, 'height': 1.5}):
            with self.subTest(dimensions=dimensions):
                with self.assertRaisesRegex(DeviceError, 'dimensions'):
                    ConnectorPinout({'name': 'Invalid', 'dimensions': dimensions})
        for pins in (None, {}, [None], [{}], [{'number': True}], [{'number': 0}],
                     [{'number': 5}], [{'number': 1.5}], [{'number': 1, 'name': None}],
                     [{'number': 1}, {'number': 1}]):
            with self.subTest(pins=pins):
                with self.assertRaisesRegex(DeviceError, 'pins'):
                    ConnectorPinout({'name': 'Invalid', 'dimensions': valid_dimensions,
                                     'pins': pins})

    def test_source_launcher_help(self):
        launcher = DATA.parents[1] / 'bin/pinout'
        result = subprocess.run([sys.executable, '-B', str(launcher), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('usage: pinout', result.stdout)
        self.assertIn('--help', result.stdout)


if __name__ == '__main__':
    unittest.main()
