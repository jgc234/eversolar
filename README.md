# Protocol decoder for Eversolar PV Inverter

This is my attempt to reverse engineer the serial protocol used in the
Eversolar PV Inverters.  If you google for a document called
`eversolar_Inverter_PMU_PROTOCOL_V1-1.pdf`, this will explain the
protocol.  It is difficult to understand (at last in English).  The
rest of my learnings is from
https://github.com/solmoller/eversolar-monitor .  This particular
project explains how to setup the serial communication and lots of
other interesting stuff.  It's also fairly easy to understand the
protocol from, except a few parts which I believe are different.

This code works (at least for a TL1500 model unit) on a Pi, but
doesn't do too much otherwise.

Code as an example of how to decode messages.  May be useful to build
other projects from.

```bash
./eversolar.py --kafka kafkaserver.local:9092 --debug=debug --serial /dev/ttyUSB0
```

## How the protocol works

* Note this is missing an introduction on how to initiate connections
  and a general protocol overview.  It was originally written to
  explain the differences between my understanding of the protocol
  (dynamically described) and how it was implemented in the solmoller
  project (statically assumed).

This is my understanding:

The mappings between fields are dynamically queried from the device,
using the `QUERY_DESCRIPTION` (0x11,0x00) command.  This returns a
list of all the data codes (in order) that will be returned when you
when you call `QUERY_NORMAL_INFO` later.  This would be unique to each
device (in theory, although it looks like most return the same order
anyway).  Build a lookup table of these mappings based in their index
position in the packet.

You then use this mapping to determine what fields are returned from
the `QUERY_NORMAL_INFO` (0x11,0x02) command.

That's my interpretation anyway.

Here's the results from my inverter (Eversolar TL1500)

send query_description...

```
2018-09-24 09:38:49 [INFO] tx packet - aa55010000101100000121
2018-09-24 09:38:49 [INFO] expecting reply of (17, 128)
2018-09-24 09:38:50 [INFO] rx packet - aa5500100100118016000d010441424344454748494a4c78797a7b7c7d7e7f0862
2018-09-24 09:38:50 [INFO] rx packet - src=0x10, dst=0x100, function=(17, 128), data=b'\x00\r\x01\x04ABCDEGHIJLxyz{|}~\x7f', len=22, checksum=b'\x08'
```

My inverter returns 22 bytes, which represent the single-byte codes for each position

```
00
0d
01
04
41
42
43
44
45
47
48
49
4a
4c
78
79
7a
7b
7c
7d
7e
7f
08
62
```

If you decode this as single bytes representing the data code by positional index.
eg

```
position 0 -> code 0x00
position 1 -> code 0x0d
position 2 -> code 0x01
etc..
```

So, looking up a huge table of all possible fields (from protocol PDF), and then keeping a map of index -> data code..

