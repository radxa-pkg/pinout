local models = [
  // https://docs.radxa.com/en/x/x5/download
  'Radxa X5',
];

{
  models: models,
  connectors: [{
    id: '40-pin-rp2-mcu',
    pins: {
      '8': { name: 'SIO_UART2_TXD' },
      '10': { name: 'SIO_UART2_RXD' },
      '36': { name: 'GPIO20' },
    },
  }],
}
