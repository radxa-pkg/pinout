local models = [
  // https://docs.radxa.com/en/rock2/rock2a/hardware-design/hardware-interface
  'Radxa ROCK 2A',
  // https://docs.radxa.com/en/rock2/rock2f/hardware-design/hardware-interface
  'Radxa ROCK 2F',
];

{
  models: models,
  connectors: [{
    id: '40-pin',
    pins: {
      '37': {
        name: 'SARADC_IN3',
        gpiod_label: null,
      },
    },
  }],
}
