% PINOUT(1) pinout | User Commands

# NAME

pinout - report information about the current device

# SYNOPSIS

**pinout** [**-h**] [**-c** | **-m**]

# DESCRIPTION

**pinout** identifies the current device using the device-tree model, followed
by the DMI system product name if no device-tree match is found. It compares
these values with the installed Jsonnet device definitions and prints a
Description line and connector pinouts for a matching device. Pin labels and
numbers use the colors specified in the connector definitions. Color is enabled
automatically when stdout is a terminal and `TERM` is not `dumb`; redirected
output is plain text unless color is forced.

Pins with a `gpiod_label` are labeled only when a GPIO line with that name exists
on an accessible GPIO chip. A matching pin uses its fixed `name` when provided,
otherwise it uses `gpiod_label`. An unmatched pin still prints its number.
Detection reads line information without requesting lines or changing their
state. GPIO chip access failures are reported as connector errors.

# OPTIONS

`-h`, `--help`
:   Show help and exit.

`-c`, `--color`
:   Force colored output, including when stdout is redirected.

`-m`, `--monochrome`
:   Disable colored output.

# FILES

`/proc/device-tree/model`
:   Device-tree model used for initial detection.

`/sys/class/dmi/id/product_name`
:   DMI system product name used for fallback detection.

`/usr/share/pinout/devices/*.jsonnet`
:   Supported device definitions.

`/dev/gpiochip*`
:   GPIO chips inspected for matching line names. The user must have permission
    to open these devices.

# EXIT STATUS

**0**
:   Success.

**1**
:   Device detection or definition loading failed.

**2**
:   Invalid command-line arguments.
