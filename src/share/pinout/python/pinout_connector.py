"""Resolve connector IDs and apply nested device-specific overrides."""

from copy import deepcopy
import json
from pathlib import Path

import _jsonnet

from pinout_device import DeviceError
from pinout_render import ConnectorPinout, validate_dimensions, validate_pins, validate_starting_num


def merge_connector(base, override):
    """Merge objects recursively, replacing other values without mutating inputs."""
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_connector(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


class ConnectorDatabase:
    """Index connector IDs while evaluating full definitions in display order."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self._paths = None
        self._errors = {}

    def references(self, device):
        entries = device.get('connectors')
        if not isinstance(entries, list):
            raise DeviceError(f'Device {device["model"]!r}: connectors must be an array')
        return entries

    def _index(self):
        self._paths = {}
        for path in sorted(self.directory.glob('*.jsonnet')):
            try:
                # Jsonnet is lazy: inspect only the ID, not pins or other fields.
                expression = (
                    f'local c = import {json.dumps(str(path.resolve()))}; '
                    'if std.type(c) != "object" then error "connector definition must be an object" '
                    f'else if std.objectHas(c, "id") then c.id else {json.dumps(path.stem)}'
                )
                identifier = json.loads(_jsonnet.evaluate_snippet(str(path), expression))
                if not isinstance(identifier, str) or not identifier.strip():
                    raise DeviceError('id must be a non-empty string')
            except (OSError, RuntimeError, ValueError, DeviceError) as exc:
                self._errors[path.stem] = f'{path}: cannot evaluate connector ID: {exc}'
                continue
            if identifier in self._paths:
                self._errors[identifier] = (
                    f'duplicate connector id {identifier!r}: {self._paths[identifier]} and {path}'
                )
            else:
                self._paths[identifier] = path

    def _override(self, entry, context):
        if isinstance(entry, str):
            override = {'id': entry}
        elif isinstance(entry, dict):
            override = entry
        else:
            raise DeviceError(f'{context}: must be a connector ID string or override object')
        identifier = override.get('id')
        if not isinstance(identifier, str) or not identifier.strip():
            raise DeviceError(f'{context}: id must be a non-empty string')
        if set(override) - {'id', 'name', 'dimensions', 'pins', 'starting_num'}:
            raise DeviceError(f'{context}: override has unsupported fields')
        if 'starting_num' in override:
            validate_starting_num(override['starting_num'], context)
        if 'name' in override:
            if not isinstance(override['name'], str) or not override['name'].strip():
                raise DeviceError(f'{context}: name must be a non-empty string')
        if 'dimensions' in override:
            validate_dimensions(override['dimensions'], context, partial=True)
        if 'pins' in override:
            validate_pins(override['pins'], context)
        return identifier, override

    def load_connector(self, device, entry, index):
        context = f'Device {device["model"]!r}, connectors[{index}]'
        identifier, override = self._override(entry, context)
        if self._paths is None:
            self._index()
        if identifier in self._errors:
            raise DeviceError(f'{context}: {self._errors[identifier]}')
        path = self._paths.get(identifier)
        if path is None:
            raise DeviceError(f'{context}: connector {identifier!r} is missing '
                              f'(no matching ID in {self.directory})')
        reference = f'{context}, connector {identifier!r} ({path})'
        try:
            definition = json.loads(_jsonnet.evaluate_file(str(path)))
            if not isinstance(definition, dict):
                raise DeviceError('connector definition must be an object')
            definition.setdefault('id', path.stem)
            ConnectorPinout(definition)
            offset = (override.get('starting_num', definition.get('starting_num', 1))
                      - definition.get('starting_num', 1))
            if offset and 'pins' in definition:
                definition = dict(definition, pins={
                    str(int(number) + offset): pin
                    for number, pin in definition['pins'].items()
                })
            resolved = merge_connector(definition, override)
            ConnectorPinout(resolved)
        except (OSError, RuntimeError, ValueError, DeviceError) as exc:
            raise DeviceError(f'{reference}: cannot resolve connector: {exc}') from exc
        return resolved

    def load(self, device):
        return [self.load_connector(device, entry, index)
                for index, entry in enumerate(self.references(device))]
