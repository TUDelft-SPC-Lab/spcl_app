import asyncio
import pandas as pd
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic
import uuid


def get_mac_address(df, badge_id: int) -> str:
    mac_address = df[df['Participant Id'] == badge_id]['Mac Address']
    mac_address = list(mac_address)[0]
    return mac_address


df_badge = pd.read_csv("mappings_allBackup.csv")

UART_SERVICE_UUID = uuid.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
TX_CHAR_UUID = uuid.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
RX_CHAR_UUID = uuid.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")

async def main():
    badge_scanner = BleakScanner()
    # Find all devices
    devices = await badge_scanner.discover(timeout=2.0)

    # Filter out the devices that are not the midge
    midges = [d for d in devices if d.name == 'HDBDG']

    for d in midges:
        print(f"Signal: {d.rssi}, Name: {d.name}, Address: {d.address}")

    for d in midges:
        # Connect to the midge
        async with BleakClient(d.address) as client:
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
            # CONFIG_HANDLE = 0x0013
            # ACTIVATION_VAL = struct.pack("<bb", 0x01, 0x00)
            # await client.write_gatt_char(CONFIG_HANDLE, ACTIVATION_VAL)

            #
            # Option 3, it doesn't crash but not sure if it actually works
            # 
            def callback(sender: BleakGATTCharacteristic, data: bytearray):
                print(f"RX changed {sender}: {data}")

            await client.start_notify(rx, callback)

            print("Done")



        break

if __name__ == "__main__":
    asyncio.run(main())