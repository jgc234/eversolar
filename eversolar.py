#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import json
import serial
import logging
import struct
import collections
import datetime
import argparse

#format = '%(asctime)-15s %(filename)s:%(funcName)s:%(lineno)s [%(levelname)s] %(message)s'
format = '%(asctime)-15s [%(levelname)s] %(message)s'

datefmt="%Y-%m-%d %H:%M:%S"

logging.basicConfig(format=format, datefmt=datefmt)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Device:
    def __init__(self, serial, addr):
        self.serial = serial
        self.addr = addr
        self.field_map = {}
        return
    pass

item_map = {}

class DataItem:
    def __init__(self, code, var, name, multiplier, units, descr):
        self.code = code
        self.var = var
        self.name = name
        self.multiplier = multiplier
        self.units = units
        self.descr = descr
        item_map[code] = self
        return
    pass
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
DataItem(0x22, 'irr',       'irr',             0.1,   'W/m2',    'Rad')
DataItem(0x23, 'wind_speed', 'windSpeed',      0.1,   'm/s',     'Speed of wind')
DataItem(0x38, 'waiting_time', 'waitingTime',  1,     's',       'wait time on connection')
DataItem(0x39, 'tmp_fault_value', 'TmpFaultValue', 0.1, '°C',    'Temperature fault value')
DataItem(0x3a, 'pv1_fault_value', 'PV1FaultValue', 0.1, 'V',     'PV1 voltage fault value')
DataItem(0x3b, 'pv2_fault_value', 'PV2FaultValue', 0.1, 'V',     'PV2 voltage fault value')
DataItem(0x3d, 'gfci_fault_value', ' GFCIFaultValue', 0.001, 'A', 'GFCI current fault value')
DataItem(0x3e, 'error_msg_h', 'ErrorMesssageH', None, '',        'Failure description for status')
DataItem(0x3f, 'error_msg_l', 'ErrorMesssageH', None, '',        'Failure description for status')
#
# Single or R phase.
#
DataItem(0x40, 'v_pv',       'Vpv',             0.1,   'V',       'PV voltage')
DataItem(0x41, 'i_pv',       'Ipv1',            0.1,   'A',       'PV current')
DataItem(0x42, 'v_ac',       'Vac',             0.1,   'V',       'Grid voltage')
DataItem(0x43, 'f_ac',       'Fac',             0.01,  'Hz',      'Grid frequency')
DataItem(0x44, 'p_ac',       'Pac',             1,     'W',       'Power to grid')
DataItem(0x45, 'z_ac',       'Zac',             0.001, 'Ω',       'Grid Impedance')
DataItem(0x46, 'i_pv',       'Ipv',             0.1,   'A',       'PV current')
DataItem(0x47, 'e_total_hr', 'E-Total_H',       0.1,   'KW.Hr',   'Total Energy to grid')
DataItem(0x48, 'e_total_l',  'E-Total_L',       0.1,   'KW.Hr',   'Total Energy to grid')
DataItem(0x49, 'h_total_h',  'H-Total_H',       1,     'Hr',      'Total operation hours')
DataItem(0x4a, 'h_total_l',  'H-Total_L',       1,     'Hr',      'Total operation hours')
DataItem(0x4b, 'power_on',   'Power_On',        None,  '',        'Number of times the inverter starts feeding the grid')
DataItem(0x4c, 'mode',       'Mode',            1,     '',        'Operation Mode')
DataItem(0x78, 'gv_fault_value', 'GVFaultValue', 0.1, 'V',       'Grid Voltage Fault Value')
DataItem(0x79, 'gf_fault_value', 'GFFaultValue', 0.01, 'Hz',     'Grid Frequency Fault Value')
DataItem(0x7a, 'gz_fault_value', 'GZFaultValue', 0.001, 'Ω',     'Grid Impedance Fault Value')
DataItem(0x7b, 'tmp_fault_fault','TmpFaultValue', 0.1, '°C',     'Temperature Fault Value')
DataItem(0x7c, 'pv1_fault_value','PV1FaultValue', 0.1, 'V',      'PV1 voltage fault value')
DataItem(0x7d, 'gfci_fault_value','GFCIFaultValue', 0.1, 'A',    'GFCI current fault value')
DataItem(0x7e, 'error_msg_h', 'ErrorMesssageH', None, '',        'Failure description for status')
DataItem(0x7f, 'error_msg_l', 'ErrorMesssageH', None, '',        'Failure description for status')
#
# S phase
#
DataItem(0x80, 'v_pv2',      'Vpv',              0.1,   'V',       'PV voltage')
DataItem(0x81, 'i_pv_s',      'Ipv1',            0.1,   'A',       'PV current')
DataItem(0x82, 'v_ac_s',      'Vac',             0.1,   'V',       'Grid voltage')
DataItem(0x83, 'f_ac_s',      'Fac',             0.01,  'Hz',      'Grid frequency')
DataItem(0x84, 'p_ac_s',      'Pac',             1,     'W',       'Power to grid')
DataItem(0x85, 'z_ac_s',      'Zac',             0.001, 'Ω',       'Grid Impedance')
DataItem(0x86, 'i_pv_s',      'Ipv',             0.1,   'A',       'PV current')
DataItem(0x87, 'e_total_hr', 'E-Total_H',        0.1,   'KW.Hr',   'Total Energy to grid')
DataItem(0x88, 'e_total_l', 'E-Total_L',       0.1,   'KW.Hr',   'Total Energy to grid')
DataItem(0x89, 'h_total_h', 'H-Total_H',       1,     'Hr',      'Total operation hours')
DataItem(0x8a, 'h_total_l', 'H-Total_L',       1,     'Hr',      'Total operation hours')
DataItem(0x8b, 'power_on',  'Power_On',        None,  '',        'Number of times the inverter starts feeding the grid')
DataItem(0x8c, 'mode',      'Mode',            1,     '',        'Operation Mode')
DataItem(0xb8, 'gv_fault_value', 'GVFaultValue', 0.1, 'V',       'Grid Voltage Fault Value')
DataItem(0xb9, 'gf_fault_value', 'GFFaultValue', 0.01, 'Hz',     'Grid Frequency Fault Value')
DataItem(0xba, 'gz_fault_value', 'GZFaultValue', 0.001, 'Ω',     'Grid Impedance Fault Value')
DataItem(0xbb, 'tmp_fault_fault','TmpFaultValue', 0.1, '°C',     'Temperature Fault Value')
DataItem(0xbc, 'pv1_fault_value','PV1FaultValue', 0.1, 'V',      'PV1 voltage fault value')
DataItem(0xbd, 'gfci_fault_value','GFCIFaultValue', 0.1, 'A',    'GFCI current fault value')
DataItem(0xbe, 'error_msg_h', 'ErrorMesssageH', None, '',        'Failure description for status')
DataItem(0xbf, 'error_msg_l', 'ErrorMesssageH', None, '',        'Failure description for status')
#
# T phase
#
DataItem(0xc0, 'v_pv2',      'Vpv',             0.1,   'V',       'PV voltage')
DataItem(0xc1, 'i_pv_s',      'Ipv1',            0.1,   'A',       'PV current')
DataItem(0xc2, 'v_ac_s',      'Vac',             0.1,   'V',       'Grid voltage')
DataItem(0xc3, 'f_ac_s',      'Fac',             0.01,  'Hz',      'Grid frequency')
DataItem(0xc4, 'p_ac_s',      'Pac',             1,     'W',       'Power to grid')
DataItem(0xc5, 'z_ac_s',      'Zac',             0.001, 'Ω',       'Grid Impedance')
DataItem(0xc6, 'i_pv_s',      'Ipv',             0.1,   'A',       'PV current')
DataItem(0xc7, 'e_total_hr', 'E-Total_H',       0.1,   'KW.Hr',   'Total Energy to grid')
DataItem(0xc8, 'e_total_l', 'E-Total_L',       0.1,   'KW.Hr',   'Total Energy to grid')
DataItem(0xc9, 'h_total_h', 'H-Total_H',       1,     'Hr',      'Total operation hours')
DataItem(0xca, 'h_total_l', 'H-Total_L',       1,     'Hr',      'Total operation hours')
DataItem(0xcb, 'power_on',  'Power_On',        None,  '',        'Number of times the inverter starts feeding the grid')
DataItem(0xcc, 'mode',      'Mode',            1,     '',        'Operation Mode')
DataItem(0xf8, 'gv_fault_value', 'GVFaultValue', 0.1, 'V',       'Grid Voltage Fault Value')
DataItem(0xf9, 'gf_fault_value', 'GFFaultValue', 0.01, 'Hz',     'Grid Frequency Fault Value')
DataItem(0xfa, 'gz_fault_value', 'GZFaultValue', 0.001, 'Ω',     'Grid Impedance Fault Value')
DataItem(0xfb, 'tmp_fault_fault','TmpFaultValue', 0.1, '°C',     'Temperature Fault Value')
DataItem(0xfc, 'pv1_fault_value','PV1FaultValue', 0.1, 'V',      'PV1 voltage fault value')
DataItem(0xfd, 'gfci_fault_value','GFCIFaultValue', 0.1, 'A',    'GFCI current fault value')
DataItem(0xfe, 'error_msg_h', 'ErrorMesssageH', None, '',        'Failure description for status')
DataItem(0xff, 'error_msg_l', 'ErrorMesssageH', None, '',        'Failure description for status')

