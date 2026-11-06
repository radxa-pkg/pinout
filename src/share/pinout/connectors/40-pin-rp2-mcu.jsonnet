// https://docs.radxa.com/en/x/x4/software/gpio
local header = import '40-pin.jsonnet';
local gpios = {
  '3': 28,
  '5': 29,
  '7': 4,
  '8': 20,
  '10': 21,
  '11': 5,
  '12': 23,
  '13': 6,
  '15': 3,
  '16': 22,
  '18': 27,
  '19': 11,
  '21': 8,
  '22': 24,
  '23': 10,
  '24': 9,
  '26': 18,
  '27': 16,
  '28': 17,
  '29': 7,
  '31': 12,
  '32': 19,
  '33': 13,
  '35': 15,
  '36': 26,
  '37': 14,
  '38': 2,
  '40': 25,
};

header {
  pins+: {
    [pin]: header.pins[pin] {
      name: 'GPIO%02d' % gpios[pin],
      gpiod_label: null,
      color: '#00ff00',
    }
    for pin in std.objectFields(gpios)
  },
}
