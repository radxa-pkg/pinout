"""Discover GPIO line names without requesting or changing GPIO lines."""

from pathlib import Path

import gpiod

from pinout_device import DeviceError


class GpioLines:
    """A lazy, cached set of line names across all GPIO chips."""

    def __init__(self, directory='/dev'):
        self.directory = Path(directory)
        self._names = None
        self._failure = None

    def _scan(self):
        names = set()
        for path in sorted(self.directory.glob('gpiochip*')):
            try:
                chip = gpiod.Chip(str(path))
                try:
                    if hasattr(chip, 'get_info'):
                        # libgpiod 2.x
                        for offset in range(chip.get_info().num_lines):
                            name = chip.get_line_info(offset).name
                            if name:
                                names.add(name)
                    else:
                        # libgpiod 1.x (Debian Bookworm)
                        for offset in range(chip.num_lines()):
                            name = chip.get_line(offset).name()
                            if name:
                                names.add(name)
                finally:
                    chip.close()
            except OSError as exc:
                reason = exc.strerror or str(exc)
                raise DeviceError(f'Cannot inspect GPIO chip {path}: {reason}') from exc
        return frozenset(names)

    def __contains__(self, name):
        if self._failure is not None:
            raise DeviceError(self._failure)
        if self._names is None:
            try:
                self._names = self._scan()
            except DeviceError as exc:
                self._failure = str(exc)
                raise
        return name in self._names
