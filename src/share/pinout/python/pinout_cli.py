"""Command-line interface for pinout."""

import argparse
import os
import sys

from pinout_device import DeviceDatabase, DeviceDetector, DeviceError
from pinout_connector import ConnectorDatabase
from pinout_render import ConnectorPinout
from pinout_gpio import GpioLines


def main(data_directory, argv=None):
    parser = argparse.ArgumentParser(
        description='Pinout reporting utility.'
    )
    colors = parser.add_mutually_exclusive_group()
    colors.add_argument('-c', '--color', dest='color', action='store_const', const=True,
                        default=None, help='force colored output')
    colors.add_argument('-m', '--monochrome', dest='color', action='store_const', const=False,
                        help='disable colored output')
    args = parser.parse_args(argv)
    color = args.color
    if color is None:
        color = sys.stdout.isatty() and os.environ.get('TERM') != 'dumb'
    try:
        database = DeviceDatabase(data_directory / 'devices')
        device = DeviceDetector(database).detect()
    except DeviceError as exc:
        print(f'pinout: error: {exc}', file=sys.stderr)
        return 1
    print(f'Description        : {device["model"]}')
    connectors = ConnectorDatabase(data_directory / 'connectors')
    try:
        references = connectors.references(device)
    except DeviceError as exc:
        print(f'pinout: error: {exc}', file=sys.stderr)
        return 1
    status = 0
    gpio_lines = GpioLines()
    for index, name in enumerate(references):
        try:
            connector = connectors.load_connector(device, name, index)
            pinout = ConnectorPinout(connector, gpio_labels=gpio_lines)
        except DeviceError as exc:
            print(f'pinout: error: {exc}', file=sys.stderr)
            status = 1
            continue
        print(f'\n{connector["name"]}:', flush=True)
        for row in pinout.rows(color=color):
            print(row, flush=True)
    return status
