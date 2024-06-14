import asyncio
import time
import logging
import utils
from bleak import BleakScanner
from badge import OpenBadge


async def synchronize_device(open_badge: OpenBadge, logger: logging.Logger) -> None:
    # TODO: pass in the universal time code here?
    status = await open_badge.get_status()
    logger.info(f"Status received for the following midge: {open_badge.id}.")
    # TODO This is not actually the timestamp before, find how to get it.
    logger.debug(f"Device timestamp before sync - seconds: {status.timestamp.seconds}, ms:{status.timestamp.ms}.")
    if status.imu_status == 0:
        logger.info(f"IMU is not recording for participant {open_badge.id}.")
    if status.microphone_status == 0:
        logger.info(f"Mic is not recording for participant {open_badge.id}.")
    if status.scan_status == 0:
        logger.info(f"Scan is not recording for participant {open_badge.id}.")
    if status.clock_status == 0:
        logger.info(f"Can't sync for participant {open_badge.id}.")


async def main():
    logger = utils.get_logger('bleak_logger')
    # Find all devices
    # using both BLEdevice and advertisement data here since it has more information. Also mutes the warning.
    devices = await BleakScanner.discover(timeout=10.0, return_adv=True)

    # Filter out the devices that are not the midge
    devices = [d for d in devices.values() if utils.is_spcl_midge(d[0])]

    # Print Id to see if it matches with any devices in the csv file.
    for ble_device, adv_data in devices:
        device_id = utils.get_device_id(ble_device)
        print(f"RSSI: {adv_data.rssi}, Id: {device_id}, Address: {ble_device.address}")

    for ble_device, adv_data in devices:
        # open_badge = OpenBadge(ble_device)
        # space = await open_badge.get_free_sdc_space()
        async with OpenBadge(ble_device) as open_badge:
            # space = await open_badge.get_free_sdc_space()
            out = await open_badge.get_status(t=40)
            start = await open_badge.start_imu()
        time.sleep(15)
        async with OpenBadge(ble_device) as open_badge:
            stop = await open_badge.stop_imu()
            # await synchronize_device(open_badge, logger)
        c = 9
    print('completed')
    # Connect to the midge


if __name__ == "__main__":
    asyncio.run(main())
