local models = [
  // https://docs.radxa.com/en/zero/zero2pro/hardware-design/hardware-interface
  'Radxa Zero2',
];

{
  models: models,
  connectors: [{
    id: '40-pin',
    pins: {
      '26': {
        name: 'SARADC_CH2',
        gpiod_label: null,
      },
    },
  }],
}
