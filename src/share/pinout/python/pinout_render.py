"""Render connector pin numbers and fixed labels as plain text."""

from pinout_device import DeviceError


class ConnectorPinout:
    """A numbered connector with optional, connector-local pin definitions."""

    def __init__(self, connector):
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
            self.labels[number] = label

    def rows(self):
        """Yield rows, adding the right column only for two-column connectors."""
        label_width = max((len(self.labels.get(number, ''))
                           for number in range(1, self.count + 1, self.width)),
                          default=0)
        number_width = len(str(self.count))
        for left in range(1, self.count + 1, self.width):
            label = self.labels.get(left, '')
            row = f'{label:>{label_width}} ({left:>{number_width}})'
            if self.width == 2:
                right = left + 1
                row += f' ({right:>{number_width}}) {self.labels.get(right, "")}'
            yield row.rstrip()