device_map = {}

class Eversolar:

    ##
    ##
    functions = {
        'register_offline_query'         : ((0x10, 0x00), (0x10, 0x80)),
        'register_send_register_address' : ((0x10, 0x01), (0x10, 0x81)),
        'register_remove_register'       : ((0x10, 0x02), (0x10, 0x82)),
        'register_re_connect'            : ((0x10, 0x03), None),
        'register_re_register'           : ((0x10, 0x04), None),
        'read_query_description'         : ((0x11, 0x00), (0x11, 0x80)),
        'read_query_normal_info'         : ((0x11, 0x02), (0x11, 0x82)),
        'read_query_inverter_id'         : ((0x11, 0x03), (0x11, 0x83)),
    }

    ##
    ##
    def __init__(self, port_filename):
        self.port_filename = port_filename
        self.addr = 0x01
        self.next_addr = 0x10
        self.open_port()
        return

    ##
    ##
    def open_port(self):
        self.port = serial.Serial()
        self.port.port = self.port_filename
        self.port.baudrate = 9600
        self.port.parity = serial.PARITY_NONE
        self.port.stopbits = serial.STOPBITS_ONE
        self.port.bytesize = serial.EIGHTBITS
        self.port.timeout = 1
        self.port.open()
        return

    ##
    ##
    def register(self):
        log.info('register')
        reply = self.send_request(self.addr, 0x00, self.functions['register_offline_query'])

        log.info('register reply=%s', reply)
        if not reply:
            log.error('wrong response from register_offline_query')
            return

        serial = reply
        addr = self.next_addr
        self.next_addr += 1
        data = serial + struct.pack('B', addr)
        reply = self.send_request(self.addr, 0x00, self.functions['register_send_register_address'], data)
        if not reply:
            log.error('register_send_register_address failed')
            return

        ack, = struct.unpack('B', reply)
        log.info('ack =%s, type=%s, reply=%s', ack, type(ack), reply)
        if ack != 0x06:
            log.error('wrong acknowledgement code for from register_send_register_address response')
            return

        device = Device(serial, addr)
        device_map[serial] = device

        comm.get_inverter_id(device)
        comm.get_inverter_descr(device)

        return

    ##
    ##
    def get_inverter_id(self, device):
        data = self.send_request(self.addr, device.addr, self.functions['read_query_inverter_id'])
        if not data:
            log.error('failed to get data from id request')
            return
        phase, rating, firmware, model, manufacturer, serial, nomv = struct.unpack('!B6s5s16s16s16s4s', data[:64])
        log.info(' INFO phase=%s, rating=%s, firmware=%s, model=%s, manufacturer=%s, serial=%s, nomv=%s',
                 phase, rating, firmware, model, manufacturer, serial, nomv)
        device.phase = phase
        device.rating = rating
        device.firmware = firmware
        device.manufacturer = manufacturer
        device.nomv = nomv
        return

    ##
    ##
    def get_inverter_descr(self, device):
        data = self.send_request(self.addr, device.addr, self.functions['read_query_description'])
        if not data:
            log.error('failed to get data from query description')
            return

        for i in range(0, len(data)):
            value = data[i]
            item = item_map.get(value)
            device.field_map[i] = item

            if item is None:
                info = '(missing)'
            else:
                info = 'code=0x%02x, var=%s, multiplier=%s, units=%s, descr=%s' % (
                    item.code, item.var, item.multiplier, item.units, item.descr)
                pass

            log.info(' map [%02d] -> %s', i, info)
            pass

        return

    def get_inverter_info(self, device):
        log.info('--')

        output = {}

        data = self.send_request(self.addr, device.addr, self.functions['read_query_normal_info'])
        if not data:
            log.error('failed to get data from info request')
            return

        output['device'] = device.serial.decode()
        output['timestamp'] = datetime.datetime.now().isoformat()

        for index in range(0, int(len(data) / 2)):
            offset = index * 2
            chunk = data[offset:offset+2]
            raw_value, = struct.unpack('!H', chunk)

            dataitem = device.field_map.get(index)
            if not dataitem: continue

            if dataitem.multiplier:
                value = raw_value * dataitem.multiplier
                pass

            log.info('  [%02d]->[0x%02x] %s = %s %s (%s)', index, dataitem.code, dataitem.name, value, dataitem.units, dataitem.descr)
            output[dataitem.var] = value

            pass

        return output

    ##
    ##
    def send_request(self, src_addr, dst_addr, function_info, data=[]):

        tx_info, rx_info = function_info

        #
        # build packet
        #
        packet = bytearray()
        packet.extend((0xAA, 0x55))
        packet.extend((src_addr, 0x00))
        packet.extend((0x00, dst_addr))
        packet.extend(tx_info)
        packet.append(len(data))
        packet.extend(data)
        checksum = sum(packet)
        packet.extend(struct.pack('!H', checksum & 0xFFFF))

        log.info('tx packet - src=0x%X, dst=0x%X, function=%s, data=%s, len=%s, checksum=%s', src_addr, dst_addr, tx_info, data, len(data), checksum) 

        log.info('tx packet - %s', packet.hex())

        self.port.write(packet)

        if rx_info is None:
            log.info('not expecting a response')
            return
        log.info('expecting reply of %s', rx_info)
        return self.receive_request(rx_info)

    ##
    ##
    def receive_request(self, rx_info):

        packet = self.port.read(256)
        if not packet: return

        log.info('rx packet - %s', packet.hex())

        length = len(packet)
        header, src_addr, dst_addr, control, function, data_len = struct.unpack('!HHHBBB', packet[0:9])
        data = packet[9:9+data_len]
        checksum = packet[-2:-1]

        log.info('rx packet - src=0x%X, dst=0x%X, function=%s, data=%s, len=%s, checksum=%s', src_addr, dst_addr, rx_info, data, len(data), checksum)

        return data

    ##
    ##
    def re_register_all(self):

        for i in range(0,3):
            self.send_request(self.addr, 0x00, self.functions['register_re_register'])
            pass

        return

    pass

