import pandas as pandas
from bluepy import btle
import uuid
import logging
import struct
import queue
from bluepy.btle import Peripheral
from ble_badge_connection import Peripheral2
from badge import OpenBadge
import time
import badge_protocol

UART_SERVICE_UUID = uuid.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
TX_CHAR_UUID = uuid.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
RX_CHAR_UUID = uuid.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")

logger = logging.getLogger(__name__)


class SimpleBadge:
    def __init__(self, q: queue.Queue):
        self.queue = q

    def receive(self, data):
        for b in data:
            self.queue.put(b)

    def await_data(self, conn, data_len):
        rx_message = b""
        rx_bytes_expected = data_len

        if rx_bytes_expected > 0:
            while True:
                while not self.queue.empty():
                    rx_message += self.queue.get().to_bytes(1, byteorder="big")
                    if len(rx_message) == rx_bytes_expected:
                        return rx_message

                conn.waitForNotifications(5.0)

    def send(self, conn, tx: btle.Characteristic, message, response_len=0):
        rx_message = b""
        rx_bytes_expected = response_len

        tx.write(message, withResponse=True)
        conn.waitForNotifications(5.0)
        # if True:
        # while True:
        while not self.queue.empty():
            rx_message += self.queue.get().to_bytes(1, byteorder="big")
            if len(rx_message) >= 18:
                break
        return rx_message
                # if len(rx_message) == rx_bytes_expected:
                #     return rx_message


class SimpleDelegate2(btle.DefaultDelegate):
    def __init__(self, badge: SimpleBadge):
        btle.DefaultDelegate.__init__(self)
        self.badge = badge

    def handleNotification(self, cHandle, data):
        print(f'handle: {cHandle}, data:{data}')
        self.badge.receive(data)


def main():
    df = pandas.read_csv("mappings_allBackup.csv")
    # df = pd.read_csv("mappings_all.csv")
    devices_id = [29]  # test with 1 midge
    df = df[df["Participant Id"].isin(devices_id)]
    for _, row in df.iterrows():
        current_participant: int = row["Participant Id"]
        current_mac: str = row["Mac Address"]
        conn = Peripheral(current_mac, btle.ADDR_TYPE_RANDOM)
        # self.conn = Peripheral2(self.ble_device, btle.ADDR_TYPE_RANDOM)

        # Find the UART service and its characteristics.
        uart = conn.getServiceByUUID(UART_SERVICE_UUID)
        rx = uart.getCharacteristics(RX_CHAR_UUID)[0]
        tx = uart.getCharacteristics(TX_CHAR_UUID)[0]

        # Turn on notification of RX characteristics
        logger.debug("Subscribing to RX characteristic changes...")
        CONFIG_HANDLE = 0x0013
        # was wrong 0x000c
        get_free_sdc_space = b'\x01\x00\x1e'
        start_microphone = b'\x08\x00\x02\xc6\xa2\xf9ek\x02\x01'
        stop_microphone = b'\x01\x00\x03'
        val = struct.pack("<bb", 0x01, 0x00)

        badge = SimpleBadge(queue.Queue())
        # badge_bluepy = OpenBadge(conn)
        # badge_bluepy.start_microphone()
        # badge_bluepy.stop_microphone()
        # characteristics = conn.getCharacteristics()
        # descriptors = conn.getDescriptors()
        # services = conn.getServices()

        conn.writeCharacteristic(handle=CONFIG_HANDLE, val=val)
        conn.setDelegate(SimpleDelegate2(badge=badge))

        message = badge.send(conn, tx, get_free_sdc_space)
        response_len = struct.unpack("<H", badge.await_data(conn, 2))[0]
        message = badge.await_data(conn, response_len)
        decoded_message_space = badge_protocol.Response.decode(message)

        message = badge.send(conn, tx, start_microphone)
        response_len = struct.unpack("<H", badge.await_data(conn, 2))[0]
        message = badge.await_data(conn, response_len)
        decoded_message_start = badge_protocol.Response.decode(message)
        time.sleep(6)
        # send(conn, tx, stop_microphone)
        message = badge.send(conn, tx, stop_microphone)

        # handle: 18, data: b'\x10\x00\x05\xbd\x0e\x00\x00\xb7\x0e\x00\x00\x0e\x00\x00\x00\xd2\x01\x00'
        c = 9


# I think this makes sense. Further proofs are that characteristic 5 has properties 12
# which is the combination of 4+8,
# indication that we can do WRITE and WRITE_NO_RESP on tx. Similarly,

if __name__ == "__main__":
    main()
