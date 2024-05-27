from badge import OpenBadge
import sys
import tty
import termios
import logging
import time
import utils
from bleak import BleakScanner, BleakClient, BLEDevice


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


logger = get_logger("hub_utilities")


def choose_function(badge: OpenBadge, user_input):
    chooser = {
        "help": badge.print_help,
        "status": badge.get_status,
        "start_all_sensors": badge.start_recording_all_sensors,
        "stop_all_sensors": badge.stop_recording_all_sensors,
        "start_microphone": badge.start_microphone,
        "stop_microphone": badge.stop_microphone,
        "start_scan": badge.start_scan,
        "stop_scan": badge.stop_scan,
        "start_imu": badge.start_imu,
        "stop_imu": badge.stop_imu,
        "identify": badge.identify,
        "restart": badge.restart,
        "get_free_space": badge.get_free_sdc_space,
    }
    func = chooser.get(user_input, lambda: "Invalid command!")
    logger.info("Following command is entered: " + user_input + ".")
    try:
        out = func()
        return out
    except Exception as error:
        logger.info("Error: " + str(error))
        return


async def start_recording_all_devices(df):
    for _, row in df.iterrows():
        device_id: int = row["Participant Id"]
        device_addr: str = row["Mac Address"]
        use_current_device: bool = row["Use"]
        if not use_current_device:
            continue
        try:
            async with OpenBadge(device_id, device_addr) as open_badge:
                # await open_badge.set_id_at_start()
                await open_badge.start_recording_all_sensors()
        except Exception as error:
            logger.info(f"Sensors for midge {str(device_id)} are not started with the following error: {str(error)}")
            continue
    print('completed')


async def stop_recording_all_devices(df):
    for _, row in df.iterrows():
        device_id: int = row["Participant Id"]
        device_addr: str = row["Mac Address"]
        use_current_device: bool = row["Use"]
        if not use_current_device:
            continue
        try:
            async with OpenBadge(device_id, device_addr) as open_badge:
                await open_badge.stop_recording_all_sensors()
        except Exception as error:
            logger.info(f"Sensors for midge {str(device_id)} are not stopped with the following error: {str(error)}")
            continue
    print('completed')


# async def synchronise_one_device(df):


async def synchronise_and_check_all_devices(df):
    for _, row in df.iterrows():
        device_id: int = row["Participant Id"]
        device_addr: str = row["Mac Address"]
        use_current_device: bool = row["Use"]
        if not use_current_device:
            continue
        try:
            async with OpenBadge(device_id, device_addr) as open_badge:
                out = await open_badge.get_status()
                logger.info("Status received for the following midge:" + str(device_id) + ".")
                # TODO This is not actually the timestamp before, find how to get it.
                logger.debug("Device timestamp before sync - seconds:"
                             + str(out.timestamp.seconds) + ", ms:"
                             + str(out.timestamp.ms) + ".")
                error_message = "{} is not recording for participant " + str(device_id) + "."
                if out.imu_status == 0:
                    logger.info(error_message.format("IMU"))
                if out.microphone_status == 0:
                    logger.info(error_message.format("Mic"))
                if out.scan_status == 0:
                    logger.info(error_message.format("Scan"))
                if out.clock_status == 0:
                    logger.info("Cant sync for participant " + str(device_id) + ".")
        except Exception as error:
            logger.info(f"Status check for midge {str(device_id)} returned the following error: {str(error)}")
            # sys.stdout.flush()
            continue
    print('completed')


class timeout_input(object):
    def __init__(self, poll_period=0.05):
        self.poll_period = poll_period

    def _getch_nix(self):
        from select import select

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            [i, _, _] = select([sys.stdin.fileno()], [], [], self.poll_period)
            if i:
                ch = sys.stdin.read(1)
            else:
                ch = ""
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def input(
        self,
        prompt=None,
        timeout=None,
        extend_timeout_with_input=True,
        require_enter_to_confirm=True,
    ):
        prompt = prompt or ""
        sys.stdout.write(prompt)
        sys.stdout.flush()
        input_chars = []
        start_time = time.time()
        received_enter = False
        while (time.time() - start_time) < timeout:
            c = self._getch_nix()
            if c in ("\n", "\r"):
                received_enter = True
                break
            elif c:
                input_chars.append(c)
                sys.stdout.write(c)
                sys.stdout.flush()
                if extend_timeout_with_input:
                    start_time = time.time()
        sys.stdout.write("\n")
        sys.stdout.flush()
        captured_string = "".join(input_chars)
        if require_enter_to_confirm:
            return_string = captured_string if received_enter else ""
        else:
            return_string = captured_string
        return return_string
