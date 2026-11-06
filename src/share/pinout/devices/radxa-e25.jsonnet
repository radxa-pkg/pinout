local models = [
  // https://docs.radxa.com/en/e/e25/hardware-design/hardware-interface
  'Radxa E25 Carrier Board',
];

{
  models: models,
  connectors: [{
    id: '26-pin',
    pins: {
      [std.toString(i)]: {
        color: '#666666',
      }
      for i in std.range(1, 26)
    } + {
      '22': {
        name: 'SARADC_VIN5',
        gpiod_label: null,
      },
    },
  }],
}
