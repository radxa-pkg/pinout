// Standard 2x13 header; devices override board-specific signals and supply pins.
local pins_3v3 = [1, 17];
local pins_5v = [2, 4];
local gnd_pins = [6, 9, 14, 20, 25];

{
  name: '26-pin GPIO header',
  dimensions: {
    width: 2,
    height: 13,
  },
  pins: {
    [std.toString(i)]: {
      name: '3V3',
      color: '#ffff00',
    }
    for i in pins_3v3
  } + {
    [std.toString(i)]: {
      name: '5V',
      color: '#ff0000',
    }
    for i in pins_5v
  } + {
    [std.toString(i)]: {
      name: 'GND',
      color: '#666666',
    }
    for i in gnd_pins
  } + {
    [std.toString(i)]: {
      gpiod_label: 'PIN_%d' % i,
      color: '#00ff00',
    }
    for i in std.range(1, 26)
    if !std.member(pins_3v3 + pins_5v + gnd_pins, i)
  },
}