```
2018-09-24 09:38:50 [INFO]  map [00] -> code=0x00, var=temp, multiplier=0.1, units=°C, descr=Internal inverter temperature
2018-09-24 09:38:50 [INFO]  map [01] -> code=0x0d, var=e_today, multiplier=0.01, units=KW.Hr, descr=The accumulated kWh of day
2018-09-24 09:38:50 [INFO]  map [02] -> code=0x01, var=v_pv1, multiplier=0.1, units=V, descr=PV1 voltage
2018-09-24 09:38:50 [INFO]  map [03] -> code=0x04, var=i_pv1, multiplier=0.1, units=A, descr=PV1 current
2018-09-24 09:38:50 [INFO]  map [04] -> code=0x41, var=i_pv, multiplier=0.1, units=A, descr=PV current
2018-09-24 09:38:50 [INFO]  map [05] -> code=0x42, var=v_ac, multiplier=0.1, units=V, descr=Grid voltage
2018-09-24 09:38:50 [INFO]  map [06] -> code=0x43, var=f_ac, multiplier=0.01, units=Hz, descr=Grid frequency
2018-09-24 09:38:50 [INFO]  map [07] -> code=0x44, var=p_ac, multiplier=1, units=W, descr=Power to grid
2018-09-24 09:38:50 [INFO]  map [08] -> code=0x45, var=z_ac, multiplier=0.001, units=Ω, descr=Grid Impedance
2018-09-24 09:38:50 [INFO]  map [09] -> code=0x47, var=e_total_hr, multiplier=0.1, units=KW.Hr, descr=Total Energy to grid
2018-09-24 09:38:50 [INFO]  map [10] -> code=0x48, var=e_total_l, multiplier=0.1, units=KW.Hr, descr=Total Energy to grid
2018-09-24 09:38:50 [INFO]  map [11] -> code=0x49, var=h_total_h, multiplier=1, units=Hr, descr=Total operation hours
2018-09-24 09:38:50 [INFO]  map [12] -> code=0x4a, var=h_total_l, multiplier=1, units=Hr, descr=Total operation hours
2018-09-24 09:38:50 [INFO]  map [13] -> code=0x4c, var=mode, multiplier=1, units=, descr=Operation Mode
2018-09-24 09:38:50 [INFO]  map [14] -> code=0x78, var=gv_fault_value, multiplier=0.1, units=V, descr=Grid Voltage Fault Value
2018-09-24 09:38:50 [INFO]  map [15] -> code=0x79, var=gf_fault_value, multiplier=0.01, units=Hz, descr=Grid Frequency Fault Value
2018-09-24 09:38:50 [INFO]  map [16] -> code=0x7a, var=gz_fault_value, multiplier=0.001, units=Ω, descr=Grid Impedance Fault Value
2018-09-24 09:38:50 [INFO]  map [17] -> code=0x7b, var=tmp_fault_fault, multiplier=0.1, units=°C, descr=Temperature Fault Value
2018-09-24 09:38:50 [INFO]  map [18] -> code=0x7c, var=pv1_fault_value, multiplier=0.1, units=V, descr=PV1 voltage fault value
2018-09-24 09:38:50 [INFO]  map [19] -> code=0x7d, var=gfci_fault_value, multiplier=0.1, units=A, descr=GFCI current fault value
2018-09-24 09:38:50 [INFO]  map [20] -> code=0x7e, var=error_msg_h, multiplier=None, units=, descr=Failure description for status
2018-09-24 09:38:50 [INFO]  map [21] -> code=0x7f, var=error_msg_l, multiplier=None, units=, descr=Failure description for status
2018-09-24 09:38:50 [INFO] --
```

Then.. using this mapping to decode the two-byte values from `normal_info` (using the position as an index to look up the previous mapping)..  `normal_info` also has 22 fields for mine - which matches the response from query_description.

