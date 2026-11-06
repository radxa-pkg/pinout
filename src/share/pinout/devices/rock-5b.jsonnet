local models = [
  // https://docs.radxa.com/en/rock5/rock5b/hardware-design/hardware-interface
  'Radxa ROCK 5B',
  // https://docs.radxa.com/en/rock5/rock5b/hardware-design/hardware-interface
  'Radxa ROCK 5B+',
  // https://docs.radxa.com/en/rock5/rock5t/hardware-design/hardware-interface
  'Radxa ROCK 5T',
];

{
  models: models,
  connectors: [{
    id: '40-pin',
    pins: {
      '22': {
        name: 'SARADC_IN4',
        gpiod_label: null,
      },
    },
  }],
}
