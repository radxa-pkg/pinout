local models = [
  // https://docs.radxa.com/en/rockpi/rockpie/hardware/gpio
  'Radxa ROCK Pi E',
];

{
  models: models,
  connectors: [{
    id: '40-pin',
    pins: {
      '22': {
        name: 'ADC_IN1',
        gpiod_label: null,
      },
    },
  }],
}
