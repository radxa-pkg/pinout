local pins_3v3 = [1, 17];
local pins_5v = [2, 4];
local gnd_pins = [6, 9, 14, 20, 25, 30, 34, 39];
local blue_pins = [27, 28];

{
    name: '40-pin GPIO header',
    dimensions: {
        width: 2,
        height: 20,
    },
    pins: [
        {
            number: i,
            name: '3V3',
            color: '#ffff00',
        } for i in pins_3v3
    ] + [
        {
            number: i,
            name: '5V',
            color: '#ff0000',
        } for i in pins_5v
    ] + [
        {
            number: i,
            name: 'GND',
            color: '#666666',
        } for i in gnd_pins
    ] + [
        {
            number: i,
            gpiod_label: 'PIN_%d' % i,
            color: '#0000ff',
        } for i in blue_pins
    ] + [
        {
            number: i,
            gpiod_label: 'PIN_%d' % i,
            color: '#00ff00',
        } for i in std.range(1, 40) if !std.member(pins_3v3 + pins_5v + gnd_pins + blue_pins, i)
    ],
}
