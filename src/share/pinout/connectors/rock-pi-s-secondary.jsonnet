// https://docs.radxa.com/en/rockpi/rockpis/hardware/pin-gpio

local gpio_pins = [28, 30, 32, 34, 39, 40, 41, 42, 43, 44, 45, 46];

local signals = [
  'GND',
  '',
  'ADC_KEY_IN1',
  '',
  'MICBIAS2',
  '',
  'MICBIAS1',
  '',
  'MICN8',
  'MICP8',
  'MICN7',
  'MICP7',
  '',
  '',
  '',
  '',
  '',
  '',
  '',
  '',
  'MICN2',
  'MICP2',
  'MICN1',
  'MICP1',
  'LINEOUT_R',
  'LINEOUT_L',
];
{
  name: '26-pin GPIO header 2',
  dimensions: { width: 2, height: 13 },
  starting_num: 27,
  pins: {
    [std.toString(i)]: {
      color: '#666666',
    }
    for i in std.range(27, 52)
  } + {
    [std.toString(i)]: {
      gpiod_label: 'PIN_%d' % i,
    }
    for i in gpio_pins
  } + {
    [std.toString(i)]: {
      name: signals[i - 27],
    }
    for i in std.range(27, 52)
    if !std.member(gpio_pins, i)
  },
}