```
2018-09-24 09:38:50 [INFO] tx packet - src=0x1, dst=0x10, function=(17, 2), data=[], len=0, checksum=291
2018-09-24 09:38:50 [INFO] tx packet - aa55010000101102000123
2018-09-24 09:38:50 [INFO] expecting reply of (17, 130)
2018-09-24 09:38:51 [INFO] rx packet - aa550010010011822c007c00480b4600110013097d138d01cdffff0002452e00007ae3000100000000ffff000000000000000000000acb
2018-09-24 09:38:51 [INFO] rx packet - src=0x10, dst=0x100, function=(17, 130), data=b'\x00|\x00H\x0bF\x00\x11\x00\x13\t}\x13\x8d\x01\xcd\xff\xff\x00\x02E.\x00\x00z\xe3\x00\x01\x00\x00\x00\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', len=44, checksum=b'\n'
2018-09-24 09:38:51 [INFO]   [00]->[0x00] Temperature = 12.4 °C (Internal inverter temperature)
2018-09-24 09:38:51 [INFO]   [01]->[0x0d] E-today = 0.72 KW.Hr (The accumulated kWh of day)
2018-09-24 09:38:51 [INFO]   [02]->[0x01] Vpv1 = 288.6 V (PV1 voltage)
2018-09-24 09:38:51 [INFO]   [03]->[0x04] Ipv1 = 1.7000000000000002 A (PV1 current)
2018-09-24 09:38:51 [INFO]   [04]->[0x41] Ipv1 = 1.9000000000000001 A (PV current)
2018-09-24 09:38:51 [INFO]   [05]->[0x42] Vac = 242.9 V (Grid voltage)
2018-09-24 09:38:51 [INFO]   [06]->[0x43] Fac = 50.050000000000004 Hz (Grid frequency)
2018-09-24 09:38:51 [INFO]   [07]->[0x44] Pac = 461 W (Power to grid)
2018-09-24 09:38:51 [INFO]   [08]->[0x45] Zac = 65.535 Ω (Grid Impedance)
2018-09-24 09:38:51 [INFO]   [09]->[0x47] E-Total_H = 0.2 KW.Hr (Total Energy to grid)
2018-09-24 09:38:51 [INFO]   [10]->[0x48] E-Total_L = 1771.0 KW.Hr (Total Energy to grid)
2018-09-24 09:38:51 [INFO]   [11]->[0x49] H-Total_H = 0 Hr (Total operation hours)
2018-09-24 09:38:51 [INFO]   [12]->[0x4a] H-Total_L = 31459 Hr (Total operation hours)
2018-09-24 09:38:51 [INFO]   [13]->[0x4c] Mode = 1  (Operation Mode)
2018-09-24 09:38:51 [INFO]   [14]->[0x78] GVFaultValue = 0.0 V (Grid Voltage Fault Value)
2018-09-24 09:38:51 [INFO]   [15]->[0x79] GFFaultValue = 0.0 Hz (Grid Frequency Fault Value)
2018-09-24 09:38:51 [INFO]   [16]->[0x7a] GZFaultValue = 65.535 Ω (Grid Impedance Fault Value)
2018-09-24 09:38:51 [INFO]   [17]->[0x7b] TmpFaultValue = 0.0 °C (Temperature Fault Value)
2018-09-24 09:38:51 [INFO]   [18]->[0x7c] PV1FaultValue = 0.0 V (PV1 voltage fault value)
2018-09-24 09:38:51 [INFO]   [19]->[0x7d] GFCIFaultValue = 0.0 A (GFCI current fault value)
2018-09-24 09:38:51 [INFO]   [20]->[0x7e] ErrorMesssageH = 0.0  (Failure description for status)
2018-09-24 09:38:51 [INFO]   [21]->[0x7f] ErrorMesssageH = 0.0  (Failure description for status)
2018-09-24 09:38:51 [INFO] kafka send json - {"v_ac": 242.9, "e_today": 0.72, "gz_fault_value": 65.535, "h_total_h": 0, "error_msg_l": 0.0, "timestamp": "2018-09-24T09:38:51.444815", "mode": 1, "i_pv": 1.9000000000000001, "gfci_fault_value": 0.0, "tmp_fault_fault": 0.0, "temp": 12.4, "gv_fault_value": 0.0, "pv1_fault_value": 0.0, "error_msg_h": 0.0, "v_pv1": 288.6, "gf_fault_value": 0.0, "device": "8881500A10B07509", "z_ac": 65.535, "h_total_l": 31459, "f_ac": 50.050000000000004, "e_total_hr": 0.2, "p_ac": 461, "i_pv1": 1.7000000000000002, "e_total_l": 1771.0}
```

That's my take on it anyway.. The Impedance field seems broken on mine - it returns 0xFFFF (hence the 65.535 Ohms.)  Also, I haven't re-assembled the multi-field high/low values yet.

Also, I've trascribed all the definitions in, just incase they pop up.. eg:

```
#
# data definitions
#

DataItem(0x00, 'temp',      'Temperature',     0.1,   '°C',      'Internal inverter temperature')
DataItem(0x01, 'v_pv1',     'Vpv1',            0.1,   'V',       'PV1 voltage')
DataItem(0x02, 'v_pv2',     'Vpv2',            0.1,   'V',       'PV2 voltage')
DataItem(0x04, 'i_pv1',     'Ipv1',            0.1,   'A',       'PV1 current')
DataItem(0x05, 'i_pv2',     'Ipv2',            0.1,   'A',       'PV2 current')
DataItem(0x07, 'e_total_h', 'E-Total_H',       0.1,   'KW.Hr',   'Total Energy to grid')
DataItem(0x08, 'e_total_l', 'E-Total_L',       0.1,   'KW.Hr',   'Total Energy to grid')
DataItem(0x09, 'h_total_h', 'H-Total_H',       1,     'Hr',      'Total operation hours')
DataItem(0x0a, 'h_total_l', 'H-Total_L',       1,     'Hr',      'Total operation hours')
DataItem(0x0b, 'p_ac',      'Pac',             1,     'W',       'Total power to grid')
DataItem(0x0c, 'mode',      'Mode',            1,     '',        'Operation Mode')
DataItem(0x0d, 'e_today',   'E-today',         0.01,  'KW.Hr',   'The accumulated kWh of day')
DataItem(0x20, 'sur_temp',  'surTemp',         0.1,   '°C',      'Ambient Temperature')
DataItem(0x21, 'bd_temp',   'bdTemp',          0.1,   '°C',      'Panel Temperature')
```
.. etc.. There's about 87 of them defind in the protocol document.
