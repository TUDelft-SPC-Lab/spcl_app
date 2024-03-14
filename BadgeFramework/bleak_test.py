import asyncio

import pandas
import pandas as pd
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import uuid
import struct


def get_mac_address(df, badge_id: int) -> str:
    mac_address = df[df['Participant Id'] == badge_id]['Mac Address']
    mac_address = list(mac_address)[0]
    return mac_address


UART_SERVICE_UUID = uuid.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
TX_CHAR_UUID = uuid.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
RX_CHAR_UUID = uuid.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")


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


async def main():
    df_badge = pd.read_csv("mappings_allBackup.csv")
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

            uart = serv.get_service(UART_SERVICE_UUID)
            # self.uart = self.conn.getServiceByUUID(UART_SERVICE_UUID) # Bluepy equivalent

            rx = serv.get_characteristic(RX_CHAR_UUID)
            # self.rx = self.uart.getCharacteristics(RX_CHAR_UUID)[0] # Bluepy equivalent

            tx = serv.get_characteristic(TX_CHAR_UUID)
            # self.tx = self.uart.getCharacteristics(TX_CHAR_UUID)[0] # Bluepy equivalent

            # Trying to replicate this bluepy code with bleak

            # # Turn on notification of RX characteristics
            # logger.debug("Subscribing to RX characteristic changes...")
            # CONFIG_HANDLE = 0x0013
            # # was wrong 0x000c
            # self.conn.writeCharacteristic(
            #     handle=CONFIG_HANDLE, val=struct.pack("<bb", 0x01, 0x00)
            # )
            # self.conn.setDelegate(SimpleDelegate(bleconn=self))

            #
            # Option 1, not sure how to create a new BleakGATTCharacteristic
            #
            # noti = BleakGATTCharacteristic()
            # serv.add_characteristic(noti)

            #
            # Option 2, does not work because the CONFIG_HANDLE is not a recognised
            #
            CONFIG_HANDLE = 0x0013
            ACTIVATION_VAL = struct.pack("<bb", 0x01, 0x00)
            # await client.write_gatt_char(CONFIG_HANDLE, ACTIVATION_VAL)
            await client.write_gatt_char(RX_CHAR_UUID, ACTIVATION_VAL)

            #
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
