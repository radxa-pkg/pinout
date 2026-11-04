"""GPIO discovery and label resolution without real GPIO hardware."""

import contextlib
import errno
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

DATA = Path(__file__).resolve().parents[1] / 'src/share/pinout'
sys.path.insert(0, str(DATA / 'python'))

from pinout_cli import main
from pinout_device import DeviceError
from pinout_gpio import GpioLines
from pinout_render import ConnectorPinout


class GpioTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def test_v2_line_names_across_chips_are_scanned_once(self):
        first = self.directory / 'gpiochip0'
        second = self.directory / 'gpiochip1'
        first.touch()
        second.touch()
        chips = []
        for names in (('LINE_A', None), ('LINE_B', 'LINE_A', '')):
            chips.append(SimpleNamespace(
                get_info=Mock(return_value=SimpleNamespace(num_lines=len(names))),
                get_line_info=Mock(side_effect=[SimpleNamespace(name=name) for name in names]),
                close=Mock(),
            ))
        with patch('pinout_gpio.gpiod.Chip', side_effect=chips) as factory:
            lines = GpioLines(self.directory)
            factory.assert_not_called()
            self.assertIn('LINE_A', lines)
            self.assertIn('LINE_B', lines)
            self.assertNotIn('UNKNOWN', lines)
            self.assertNotIn('', lines)
            self.assertEqual(factory.call_args_list, [call(str(first)), call(str(second))])
        for chip in chips:
            chip.close.assert_called_once_with()
        self.assertEqual(chips[1].get_line_info.call_args_list, [call(0), call(1), call(2)])

    def test_v1_line_names(self):
        path = self.directory / 'gpiochip0'
        path.touch()
        chip = SimpleNamespace(
            num_lines=Mock(return_value=3),
            get_line=Mock(side_effect=[SimpleNamespace(name=Mock(return_value=name))
                                       for name in ('LINE_A', None, 'LINE_B')]),
            close=Mock(),
        )
        with patch('pinout_gpio.gpiod.Chip', return_value=chip):
            lines = GpioLines(self.directory)
            self.assertIn('LINE_A', lines)
            self.assertIn('LINE_B', lines)
            self.assertNotIn('UNKNOWN', lines)
        chip.num_lines.assert_called_once_with()
        self.assertEqual(chip.get_line.call_args_list, [call(0), call(1), call(2)])
        chip.close.assert_called_once_with()

    def test_no_chips_is_an_empty_set(self):
        with patch('pinout_gpio.gpiod.Chip') as factory:
            self.assertNotIn('LINE_A', GpioLines(self.directory))
            factory.assert_not_called()

    def test_permission_error_is_readable_and_cached(self):
        path = self.directory / 'gpiochip0'
        path.touch()
        with patch('pinout_gpio.gpiod.Chip',
                   side_effect=PermissionError(errno.EACCES, 'Permission denied')) as factory:
            lines = GpioLines(self.directory)
            for name in ('LINE_A', 'LINE_B'):
                with self.assertRaises(DeviceError) as caught:
                    name in lines
                self.assertIn(str(path), str(caught.exception))
                self.assertIn('Permission denied', str(caught.exception))
            factory.assert_called_once()

    def test_failed_line_query_closes_chip(self):
        (self.directory / 'gpiochip0').touch()
        chip = SimpleNamespace(
            get_info=Mock(return_value=SimpleNamespace(num_lines=1)),
            get_line_info=Mock(side_effect=OSError(errno.EIO, 'Input/output error')),
            close=Mock(),
        )
        with patch('pinout_gpio.gpiod.Chip', return_value=chip):
            with self.assertRaisesRegex(DeviceError, 'Input/output error'):
                'LINE_A' in GpioLines(self.directory)
        chip.close.assert_called_once_with()

    def test_gpio_labels_require_matches_and_fixed_names_take_priority(self):
        pinout = ConnectorPinout({
            'name': 'Header', 'dimensions': {'width': 2, 'height': 3},
            'pins': [
                {'number': 1, 'name': 'FIXED', 'gpiod_label': 'LINE_A'},
                {'number': 2, 'gpiod_label': 'LINE_B'},
                {'number': 3, 'name': 'HIDDEN', 'gpiod_label': 'MISSING'},
                {'number': 4, 'gpiod_label': 'MISSING'},
                {'number': 5, 'name': 'POWER'},
                {'number': 6, 'name': '', 'gpiod_label': 'LINE_A'},
            ],
        }, gpio_labels={'LINE_A', 'LINE_B'})
        self.assertEqual(list(pinout.rows()), [
            'FIXED (1) (2) LINE_B', '      (3) (4)', 'POWER (5) (6)',
        ])

    def test_invalid_gpio_labels(self):
        for value in (None, 1, '', ' ', [], {}):
            with self.subTest(label=value):
                with self.assertRaisesRegex(DeviceError, 'gpiod_label must be a non-empty string'):
                    ConnectorPinout({
                        'name': 'Header', 'dimensions': {'width': 1, 'height': 1},
                        'pins': [{'number': 1, 'gpiod_label': value}],
                    })

    def test_fixed_only_pins_do_not_scan_gpio(self):
        lines = GpioLines(self.directory)
        with patch.object(lines, '_scan') as scan:
            pinout = ConnectorPinout({
                'name': 'Header', 'dimensions': {'width': 1, 'height': 1},
                'pins': [{'number': 1, 'name': 'GND'}],
            }, gpio_labels=lines)
            self.assertEqual(list(pinout.rows()), ['GND (1)'])
            scan.assert_not_called()

    def test_cli_uses_gpio_names_and_continues_after_access_failure(self):
        gpio_connector = {
            'name': 'GPIO header', 'dimensions': {'width': 1, 'height': 1},
            'pins': [{'number': 1, 'gpiod_label': 'LINE_A'}],
        }
        fixed_connector = {
            'name': 'Fixed header', 'dimensions': {'width': 1, 'height': 1},
            'pins': [{'number': 1, 'name': 'GND'}],
        }
        for failure in (False, True):
            with self.subTest(failure=failure):
                output, error = io.StringIO(), io.StringIO()
                with patch('pinout_cli.DeviceDatabase'), \
                        patch('pinout_cli.DeviceDetector') as detector, \
                        patch('pinout_cli.ConnectorDatabase') as database, \
                        patch('pinout_cli.GpioLines') as gpio:
                    detector.return_value.detect.return_value = {'model': 'Test Board'}
                    database.return_value.references.return_value = ['gpio', 'fixed']
                    database.return_value.load_connector.side_effect = [gpio_connector, fixed_connector]
                    if failure:
                        gpio.return_value.__contains__.side_effect = DeviceError('GPIO access denied')
                    else:
                        gpio.return_value.__contains__.return_value = True
                    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                        self.assertEqual(main(self.directory, ['--monochrome']), int(failure))
                    gpio.assert_called_once_with()
                self.assertIn('Fixed header:\nGND (1)', output.getvalue())
                if failure:
                    self.assertIn("Connector 'GPIO header', pins[0]: GPIO access denied", error.getvalue())
                    self.assertNotIn('\nGPIO header:', output.getvalue())
                else:
                    self.assertIn('GPIO header:\nLINE_A (1)', output.getvalue())
                    self.assertEqual(error.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
