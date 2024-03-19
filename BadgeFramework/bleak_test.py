import asyncio
import queue

import pandas
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import uuid
import struct
import badge
from badge_protocol import Request
import badge_bleak
from hub_connection_bleak import Connection
from badge import OpenBadge


def get_mac_address(df, badge_id: int) -> str:
    mac_address = df[df['Participant Id'] == badge_id]['Mac Address']
    mac_address = list(mac_address)[0]
    return mac_address


UART_SERVICE_UUID = uuid.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
TX_CHAR_UUID = uuid.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
RX_CHAR_UUID = uuid.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
RX_CHAR_UUID_2 = uuid.UUID("00002902-0000-1000-8000-00805F9b34FB")


def is_spcl_midge(device: BLEDevice) -> bool:
    return device.name == 'HDBDG'


def get_device_id(device: BLEDevice, addr_df: pandas.DataFrame) -> int:
    address = device.address.lower()
    try:
        badge_id = addr_df[addr_df['Mac Address'] == address]['Participant Id']
        badge_id = badge_id.values[0]
    except IndexError:
        badge_id = -1000
    return badge_id


def callback(sender: BleakGATTCharacteristic, data: bytearray):
    if len(data) > 0:
        print(f"RX changed {sender}: {data}")


async def main():
    df_badge = pandas.read_csv("mappings_allBackup.csv")
    # Find all devices
    # using both BLEdevice and advertisement data here since it has more information. Also mutes the warning.
    # devices = await badge_scanner.discover(timeout=2.0)
    devices = await BleakScanner.discover(timeout=10.0, return_adv=True)

    # Filter out the devices that are not the midge
    # midges = [d for d in devices if d.name == 'HDBDG']
    devices = [d for d in devices.values() if is_spcl_midge(d[0])]

    # Print Id to see if it matches with any devices in the csv file.
    for ble_device, adv_data in devices:
        device_id = get_device_id(ble_device, df_badge)
        print(f"RSSI: {adv_data.rssi}, Id: {device_id}, Address: {ble_device.address}")

    for ble_device, adv_data in devices:
        # Connect to the midge
        async with BleakClient(ble_device.address) as client:
            serv = client.services
            # char_13 = serv.char_13[-1]
            uart = serv.get_service(UART_SERVICE_UUID)
            # self.uart = self.conn.getServiceByUUID(UART_SERVICE_UUID) # Bluepy equivalent

            rx = serv.get_characteristic(RX_CHAR_UUID)
            # self.rx = self.uart.getCharacteristics(RX_CHAR_UUID)[0] # Bluepy equivalent

            tx = serv.get_characteristic(TX_CHAR_UUID)
            # self.tx = self.uart.getCharacteristics(TX_CHAR_UUID)[0] # Bluepy equivalent
            # my_badge = OpenBadge(client)
            message = b'\x01\x00\x1e'
            # val = struct.pack("<bb", 0x01, 0x00)
            # a = my_badge.get_free_sdc_space()
            # await client.start_notify(11, callback)
            await client.start_notify(rx, callback)
            # await client.write_gatt_char(0x0013, val, response=False)
            await client.write_gatt_char(TX_CHAR_UUID, message, response=True)
            # response_11 = await client.read_gatt_char(11)

            response_rx = b''
            while client.is_connected:
                if len(response_rx) > 0:
                    break
                response_rx = await client.read_gatt_char(RX_CHAR_UUID)
            # handle: 18, data: b'\x10\x00\x05\xbd\x0e\x00\x00\xb7\x0e\x00\x00\x0e\x00\x00\x00\xd2\x01\x00'

            c = 9


            # bleak_badge = badge_bleak.OpenBadge(client)
            # bleak_badge.get_status()
            # c = 9
            # #
            # Option 3, it doesn't crash but not sure if it actually works
            #
            # def callback(sender: BleakGATTCharacteristic, data: bytearray):
            #     print(f"RX changed {sender}: {data}")
            #
            # await client.start_notify(rx, callback)

            print("Done")

        break


if __name__ == "__main__":
    asyncio.run(main())
