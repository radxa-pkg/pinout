local models = [
  // https://docs.radxa.com/en/rock4/hardware/rock4-gpio
  'Radxa ROCK 4C+',
  // https://docs.radxa.com/en/rock4/rock4ab-se/hardware-design/hardware-interface
  'Radxa ROCK 4SE',
  // https://docs.radxa.com/en/rock4/hardware/rock4-gpio
  'Radxa ROCK Pi 4A',
  // https://docs.radxa.com/en/rock4/hardware/rock4-gpio
  'Radxa ROCK Pi 4A+',
  // https://docs.radxa.com/en/rock4/rock4ab-se/hardware-design/hardware-interface
  'Radxa ROCK Pi 4B',
  // https://docs.radxa.com/en/rock4/rock4ab-se/hardware-design/hardware-interface
  'Radxa ROCK Pi 4B+',
  // https://docs.radxa.com/en/rock4/hardware/rock4-gpio
  'Radxa ROCK Pi 4C',
];

{
  models: models,
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
  ],
}
