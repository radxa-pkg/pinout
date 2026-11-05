local model = 'Radxa ROCK 4C+';

{
  model: model,
  connectors: [
    {
      id: '40-pin',
      pins: {
        '26': {
          name: 'ADC_IN0',
          gpiod_label: null,
        },
      },
    },
    'poe',
  ],
}
