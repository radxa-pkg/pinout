local models = [
  // https://docs.radxa.com/en/rock3/rock3b/hardware-design/hardware-interface
  'Radxa ROCK 3 Model B',
  // https://docs.radxa.com/en/rock3/rock3a/hardware-design/hardware-interface
  'Radxa ROCK3 Model A',
];

{
  models: models,
  connectors: [{
    id: '40-pin',
    pins: {
      '37': {
        name: 'SARADC_VIN5',
        gpiod_label: null,
      },
    },
  }],
}
