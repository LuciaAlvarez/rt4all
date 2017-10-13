#! /usr/bin/env python

"""
Modbus module
"""

__author__ = 'Javi Ortega'
__copyright__ = 'Copyright (C) 2017'
__license__ = 'MIT (expat) License'
__version__ = '0.1'
__maintainer__ = 'Javi Ortega'
__email__ = 'javier.ortega@whitewallenergy.com'


import platform
import sys
import os
import serial
import struct
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rs485 import rs485

DIR_SERIAL_PORT_MIPS = '/dev/ttyATH0'
DIR_SERIAL_PORT_LINUX = '/dev/ttyUSB0'
PLATFORM_MIPS = 'mips' == platform.machine()

DEFAULT_PORT = DIR_SERIAL_PORT_MIPS if PLATFORM_MIPS else DIR_SERIAL_PORT_LINUX


"""
Average error is 0.00028 seg.
Average enable write is 0.00000369240 seg.
Average disable write is 0.00000364015 seg.

8N1

C071    BAUDRATE    N_BYTES    TIME_SLEEP    (TIME_SLEEP/N_BYTES) seg.
3       2400        255        ---           0.0046
4       4800        255        ---           0.0023
5       9600        255        0.27          0.0010588235294117648
6       19200       255        0.14          0.0005490196078431374
7       38400       255        0.07          0.0002745098039215687
8       57600       255        0.045         0.0001764705882352941
9       76800       N O     S O P O R T A D O     E N     I V Y
10      115200      255        0.0215        0.00008431372549019607

MX 2
[]   => sin respuesta

        8N1     8N2     8E1     8E2     8O1     8O2
2400    ok
4800    ok
9600    ok      ok      []      []      []      ok
19200   ok
38400   ok
57600   ok
115200  ok
"""

BAUDRATE_2400 = 2400
BAUDRATE_4800 = 4800
BAUDRATE_9600 = 9600
BAUDRATE_19200 = 19200
BAUDRATE_38400 = 38400
BAUDRATE_57600 = 57600
BAUDRATE_115200 = 115200

MODBUS_ASCII = 'ASCII'
MODBUS_RTU = 'RTU'

COLON = '\x35'
CARRIAGE_RETURN = '\x0D'
LINE_FEED = '\x0A'

BYTE_MAX_FRAME = 255    #: Maximum frame
FRAME_END_RTU = 3.5
FRAME_END_ASCII = CARRIAGE_RETURN + LINE_FEED

ALL_PROTOCOL = [MODBUS_RTU, MODBUS_ASCII]  #: Protocol support
ALL_BAUDRATE = [BAUDRATE_2400, BAUDRATE_4800, BAUDRATE_9600, BAUDRATE_19200, BAUDRATE_38400, BAUDRATE_57600, BAUDRATE_115200] #: Baud rate support
ALL_PARITY = [serial.PARITY_NONE, serial.PARITY_ODD]        #: Parity support
ALL_STOPBITS = [serial.STOPBITS_ONE, serial.STOPBITS_TWO]   #: Stop bits support
ALL_BYTESIZE = [serial.EIGHTBITS]                           #: Bytesize support

DEFAULT_PROTOCOL = ALL_PROTOCOL[0]      #: Protcol default
DEFAULT_BAUDRATE = ALL_BAUDRATE[2]      #: Baud rate default
DEFAULT_PARITY = ALL_PARITY[0]          #: Parity default
DEFAULT_STOPBITS = ALL_STOPBITS[0]      #: Stop bits default
DEFAULT_BYTESIZE = ALL_BYTESIZE[0]      #: Bytesize default
DEFAULT_TIMEOUT = None                  #: Timeout default
DEFAULT_DELAY = 0                       #: Delay default

BYTE_PER_SEC_2400 = 0.0046              #: Seconds to transfer a byte to 2400 baud
BYTE_PER_SEC_4800 = 0.0023              #: Seconds to transfer a byte to 4800 baud
BYTE_PER_SEC_9600 = 0.0012              #: Seconds to transfer a byte to 9600 baud
BYTE_PER_SEC_19200 = 0.000573           #: Seconds to transfer a byte to 19200 baud
BYTE_PER_SEC_38400 = 0.000286           #: Seconds to transfer a byte to 38400 baud
BYTE_PER_SEC_57600 = 0.000177           #: Seconds to transfer a byte to 57600 baud
BYTE_PER_SEC_115200 = 0.00095           #: Seconds to transfer a byte to 115200 baud

