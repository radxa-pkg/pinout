% PINOUT(1) pinout | User Commands

# NAME

pinout - report information about the current device

# SYNOPSIS

**pinout** [**-h**] [**-c** | **-m**]

# DESCRIPTION

**pinout** identifies the current device using the device-tree model, followed
by the DMI system product name if no device-tree match is found. It compares
these values with the `models` arrays in the installed Jsonnet device
definitions. Any model in an array selects the same device configuration.
The Description line prints only the exact model that matched, followed by
that configuration's connector pinouts. Pin labels and
numbers use the colors specified in the connector definitions. Color is enabled
automatically when stdout is a terminal and `TERM` is not `dumb`; redirected
output is plain text unless color is forced.

Pins with a `gpiod_label` are labeled only when a GPIO line with that name exists
on an accessible GPIO chip. A matching pin uses its fixed `name` when provided,
otherwise it uses `gpiod_label`. An unmatched pin still prints its number.
Detection reads line information without requesting lines or changing their
state. GPIO chip access failures are reported as connector errors.

Connector definitions have an optional `id`, defaulting to their filename
without `.jsonnet`. Device `connectors` entries are either ID strings or objects
whose required `id` selects a base connector. Other fields override that base:
objects merge recursively and scalar values replace inherited values.

The connector's `pins` object is keyed by pin-number strings such as `"1"` and
`"26"`. A pin override changes only the supplied fields, preserving settings
such as color. Setting `gpiod_label` to `null` disables an inherited GPIO
requirement so that a fixed `name` can be printed without matching a GPIO line.

The optional connector field `starting_num` is a positive integer, defaulting
to 1. A connector with width 2, height 13, and `starting_num: 27` prints pins
27 through 52. Pin-definition keys use those displayed numbers. The layout
starts with `starting_num` on the left; the next number is on the right for
two-column connectors.

When a device override changes `starting_num`, inherited pin keys shift by the
difference before its pin overrides are merged. For example, key `"1"` in a
base starting at 1 becomes `"27"` when overridden to start at 27. Override keys
then refer to the resulting displayed numbers. Pin names and GPIO labels remain
literal strings; they are not automatically renumbered.

A pin definition with `missing: true` represents a physically absent pin used
to prevent reverse insertion. Its position is left blank, without a number or
label. Other pins retain their original numbers and positions. Missing pins do
not trigger GPIO detection or color output. Omitting `missing` or setting it to
`false` prints the pin normally.

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

`/usr/share/pinout/connectors/*.jsonnet`
:   Base connector definitions indexed by unique connector ID.

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
