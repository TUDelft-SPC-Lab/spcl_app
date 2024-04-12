from __future__ import absolute_import, division, print_function

import logging
import queue
import struct
import time
import bleak
import utils

from badge_connection import BadgeConnection

logger = logging.getLogger(__name__)

# Enable debug output.
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Define service and characteristic UUIDs used by the UART service.


# BLEBadgeConnection represents a connection to 'ble_device', a badge connected over BLE.
#    ('ble_device' should be a device from the Bluefruit Library)
# This class implements the BadgeConnection interface to communicate with
#   a badge over the BLE UART service using the Adafruit BlueFruit Library.
# This class implements an additional class method, BLEBadgeConnection.get_connection_to_badge(),
#   that can be used to retrieve an instance of this class that represents a connection to a badge with
#   the given ID. This class method should be the main way clients instantiate new BLEBadgeConnections.
class BLEBadgeConnection(BadgeConnection):
    def __init__(self, device):
        self.device = device
        # We will set these on connection to be the correct objects from the
        #   Adafruit library.
        self.uart = None
        self.rx = None
        self.tx = None

        # Contains the bytes received from the device. Held here until an entire message is received.
        self.rx_queue = queue.Queue()

        BadgeConnection.__init__(self)

    # Returns a BLEBadgeConnection() to the first badge it sees, or none if a badge
    #   could not be found in timeout_seconds seconds. (Default is 10)

    # Function to receive RX characteristic changes.  Note that this will
    # be called on a different thread so be careful to make sure state that
    # the function changes is thread safe.  Use Queue or other thread-safe
    # primitives to send data to other threads.

    def received(self, data):
        logger.debug("Recieved {}".format(data.hex()))
        for b in data:
            self.rx_queue.put(b)

    # Implements BadgeConnection's connect() spec.
    def connect(self):
        logger.debug("Connecting...")
        self.conn = Peripheral(self.ble_device, btle.ADDR_TYPE_RANDOM)
        # self.conn = Peripheral2(self.ble_device, btle.ADDR_TYPE_RANDOM)
        logger.debug("Connected.")

        # Find the UART service and its characteristics.
        uart = serv.get_service(UART_SERVICE_UUID)
        # self.uart = self.conn.getServiceByUUID(UART_SERVICE_UUID) # Bluepy equivalent

        rx = serv.get_characteristic(RX_CHAR_UUID)
        # self.rx = self.uart.getCharacteristics(RX_CHAR_UUID)[0] # Bluepy equivalent

        tx = serv.get_characteristic(TX_CHAR_UUID)
        # self.tx = self.uart.getCharacteristics(TX_CHAR_UUID)[0] # Bluepy equivalent

        # Turn on notification of RX characteristics
        logger.debug("Subscribing to RX characteristic changes...")
        CONFIG_HANDLE = 0x0013
        # was wrong 0x000c
        self.conn.writeCharacteristic(
            handle=CONFIG_HANDLE, val=struct.pack("<bb", 0x01, 0x00)
        )
        self.conn.setDelegate(SimpleDelegate(bleconn=self))
        c = 9

    # Implements BadgeConnections's disconnect() spec.
    def disconnect(self):

        self.uart = None
        self.tx = None
        self.rx = None

        with self.rx_queue.mutex:
            self.rx_queue.queue.clear()

        # self.ble_device.disconnect()
        self.conn.disconnect()
        self.ble_device = None

    # Implements BadgeConnection's is_connected() spec.
    def is_connected(self):
        return self.client.is_connected

    # Implements BadgeConnection's await_data() spec.
    async def await_data(self, data_len):
        if not self.is_connected():
            raise RuntimeError("BLEBadgeConnection not connected before await_data()!")

        rx_message = b""
        rx_bytes_expected = data_len

        if rx_bytes_expected > 0:
            while True:
                while not self.rx_queue.empty():
                    rx_message += self.rx_queue.get().to_bytes(1, byteorder="big")
                    if len(rx_message) == rx_bytes_expected:
                        return rx_message

    # Implements BadgeConnection's send() spec.
    async def send(self, message, response_len=0):
        if not self.is_connected():
            raise RuntimeError("BLEBadgeConnection not connected before send()!")

        rx_message = b""
        rx_bytes_expected = response_len

        await self.client.write_gatt_char(TX_CHAR_UUID, message, response=True)

        if rx_bytes_expected > 0:
            while True:
                while not self.rx_queue.empty():
                    rx_message += self.rx_queue.get().to_bytes(1, byteorder="big")
                    if len(rx_message) == rx_bytes_expected:
                        return rx_message

                self.conn.waitForNotifications(5.0)
