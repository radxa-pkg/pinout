local models = [
  // https://docs.radxa.com/en/e/e24c/hardware-usage/hardware-interface
  'Radxa E24C',
  // https://docs.radxa.com/en/e/e24c/hardware-usage/hardware-interface
  'Radxa E24C SPI',
];

{
  models: models,
  connectors: [{
    id: '14-pin',
    name: '14-pin GPIO header',
    pins: {
      [std.toString(i)]: {
        gpiod_label: 'PIN_%d' % i,
        color: '#00ff00',
      }
      for i in [3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    } + {
      '1': { name: '3V3', color: '#ffff00' },
      '2': { name: '5V', color: '#ff0000' },
      '4': { name: 'GND', color: '#666666' },
    },
  }],
}
