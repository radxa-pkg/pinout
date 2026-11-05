"""Load Jsonnet device definitions and identify the running device."""

import json
from pathlib import Path

import _jsonnet


class DeviceError(Exception):
    """A device definition could not be loaded or no device matched."""


class DeviceDatabase:
    """Shared device definitions indexed by each exact model name."""

    def __init__(self, directory):
        self.models = {}
        for path in sorted(Path(directory).glob('*.jsonnet')):
            try:
                definition = json.loads(_jsonnet.evaluate_file(str(path)))
            except (OSError, RuntimeError) as exc:
                raise DeviceError(f'Cannot evaluate {path}: {exc}') from exc
            except (ValueError, UnicodeError) as exc:
                raise DeviceError(f'Invalid JSON from {path}: {exc}') from exc
            if not isinstance(definition, dict):
                raise DeviceError(f'{path}: device definition must be an object')
            models = definition.get('models')
            if not isinstance(models, list) or not models:
                raise DeviceError(f'{path}: models must be a non-empty array of strings')
            for index, model in enumerate(models):
                if not isinstance(model, str) or not model.strip():
                    raise DeviceError(f'{path}: models[{index}] must be a non-empty string')
                if model in self.models:
                    raise DeviceError(f'{path}: duplicate model {model!r}')
                self.models[model] = definition
        if not self.models:
            raise DeviceError(f'No device definitions found in {directory}')


class DeviceDetector:
    """Prefer the device-tree model, then try the DMI system product name."""

    def __init__(self, database, model_path='/proc/device-tree/model',
                 product_path='/sys/class/dmi/id/product_name'):
        self.database = database
        self.paths = (Path(model_path), Path(product_path))

    def detect(self):
        observations = []
        detected = False
        for label, path in zip(('Device-tree model', 'DMI product name'), self.paths):
            try:
                model = path.read_text(encoding='utf-8').strip('\x00 \t\r\n')
            except FileNotFoundError:
                observations.append(f'{label}: unavailable (not present)')
                continue
            except PermissionError:
                observations.append(f'{label}: unavailable (permission denied)')
                continue
            except OSError as exc:
                observations.append(f'{label}: unavailable ({exc.strerror})')
                continue
            except UnicodeError:
                observations.append(f'{label}: unavailable (invalid UTF-8)')
                continue
            if model in self.database.models:
                # Keep the shared definition unchanged; model is detection metadata.
                return dict(self.database.models[model], model=model)
            if model:
                detected = True
                observations.append(f'{label}: {model!r} (unsupported)')
            else:
                observations.append(f'{label}: unavailable (empty value)')
        if detected:
            message = 'Unsupported device: no installed definition matches the detected model.'
        else:
            message = 'Unable to identify this device: no model information is available.'
        raise DeviceError(message + '\n  ' + '\n  '.join(observations))