##
##
##

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Eversolar PV Inverter protocol reader')
    parser.add_argument('--debug', type=str, default='info', help='debug level debug, info, warn, etc')
    parser.add_argument('--kafka', type=str, help='optional kafka address to send messages to')
    parser.add_argument('--kafka-topic', type=str, default='pvsolar', help='kafka topic name')
    parser.add_argument('--serial', type=str, help='filename of serial device (eg /dev/ttyUSB0)')
    parser.add_argument('--syslog', default=False, action='store_true', help='enable logging to syslog')

    args = parser.parse_args()

    log.setLevel(logging.getLevelName(args.debug.upper()))

    log.debug('called with args - %s', args)

    if not args.serial:
        parser.print_help()
        sys.exit(1)
        pass

    if args.kafka:
        import kafka
        producer = kafka.KafkaProducer(bootstrap_servers=[args.kafka], )
    else:
        producer = None
        pass

    if args.syslog:
        import syslog
        syslog.openlog(ident='eversolar', facility=syslog.LOG_USER)
    else:
        syslog = False
        pass

    comm = Eversolar(args.serial)

    comm.re_register_all()
    comm.register()

    time_previous = time.time()

    while 1:

        for device in device_map.values():
            results = comm.get_inverter_info(device)

            keys = sorted(output.keys())
            json_output = json.dumps(results).encode('utf-8')
            kv_output = ' '.join( [ '%s=%s' % (k, results[k]) for k in keys ] )

            if producer:
                producer.send(args.kafka_topic, json_output)
                pass

            if syslog:
                syslog.syslog(kv_output)
                pass

            log.info('output=%s', kv_output)
            pass

        time.sleep(9)
        time_now = time.time()

        if time_now - time_previous > 60:
            time_previous = time_now
            comm.register()
            pass

        pass

    pass

