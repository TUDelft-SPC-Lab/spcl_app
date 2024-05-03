import uuid
import logging
import pandas
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from typing import Optional, Final

UART_SERVICE_UUID = uuid.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
TX_CHAR_UUID = uuid.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
RX_CHAR_UUID = uuid.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
df_badge = pandas.read_csv("mappings_allBackup.csv")


def get_logger(name):
    log_format_file = '%(asctime)s  %(levelname)5s  %(message)s'
    log_format_console = '%(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format=log_format_file,
                        filename="data_collection.log",
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_format_console))
    logging.getLogger(name).addHandler(console)
    return logging.getLogger(name)


def get_mac_address(df, badge_id: int) -> str:
    mac_address = df[df['Participant Id'] == badge_id]['Mac Address']
    mac_address = list(mac_address)[0]
    return mac_address


def is_spcl_midge(device: BLEDevice) -> bool:
    return device.name == 'HDBDG'


def get_device_id(device: BLEDevice, addr_df: Optional[pandas.DataFrame] = df_badge) -> int:
    address = device.address.lower()
    try:
        badge_id = addr_df[addr_df['Mac Address'] == address]['Participant Id']
        badge_id = badge_id.values[0]
    except IndexError:
        badge_id = -1000
    return badge_id
