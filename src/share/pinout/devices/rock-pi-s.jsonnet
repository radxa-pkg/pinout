local models = [
  // https://docs.radxa.com/en/rockpi/rockpis/hardware/pin-gpio
  'Radxa ROCK Pi S',
];

{
  models: models,
  connectors: [
    {
      id: '26-pin',
      name: '26-pin GPIO header 1',
      pins: {
        '26': {
          name: 'ADC_IN0',
          gpiod_label: null,
        },
      },
    },
    'rock-pi-s-secondary',
  ],
}
