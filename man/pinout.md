% PINOUT(1) pinout | User Commands

# NAME

pinout - report information about the current device

# SYNOPSIS

**pinout** [**-h**]

# DESCRIPTION

**pinout** identifies the current device using the device-tree model, followed
by the DMI system product name if no device-tree match is found. It compares
these values with the installed Jsonnet device definitions and prints a
Description line for a matching device.

# OPTIONS

`-h`, `--help`
:   Show help and exit.

# FILES

`/proc/device-tree/model`
:   Device-tree model used for initial detection.

`/sys/class/dmi/id/product_name`
:   DMI system product name used for fallback detection.

`/usr/share/pinout/devices/*.jsonnet`
:   Supported device definitions.

# EXIT STATUS

**0**
:   Success.

**1**
:   Device detection or definition loading failed.

**2**
:   Invalid command-line arguments.
