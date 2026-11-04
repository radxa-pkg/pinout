"""Command-line interface for pinout."""

import argparse
import sys

from pinout_device import DeviceDatabase, DeviceDetector, DeviceError
from pinout_connector import ConnectorDatabase


def main(data_directory, argv=None):
    parser = argparse.ArgumentParser(
        description='Pinout reporting utility.'
    )
    parser.parse_args(argv)
    try:
        database = DeviceDatabase(data_directory / 'devices')
        device = DeviceDetector(database).detect()
        ConnectorDatabase(data_directory / 'connectors').load(device)
    except DeviceError as exc:
        print(f'pinout: error: {exc}', file=sys.stderr)
        return 1
    print(f'Description        : {device["model"]}')
    return 0
