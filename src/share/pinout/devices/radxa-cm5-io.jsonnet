local models = [
  // https://docs.radxa.com/en/som/cm/cm5/hardware/hw-interface
  'Radxa CM5 IO',
];

{
  models: models,
  connectors: [
    {
      id: '40-pin',
      pins: {
        '37': {
          name: 'SARADC_VIN4',
          gpiod_label: null,
        },
      },
    },
  ],
}
