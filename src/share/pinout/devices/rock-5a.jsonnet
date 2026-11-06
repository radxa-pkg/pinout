local models = [
  // https://docs.radxa.com/en/rock5/rock5a/hardware-design/hardware-interface
  'Radxa ROCK 5A',
  // https://docs.radxa.com/en/rock5/rock5c/hardware-design/hardware-interface
  'Radxa ROCK 5C',
];

{
  models: models,
  connectors: [{
    id: '40-pin',
    pins: {
      '37': {
        name: 'SARADC_VIN2',
        gpiod_label: null,
      },
    },
  }],
}