class Modbus:
    """"""
    def __init__(self, port = DEFAULT_PORT, baudrate = DEFAULT_BAUDRATE, bytesize = DEFAULT_BYTESIZE, parity = DEFAULT_PARITY, stopbits = DEFAULT_STOPBITS, timeout = None, delay = DEFAULT_DELAY, protocol = DEFAULT_PROTOCOL):
        """
        :param port: Port
        :param baudrate: Baud rate
        :param bytesize: Number of data bits
        :param parity: Enable parity checking
        :param stopbits: Number of stop bits
        :param timeout: Set a read timeout value
        :param delay: Set a read delay value
        :param protocol: Communication protocol

        :type port: string
        :type baudrate: integer
        :type bytesize: integer
        :type parity: char
        :type stopbits: integer
        :type timeout: float
        :type delay: float
        :type protocol: string
        """
        self.rs485 = rs485.Rs485()
        self.serial = None

        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits

        if timeout == None:
            self.timeout = self.get_time_transfer(BYTE_MAX_FRAME, self.baudrate)
        else:
            self.timeout = timeout

        self.delay = delay
        self.protocol = protocol

        self.set_serial(self.port, self.baudrate, self.bytesize, self.parity, self.stopbits, self.timeout, self.delay, self.protocol)

    def set_serial(self, port = None, baudrate = None, bytesize = None, parity = None, stopbits = None, timeout = None, delay = None, protocol = None):
        """
        Create a new pySerial.
        Default timeout is get_time_transfer(255, baudrate)
        pySerial.timeout = (timeout + delay)

        :param port: Port
        :param baudrate: Baud rate
        :param bytesize: Number of data bits
        :param parity: Enable parity checking
        :param stopbits: Number of stop bits
        :param timeout: Set a read timeout value
        :param delay: Set a read delay value

        :type port: string
        :type baudrate: integer
        :type bytesize: integer
        :type parity: char
        :type stopbits: integer
        :type timeout: float
        :type delay: float

        :returns: Serial
        :rtype: pySerial, None
        """
        self.serial_close()

        if not port == None:
            self.port = port

        if not baudrate == None:
            self.baudrate = baudrate

        if not bytesize == None:
            self.bytesize = bytesize

        if not parity == None:
            self.parity = parity

        if not stopbits == None:
            self.stopbits = stopbits

        if not timeout == None:
            self.timeout = timeout

        if not delay == None:
            self.delay = delay

        if not protocol == None:
            self.protocol = protocol

        try:
            self.serial = serial.Serial(
                port = self.port,
                baudrate = self.baudrate,
                bytesize = self.bytesize,
                parity = self.parity,
                stopbits = self.stopbits,
                timeout = (self.timeout + self.delay)
            )
            return self.serial

        except Exception as e:
            print 'Serial exception', e
            self.serial = None

    def set_port(self, port = DEFAULT_PORT):
        """
        If pySerial already existed modify port else create a new pyserial with default values and new port

        :param port: Port
        :type port: string

        :returns: Serial
        :rtype: pySerial
        """
        return self.set_serial(port = port)

    def set_baudrate(self, baudrate = DEFAULT_BAUDRATE):
        """
        If pySerial already existed modify baudrate else create a new pyserial with default values and new baudrate

        :param baudrate: Baud rate
        :type baudrate: integer

        :returns: Serial
        :rtype: pySerial
        """
        return self.set_serial(baudrate = baudrate)

    def set_bytesize(self, bytesize = DEFAULT_BYTESIZE):
        """
        If pySerial already existed modify bytesize else create a new pyserial with default values and new bytesize

        :param bytesize: Number of data bits
        :type bytesize: integer

        :returns: Serial
        :rtype: pySerial
        """
        return self.set_serial(bytesize = bytesize)

    def set_parity(self, parity = DEFAULT_PARITY):
        """
        If pySerial already existed modify parity else create a new pyserial with default values and new parity

        :param parity: Enable parity checking
        :type parity: char

        :returns: Serial
        :rtype: pySerial
        """
        return self.set_serial(parity = parity)

    def set_stopbits(self, stopbits = DEFAULT_STOPBITS):
        """
        If pySerial already existed modify stopbits else create a new pyserial with default values and new stopbits

        :param stopbits: Number of stop bits
        :type stopbits: integer

        :returns: Serial
        :rtype: pySerial
        """
        return self.set_serial(stopbits = stopbits)

    def set_timeout(self, timeout = DEFAULT_TIMEOUT):
        """
        If pySerial already existed modify timeout else create a new pyserial with default values and new timeout

        :param timeout: Set a read timeout value
        :type timeout: float

        :returns: Serial
        :rtype: pySerial
        """
        return self.set_serial(timeout = timeout)

    def set_delay(self, delay = DEFAULT_DELAY):
        """
        If pySerial already existed modify delay else create a new pyserial with default values and new delay

        :param delay: Set a read delay value
        :type delay: float

        :returns: Serial
        :rtype: pySerial
        """
        return self.set_serial(delay = delay)

    def set_protocol(self, protocol = DEFAULT_PROTOCOL):
        """
        Update communication protocol

        :param protocol: New protocol
        :type delay: string

        :returns: Current protocol
        :rtype: string
        """
        self.protocol = protocol
        return self.protocol

    def set_tx_enable(self):
        """
        Call `rs485.set_tx_enable()`

        :returns: GPIO Address, 0/None to error
        :rtype: integer, None
        """
        if not self.is_tx_enable():
            return self.rs485.set_tx_enable()

    def set_rx_enable(self):
        """
        Call `rs485.set_rx_enable()`

        :returns: GPIO Address, 0/None to error
        :rtype: integer, None
        """
        if not self.is_rx_enable():
            return self.rs485.set_rx_enable()

    def get_serial(self):
        """
        :returns: Serial
        :rtype: pySerial
        """
        return self.serial

    def get_port(self):
        """
        :returns: Port pySerial
        :rtype: string, None
        """
        if self.serial:
            return self.serial.port

    def get_baudrate(self):
        """
        :returns: Baud rate pySerial
        :rtype: integer, None
        """
        if self.serial:
            return self.serial.baudrate

    def get_bytesize(self):
        """
        :returns: Number of data bits pySerial
        :rtype: integer, None
        """
        if self.serial:
            return self.serial.bytesize

    def get_parity(self):
        """
        :returns: Parity pySerial
        :rtype: char, None
        """
        if self.serial:
            return self.serial.parity

    def get_stopbits(self):
        """
        :returns: Number of stop bits pySerial
        :rtype: integer, None
        """
        if self.serial:
            return self.serial.stopbits

    def get_timeout(self):
        """
        :returns: Timeout
        :rtype: float, None
        """
        if self.serial:
            return self.timeout

    def get_delay(self):
        """
        :returns: Delay
        :rtype: float, None
        """
        if self.serial:
            return self.delay

    def get_protocol(self):
        """
        :returns: Protocol
        :rtype: string
        """
        return self.protocol

    def get_supported_parity(self):
        """
        :returns: All supported parity
        :rtype: Array (integer)
        """
        return ALL_PARITY

    def get_supported_stopbits(self):
        """
        :returns: All supported stopbits
        :rtype: Array (integer)
        """
        return ALL_STOPBITS

    def get_supported_protocol(self):
        """
        :returns: All supported Protocol
        :rtype: Array (string)
        """
        return ALL_PROTOCOL

    def get_supported_baudrate(self):
        """
        :returns: All supported baudrate
        :rtype: Array (integer)
        """
        return ALL_BAUDRATE

    def get_supported_bytesize(self):
        """
        :returns: All supported bytesize
        :rtype: Array (integer)
        """
        return ALL_BYTESIZE

    def get_time_transfer(self, tx_bytes=0, baud=None):
        """
        :param tx_bytes: Number of byte to transfer
        :param baud: Baud rate to transfer. If baud is None, get_baudrate()

        :type tx_bytes: float
        :type baud: integer, None

        :returns: Seconds to transfer, -1 if baud not supported
        :rtype: float
        """
        result = -1

        if baud == None:
            baud = self.get_baudrate()

        if baud == BAUDRATE_2400:
            result = tx_bytes*BYTE_PER_SEC_2400
        elif baud == BAUDRATE_4800:
            result = tx_bytes*BYTE_PER_SEC_4800
        elif baud == BAUDRATE_9600:
            result = tx_bytes*BYTE_PER_SEC_9600
        elif baud == BAUDRATE_19200:
            result = tx_bytes*BYTE_PER_SEC_19200
        elif baud == BAUDRATE_38400:
            result = tx_bytes*BYTE_PER_SEC_38400
        elif baud == BAUDRATE_57600:
            result = tx_bytes*BYTE_PER_SEC_57600
        elif baud == BAUDRATE_115200:
            result = tx_bytes*BYTE_PER_SEC_115200

        return result

    def get_time_silent(self, baud=None):
        """
        :param baud: Baud rate to transfer. If baud is None, get_baudrate()
        :type baud: integer, None

        :returns: Call `self.get_time_transfer(3.5)`
        :rtype: float
        """
        return self.get_time_transfer(FRAME_END_RTU, baud)

    def get_lrc(self, tx):
        """
        Used ASCII MODE
        http://www.simplymodbus.ca/ASCII.htm

        :param tx: Bytes to transfer

        :type tx: bytes

        :returns: One bytes
        :rtype: Buffer of bytes
        """
        lrc = 0

        for b in tx:
            lrc += int(struct.unpack('B', b)[0])
        return struct.pack('B', (-lrc & 0xFF))

    def get_crc(self, tx, is_big_endian = True):
        """
        Used RTU MODE

        :param tx: Bytes to transfer
        :param is_big_endian: Set big o little endian

        :type tx: bytes
        :type is_big_endian: bool

        :returns: Two bytes (crc16)
        :rtype: Buffer of bytes
        """
        bits = 8
        crc = 0xFFFF
        for x in struct.unpack(str(len(tx))+'c', tx):
            """ x = '\xF5' op = F code = 5 """
            op = '0'
            code = '0'
            if x != 0:
                if isinstance( x, int ):
                    value = hex(x)
                else:
                    value = hex(ord(x))

                if len(value) == 4:
                    op = (value[2:3])
                    code = (value[3:4])
                else:
                    code = (value[2:3])

            crc = crc ^ int(op+code, 16)
            for bit in range(0, bits):
                if (crc&0x0001)  == 0x0001:
                    crc = ((crc >> 1) ^ 0xA001)
                else:
                    crc = crc >> 1

        if is_big_endian:
            result = struct.pack('<H', (crc & 0xFFFF))
        else:
            result = struct.pack('>H', (crc & 0xFFFF))

        return result

    def is_tx_enable(self):
        """
        :returns: Call `rs485.is_tx_enable()`
        :rtype: boolean
        """
        return self.rs485.is_tx_enable()

    def is_rx_enable(self):
        """
        :returns: Call `rs485.is_rx_enable()`
        :rtype: boolean
        """
        return self.rs485.is_rx_enable()

    def raw(self, tx, byte_read = 255):
        """
        :param tx: Buffer to transfer
        :param byte_read: Number of bytes to read

        :type tx: Bytes
        :type byte_read: integer

        :returns: Response
        :rtype: Buffer of bytes, None
        """
        self.set_tx_enable()
        self.write(tx)
        self.sleep_tx(len(tx))
        self.set_rx_enable()
        return self.read(byte_read)

    def write(self, tx):
        """
        :param tx: Buffer to transfer
        :type tx: Buffer of bytes

        :returns: Number of byte written
        :rtype: int, None
        """
        if self.serial:
            try:
                return self.serial.write(tx)
            except Exception as e:
                print 'Write exception', e
                # self.serial_close()

    def read(self, num_bytes=255):
        """
        :param num_byte: Number of bytes to read
        :type num_byte: integer

        :returns: Buffer of bytes readed
        :rtype: Buffer of bytes, None
        """
        if self.serial:
            try:
                return self.serial.read(num_bytes)
            except Exception as e:
                print 'Read exception', e
                # self.serial_close()

    def sleep_tx(self, num_bytes):
        """
        Call `time.sleep(get_time_transfer(num_byte))`

        :param num_byte: Number of bytes to write
        :type num_byte: integer
        """
        time.sleep(self.get_time_transfer(num_bytes))

    def rtu_to_ascii(self, tx, colon = False, lrc = False, carriage_return = False, line_feed = False):
        """
        Turn from tx_rtu to tx_ascii
        tx_rtu = '\x01\x03...'
        tx_ascii = '\x30\x31\x30\x33...'

        :param tx: Buffer of bytes
        :param colon: Add colon (\x35) to the beginning
        :param lrc: Add lrc
        :param carriage_return: Add carriage (\x0D) return at the end
        :param line_feed: Add line feed (\x0A) at the end

        :type tx: Buffer of bytes
        :type colon: bool
        :type lrc: bool
        :type carriage_return: bool
        :type line_feed: bool

        :returns: Buffer of bytes readed
        :rtype: Buffer of bytes, None
        """
        tx_ascii = ''

        for x in tx:
            tmp = struct.unpack('cc', x.encode('hex'))
            tx_ascii += tmp[0].upper() + tmp[1].upper()

        if lrc:
            tx_ascii += self.get_lrc(tx_ascii)

        if colon:
            tx_ascii = COLON + tx_ascii

        if carriage_return:
            tx_ascii += CARRIAGE_RETURN

        if line_feed:
            tx_ascii += LINE_FEED

        return tx_ascii.upper()

    def serial_close(self):
        """
        Close pySerial
        """
        if self.serial:
            self.serial.close()

        self.serial = None

    def __del__(self):
        """"""
        self.serial_close()

