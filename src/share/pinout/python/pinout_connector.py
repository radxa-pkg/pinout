"""Load the connector definitions referenced by a matched device."""

import json
from pathlib import Path

import _jsonnet

from pinout_device import DeviceError


class ConnectorDatabase:
    """Evaluate individual connector files referenced by a device."""

    def __init__(self, directory):
        self.directory = Path(directory)

    def references(self, device):
        context = f'Device {device["model"]!r}'
        names = device.get('connectors')
        if not isinstance(names, list):
            raise DeviceError(f'{context}: connectors must be an array of file names')
        return names

    def load_connector(self, device, name, index):
        context = f'Device {device["model"]!r}'
        if (not isinstance(name, str) or not name.strip()
                or name in ('.', '..') or '/' in name or '\\' in name
                or '\x00' in name or name.endswith('.jsonnet')):
            raise DeviceError(
                f'{context}: connectors[{index}] must be a non-empty file name '
                'without a directory or .jsonnet extension'
            )
        path = self.directory / f'{name}.jsonnet'
        reference = f'{context}, connector {name!r} ({path})'
        if not path.is_file():
            raise DeviceError(f'{reference}: connector file is missing or is not a regular file')
        try:
            definition = json.loads(_jsonnet.evaluate_file(str(path)))
        except (OSError, RuntimeError, ValueError, UnicodeError) as exc:
            raise DeviceError(f'{reference}: cannot evaluate connector: {exc}') from exc
        if not isinstance(definition, dict):
            raise DeviceError(f'{reference}: connector definition must be an object')
        header = definition.get('name')
        if not isinstance(header, str) or not header.strip():
            raise DeviceError(f'{reference}: name must be a non-empty string')
        return definition

    def load(self, device):
        return [self.load_connector(device, name, index)
                for index, name in enumerate(self.references(device))]
