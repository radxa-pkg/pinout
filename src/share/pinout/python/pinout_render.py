"""Validate and render connector-local pins with optional ANSI colors."""

import re

from pinout_device import DeviceError


def validate_dimensions(dimensions, context, partial=False):
    if not isinstance(dimensions, dict):
        raise DeviceError(f'{context}: dimensions must be an object')
    if set(dimensions) - {'width', 'height'}:
        raise DeviceError(f'{context}: dimensions has unsupported fields')
    if not partial or 'width' in dimensions:
        width = dimensions.get('width')
        if type(width) is not int or width not in (1, 2):
            raise DeviceError(f'{context}: dimensions.width must be 1 or 2')
    if not partial or 'height' in dimensions:
        height = dimensions.get('height')
        if type(height) is not int or height < 1:
            raise DeviceError(f'{context}: dimensions.height must be a positive integer')


def validate_starting_num(value, context):
    if type(value) is not int or value < 1:
        raise DeviceError(f'{context}: starting_num must be a positive integer')


def validate_pins(pins, context, count=None, starting_num=1):
    if not isinstance(pins, dict):
        raise DeviceError(f'{context}: pins must be an object keyed by pin number')
    for key, pin in pins.items():
        reference = f'{context}, pins[{key!r}]'
        if not isinstance(key, str) or not re.fullmatch(r'[1-9][0-9]*', key):
            raise DeviceError(f'{reference}: pin key must be a positive integer string')
        if count is not None and not starting_num <= int(key) < starting_num + count:
            raise DeviceError(f'{reference}: pin number must be from '
                              f'{starting_num} to {starting_num + count - 1}')
        if not isinstance(pin, dict):
            raise DeviceError(f'{reference}: pin definition must be an object')
        if set(pin) - {'name', 'color', 'gpiod_label', 'missing'}:
            raise DeviceError(f'{reference}: pin definition has unsupported fields')
        if 'missing' in pin and type(pin['missing']) is not bool:
            raise DeviceError(f'{reference}: missing must be a boolean')
        if 'name' in pin and not isinstance(pin['name'], str):
            raise DeviceError(f'{reference}: name must be a string')
        label = pin.get('gpiod_label')
        if label is not None and (not isinstance(label, str) or not label.strip()):
            raise DeviceError(f'{reference}: gpiod_label must be a non-empty string or null')
        if 'color' in pin:
            color = pin['color']
            if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                raise DeviceError(f'{reference}: color must be a #RRGGBB string')


class ConnectorPinout:
    """A numbered connector with optional definitions keyed by pin number."""

    def __init__(self, connector, gpio_labels=()):
        context = f'Connector {connector.get("name", "")!r}'
        if set(connector) - {'id', 'name', 'dimensions', 'pins', 'starting_num'}:
            raise DeviceError(f'{context}: connector has unsupported fields')
        if not isinstance(connector.get('name'), str) or not connector['name'].strip():
            raise DeviceError(f'{context}: name must be a non-empty string')
        dimensions = connector.get('dimensions')
        validate_dimensions(dimensions, context)
        self.width = dimensions['width']
        self.height = dimensions['height']
        self.count = self.width * self.height
        self.starting_num = connector.get('starting_num', 1)
        validate_starting_num(self.starting_num, context)
        self.last_num = self.starting_num + self.count - 1
        pins = connector.get('pins', {})
        validate_pins(pins, context, self.count, self.starting_num)
        self.labels = {}
        self.colors = {}
        self.missing = set()
        for key, pin in pins.items():
            number = int(key)
            if pin.get('missing', False):
                self.missing.add(number)
                continue
            reference = f'{context}, pins[{key!r}]'
            label = pin.get('name', '')
            gpio_label = pin.get('gpiod_label')
            if gpio_label is not None:
                try:
                    valid = gpio_label in gpio_labels
                except DeviceError as exc:
                    raise DeviceError(f'{reference}: {exc}') from exc
                label = pin.get('name', gpio_label) if valid else ''
            self.labels[number] = label
            if 'color' in pin:
                color = pin['color']
                red, green, blue = (int(color[index:index + 2], 16) for index in (1, 3, 5))
                self.colors[number] = f'\x1b[38;2;{red};{green};{blue}m'

    def _paint(self, number, text, color):
        if color and number in self.colors:
            return f'{self.colors[number]}{text}\x1b[0m'
        return text

    def rows(self, color=False):
        """Yield rows, adding the right column only for two-column connectors."""
        positions = range(self.starting_num, self.last_num + 1, self.width)
        label_width = max((len(self.labels.get(number, ''))
                           for number in positions), default=0)
        number_width = len(str(self.last_num))
        for left in positions:
            label = self.labels.get(left, '')
            if left in self.missing:
                row = ' ' * (label_width + number_width + 3)
            else:
                row = self._paint(left, f'{label:>{label_width}} ({left:>{number_width}})', color)
            if self.width == 2:
                right = left + 1
                if right not in self.missing:
                    text = f'({right:>{number_width}}) {self.labels.get(right, "")}'.rstrip()
                    row += ' ' + self._paint(right, text, color)
            yield row.rstrip()
