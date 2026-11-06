{
  name: '14-pin GPIO header',
  dimensions: { width: 2, height: 7 },
  pins: {
    [std.toString(i)]: {
      color: '#666666',
    }
    for i in std.range(1, 14)
  },
}
