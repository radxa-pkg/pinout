local models = [
  // https://docs.radxa.com/en/som/cm/cm3i/hardware-design/hardware-interface
  'Radxa CM3I IO Board',
];

local signals = [
  'UART2_RX',
  'GND',
  'UART2_TX',
  'HPL_OUT',
  'GND',
  'HP_SNS',
  'SARADC_VIN0_KEY/RECOVERY',
  'HPR_OUT',
  'SPKN_OUT',
  'HP_DET_L',
  'SPKP_OUT',
  'SARADC_VIN2_HP_HOOK',
  'MIC1_INN',
  'MIC1_INP',
];
{
  models: models,
  connectors: [
    {
      id: '14-pin',
      pins: {
        [std.toString(i + 1)]: {
          name: signals[i],
        }
        for i in std.range(0, 13)
      },
    },
  ],
}
