local models = [
  // https://docs.radxa.com/en/zero/zero/hardware-design/hardware-interface
  'Radxa Zero',
];

{
  models: models,
  connectors: [{
    id: '40-pin',
    pins: {
      '7': {
        name: 'GPIOAO_3',
        gpiod_label: 'PIN_27',
      },
      '11': {
        name: 'GPIOAO_2',
        gpiod_label: 'PIN_28',
      },
      '15': {
        name: 'SARADC_CH1',
        gpiod_label: null,
      },
      '26': {
        name: 'SARADC_CH2',
        gpiod_label: null,
      },
      '29': {
        name: 'NC',
        gpiod_label: null,
      },
      '31': {
        name: 'NC',
        gpiod_label: null,
      },
      '33': {
        name: 'NC',
        gpiod_label: null,
      },
    },
  }],
}
