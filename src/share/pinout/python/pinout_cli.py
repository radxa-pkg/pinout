"""Command-line interface for pinout."""

import argparse
import sys

from pinout_device import DeviceDatabase, DeviceDetector, DeviceError
from pinout_connector import ConnectorDatabase
from pinout_render import ConnectorPinout


def main(data_directory, argv=None):
    parser = argparse.ArgumentParser(
        description='Pinout reporting utility.'
    )
    parser.parse_args(argv)
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
    for index, name in enumerate(references):
        try:
            connector = connectors.load_connector(device, name, index)
            pinout = ConnectorPinout(connector)
        except DeviceError as exc:
            print(f'pinout: error: {exc}', file=sys.stderr)
            status = 1
            continue
        print(f'\n{connector["name"]}:', flush=True)
        for row in pinout.rows():
            print(row, flush=True)
    return status