if __name__ == "__main__":
    """"""
    debug = False

    if debug:
        m = Modbus(port = None)
        tx_rtu = '\x11\x03\x00\x6B\x00\x03'
        tx_ascii = '\x31\x31\x30\x33\x30\x30\x36\x42\x30\x30\x30\x33'

        print 'RTU', list(tx_rtu)
        print 'ASCII', list(tx_ascii)

        crc_msb = m.get_crc(tx_rtu, is_big_endian = True)
        crc_lsb = m.get_crc(tx_rtu, is_big_endian = False)

        if crc_msb[0] == '\x76' and crc_msb[1] == '\x87':
            print 'OK <-- Check CRC-MSB'
        else:
            print 'FAILURE <-- Check CRC-MSB'

        if crc_lsb[0] == '\x87' and crc_lsb[1] == '\x76':
            print 'OK <-- Check CRC-LSB'
        else:
            print 'FAILURE <-- Check CRC-LSB'

        if m.get_lrc(tx_rtu) == '\x7E':
            print 'OK <-- Check LRC'

        if m.rtu_to_ascii(tx_rtu) == tx_ascii:
            print 'OK <-- Check RTU_TO_ASCII'
        else:
            print 'FAILURE <-- Check RTU_TO_ASCII'

        if m.rtu_to_ascii(tx_rtu, colon=True, carriage_return=True, line_feed=True) == COLON + tx_ascii + CARRIAGE_RETURN + LINE_FEED:
            print 'OK <-- Check RTU_TO_ASCII colon+cr+lf'
        else:
            print 'FAILURE <-- Check RTU_TO_ASCII colon+cr+lf'

        if m.get_lrc(m.rtu_to_ascii(tx_rtu)) == m.get_lrc(tx_ascii):
            print 'OK <-- Check m.get_lrc(m.rtu_to_ascii(tx_rtu)) == m.get_lrc(tx_ascii)'
        else:
            print 'FAILURE <-- Check m.get_lrc(m.rtu_to_ascii(tx_rtu)) == m.get_lrc(tx_ascii)'

        if m.rtu_to_ascii(tx_rtu, lrc=True) == ( tx_ascii + m.get_lrc(tx_ascii)):
            print 'OK <-- Check m.rtu_to_ascii(tx_rtu, lrc=True) == ( tx_ascii + m.get_lrc(tx_ascii))'
        else:
            print 'FAILURE  <-- Check m.rtu_to_ascii(tx_rtu, lrc=True) == ( tx_ascii + m.get_lrc(tx_ascii))'

    m = Modbus()

    # MX Diagnostic
    # tx = '\x01\x08\x00\x00\xAB\xCE'

    # MX Read register F002
    tx = '\x01\x03\x11\x02\x00\x02'
    tx += m.get_crc(tx)
    # rx = list(m.raw(tx))

    #print 'break_condition', m.serial.break_condition

    tx = ''
    for i in xrange(255):
        tx += struct.pack('B', i)


    # RAW
    m.set_tx_enable()
    m.write(tx)
    m.serial.flush()
    #m.sleep_tx(len(tx))

    # m.serial.setBreak(True)


    m.set_rx_enable()
    rx = list(m.read())
    # ---

    print rx

    if rx:
        print 'F002', struct.unpack('B', rx[5])[0]*16*16 + struct.unpack('B', rx[6])[0]
    else:
        print 'F002 unknow'



    # MX Write registers F002
    # tx = '\x01\x10\x10\x13\x00\x02\x04\x00\x04\x93\xE0'

    #tx += m.get_crc(tx)
    #print list(m.raw(tx))

    """
    tx = '\x01\x03\x00\x20\x00\x01'
    tx += m.get_crc(tx)

    print m.get_serial()
    print m.raw(tx)
    """



    """
    m.set_parity('O')
    m.set_parity('N')
    tx = '\x02\x03\x00\x20\x00\x03\x04\x32'

    m.set_tx_enable()
    m.write(tx)
    m.sleep_tx(len(tx))
    m.set_rx_enable()
    m.read(1024)
    """