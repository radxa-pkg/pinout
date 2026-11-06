local models = [
  // https://docs.radxa.com/en/e/e54c/hardware-design/hardware-interface
  'Radxa E54C',
];

{
  models: models,
  connectors: [{
    id: '14-pin',
    pins: {
      [std.toString(i)]: {
        gpiod_label: 'PIN_%d' % i,
      }
      for i in [3, 5, 7, 8, 9, 10, 11, 12, 13, 14]
    } + {
      '1': {
        name: '3V3',
      },
      '2': {
        name: '5V',
      },
      '4': {
        name: '5V',
      },
      '6': {
        name: 'GND',
      },
    },
  }],
}
