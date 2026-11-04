"""Validate evaluated Jsonnet configuration against its schemas and references."""

import json
from pathlib import Path
import sys

import _jsonnet
from jsonschema import Draft202012Validator, RefResolver
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/share/pinout/python'))

from pinout_device import DeviceError
from pinout_render import ConnectorPinout
from pinout_connector import ConnectorDatabase


def property_pointer(error):
    return '#' + ''.join('/' + str(part).replace('~', '~0').replace('/', '~1')
                         for part in error.absolute_path)


def validate_configuration(root):
    errors = []
    documents = {'device': {}, 'connector': {}}
    validators = {}
    for kind, definitions in documents.items():
        schema_path = root / 'schemas' / f'{kind}.schema.json'
        try:
            schema = json.loads(schema_path.read_text(encoding='utf-8'))
            Draft202012Validator.check_schema(schema)
        except (OSError, ValueError, SchemaError) as exc:
            errors.append(f'{schema_path.relative_to(root)}: {exc}')
            continue
        validator = Draft202012Validator(
            schema, resolver=RefResolver(base_uri=schema_path.resolve().as_uri(), referrer=schema)
        )
        validators[kind] = validator
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
            failures = sorted(validator.iter_errors(definition), key=property_pointer)
            for failure in failures:
                errors.append(f'{reference}:{property_pointer(failure)}: {failure.message}')
            if not failures:
                definitions[path] = definition

    identifiers = {}
    for path, connector in documents['connector'].items():
        identifier = connector.get('id', path.stem)
        if identifier in identifiers:
            errors.append(f'{path.relative_to(root)}: duplicate connector id {identifier!r}, '
                          f'also defined in {identifiers[identifier]}')
        identifiers[identifier] = path.relative_to(root)
        try:
            # JSON Schema cannot express pin bounds derived from dimensions.
            ConnectorPinout(connector)
        except DeviceError as exc:
            errors.append(f'{path.relative_to(root)}: {exc}')

    models = {}
    database = ConnectorDatabase(root / 'src/share/pinout/connectors')
    for path, device in documents['device'].items():
        reference = path.relative_to(root)
        model = device['model']
        if model in models:
            errors.append(f'{reference}: duplicate model {model!r}, also defined in {models[model]}')
        models[model] = reference
        for index, entry in enumerate(device['connectors']):
            try:
                resolved = database.load_connector(device, entry, index)
                if 'connector' in validators:
                    for failure in validators['connector'].iter_errors(resolved):
                        errors.append(f'{reference}:connectors[{index}]{property_pointer(failure)}: '
                                      f'{failure.message}')
            except DeviceError as exc:
                errors.append(f'{reference}: {exc}')
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
