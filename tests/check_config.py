"""Validate evaluated Jsonnet configuration against its schemas and references."""

import json
from pathlib import Path
import sys

import _jsonnet
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/share/pinout/python'))

from pinout_device import DeviceError
from pinout_render import ConnectorPinout


def validate_configuration(root):
    errors = []
    documents = {'device': {}, 'connector': {}}
    for kind, definitions in documents.items():
        schema_path = root / 'schemas' / f'{kind}.schema.json'
        try:
            schema = json.loads(schema_path.read_text(encoding='utf-8'))
            Draft202012Validator.check_schema(schema)
        except (OSError, ValueError, SchemaError) as exc:
            errors.append(f'{schema_path.relative_to(root)}: {exc}')
            continue
        validator = Draft202012Validator(schema)
        directory = root / 'src/share/pinout' / f'{kind}s'
        paths = sorted(directory.glob('*.jsonnet'))
        if not paths:
            errors.append(f'{directory.relative_to(root)}: no Jsonnet definitions found')
        for path in paths:
            reference = path.relative_to(root)
            try:
                definition = json.loads(_jsonnet.evaluate_file(str(path)))
            except (OSError, RuntimeError, ValueError) as exc:
                errors.append(f'{reference}: cannot evaluate Jsonnet: {exc}')
                continue
            failures = sorted(validator.iter_errors(definition), key=lambda error: error.json_path)
            for failure in failures:
                errors.append(f'{reference}:{failure.json_path}: {failure.message}')
            if not failures:
                definitions[path] = definition

    for path, connector in documents['connector'].items():
        try:
            # JSON Schema cannot express uniqueness by pin number or dynamic bounds.
            ConnectorPinout(connector)
        except DeviceError as exc:
            errors.append(f'{path.relative_to(root)}: {exc}')

    models = {}
    for path, device in documents['device'].items():
        reference = path.relative_to(root)
        model = device['model']
        if model in models:
            errors.append(f'{reference}: duplicate model {model!r}, also defined in {models[model]}')
        models[model] = reference
        for name in device['connectors']:
            connector_path = root / 'src/share/pinout/connectors' / f'{name}.jsonnet'
            if connector_path not in documents['connector']:
                errors.append(f'{reference}: connector {name!r} is missing or invalid')
    return errors


def main():
    errors = validate_configuration(ROOT)
    for error in errors:
        print(f'configuration error: {error}', file=sys.stderr)
    if errors:
        return 1
    print('Configuration schemas, Jsonnet definitions, and connector references are valid.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
