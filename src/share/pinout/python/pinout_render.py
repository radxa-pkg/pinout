"""Render connector pin numbers and fixed labels with optional ANSI colors."""

import re

from pinout_device import DeviceError


class ConnectorPinout:
    """A numbered connector with optional, connector-local pin definitions."""

    def __init__(self, connector, gpio_labels=()):
        context = f'Connector {connector["name"]!r}'
        dimensions = connector.get('dimensions')
        if not isinstance(dimensions, dict):
            raise DeviceError(f'{context}: dimensions must be an object')
        self.width = dimensions.get('width')
        self.height = dimensions.get('height')
        if type(self.width) is not int or self.width not in (1, 2):
            raise DeviceError(f'{context}: dimensions.width must be 1 or 2')
        if type(self.height) is not int or self.height < 1:
            raise DeviceError(f'{context}: dimensions.height must be a positive integer')
        self.count = self.width * self.height
        pins = connector.get('pins', [])
        if not isinstance(pins, list):
            raise DeviceError(f'{context}: pins must be an array')
        self.labels = {}
        self.colors = {}
        for index, pin in enumerate(pins):
            reference = f'{context}, pins[{index}]'
            if not isinstance(pin, dict):
                raise DeviceError(f'{reference}: pin definition must be an object')
            number = pin.get('number')
            if type(number) is not int or not 1 <= number <= self.count:
                raise DeviceError(f'{reference}: number must be an integer from 1 to {self.count}')
            if number in self.labels:
                raise DeviceError(f'{reference}: duplicate pin number {number}')
            label = pin.get('name', '')
            if not isinstance(label, str):
                raise DeviceError(f'{reference}: name must be a string')
            if 'gpiod_label' in pin:
                gpio_label = pin['gpiod_label']
                if not isinstance(gpio_label, str) or not gpio_label.strip():
                    raise DeviceError(f'{reference}: gpiod_label must be a non-empty string')
                try:
                    valid = gpio_label in gpio_labels
                except DeviceError as exc:
                    raise DeviceError(f'{reference}: {exc}') from exc
                label = pin.get('name', gpio_label) if valid else ''
            self.labels[number] = label
            if 'color' in pin:
                color = pin['color']
                if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                    raise DeviceError(f'{reference}: color must be a #RRGGBB string')
                red, green, blue = (int(color[index:index + 2], 16) for index in (1, 3, 5))
                self.colors[number] = f'\x1b[38;2;{red};{green};{blue}m'

    def _paint(self, number, text, color):
        if color and number in self.colors:
            return f'{self.colors[number]}{text}\x1b[0m'
        return text

    def rows(self, color=False):
        """Yield rows, adding the right column only for two-column connectors."""
        label_width = max((len(self.labels.get(number, ''))
                           for number in range(1, self.count + 1, self.width)),
                          default=0)
        number_width = len(str(self.count))
        for left in range(1, self.count + 1, self.width):
            label = self.labels.get(left, '')
            row = self._paint(left, f'{label:>{label_width}} ({left:>{number_width}})', color)
            if self.width == 2:
                right = left + 1
                text = f'({right:>{number_width}}) {self.labels.get(right, "")}'.rstrip()
                row += ' ' + self._paint(right, text, color)
            yield row
