"""Load the connector definitions referenced by a matched device."""

import json
from pathlib import Path

import _jsonnet

from pinout_device import DeviceError


class ConnectorDatabase:
    """Evaluate connector files in device order, retaining their full contents."""

    def __init__(self, directory):
        self.directory = Path(directory)

    def load(self, device):
        context = f'Device {device["model"]!r}'
        names = device.get('connectors')
        if not isinstance(names, list):
            raise DeviceError(f'{context}: connectors must be an array of file names')
        definitions = []
        for index, name in enumerate(names):
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
            definitions.append(definition)
        return definitions
