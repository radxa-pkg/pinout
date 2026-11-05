{
  name: 'PoE header',
  dimensions: {
    width: 2,
    height: 2,
  },
  pins: {
    [std.toString(i + 1)]: {
      name: 'TR%d' % i,
      color: '#666666',
    }
    for i in [1, 0, 3, 2]
  },
}
