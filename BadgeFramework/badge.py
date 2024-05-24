from __future__ import division, absolute_import, print_function

import sys
import functools
import time
import logging
import struct
from collections.abc import Callable

from bleak import BleakClient, BLEDevice, BleakGATTCharacteristic
from typing import Optional, Final
import badge_protocol as bp
import utils

DEFAULT_SCAN_WINDOW: Final[int] = 250
DEFAULT_SCAN_INTERVAL: Final[int] = 1000

DEFAULT_IMU_ACC_FSR: Final[int] = 4  # Valid ranges: 2, 4, 8, 16
DEFAULT_IMU_GYR_FSR: Final[int] = 1000  # Valid ranges: 250, 500, 1000, 2000
DEFAULT_IMU_DATARATE: Final[int] = 50

DEFAULT_MICROPHONE_MODE: Final[int] = 1  # Valid options: 0=Stereo, 1=Mono

CONNECTION_RETRY_TIMES = 3
DUPLICATE_TIME_INTERVAL = 1
logger = logging.getLogger(__name__)

# -- Helper methods used often in badge communication --

# We generally define timestamp_seconds to be in number of seconds since UTC epoch
# and timestamp_miliseconds to be the miliseconds portion of that UTC timestamp.


def get_timestamps_from_time(t=None) -> (int, int):
    """Returns the given time as two parts - seconds and milliseconds"""
    if t is None:
        t = time.time()
    timestamp_seconds = int(t)
    timestamp_fraction_of_second = t - timestamp_seconds
    timestamp_ms = int(1000 * timestamp_fraction_of_second)
    return timestamp_seconds, timestamp_ms


# Convert badge timestamp representation to python representation
# def timestamps_to_time(timestamp_seconds, timestamp_miliseconds):
#     return float(timestamp_seconds) + (float(timestamp_miliseconds) / 1000.0)


def bp_timestamp_from_time(t=None) -> bp.Timestamp:
    ts = bp.Timestamp()
    ts.seconds, ts.ms = get_timestamps_from_time(t)
    return ts


def badge_disconnected(b: BleakClient) -> None:
    """disconnection callback"""
    print(f"Warning: disconnected badge")


def request_handler(device_id, action_desc):
    def request_handler_decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                value = await func(*args, **kwargs)
                return value
            except Exception as err:
                error_desc = "Could not {} for participant {}, error: {}"
                raise Exception(error_desc.format(action_desc, str(device_id), str(err)))
        return wrapper
    return request_handler_decorator


def request_handler_marker(action_desc):
    def wrapper(func):
        func._handler = True  # Mark the function to be repeated
        func._action_desc = action_desc
        return func
    return wrapper


class OpenBadgeMeta:
    def __init__(self, device: BLEDevice or int, mac_address: str = None):
        # self.device = device
        if isinstance(device, BLEDevice):
            self.device_id = utils.get_device_id(device)
            self.address = device.address
        elif isinstance(device, int):
            self.device_id = device
            self.address = mac_address
        self._decorate_methods()

    def _decorate_methods(self):
        # Automatically decorate methods marked with @repeat_method
        for attr_name in dir(self):
            attr = getattr(self, attr_name, None)
            if callable(attr) and getattr(attr, '_handler', False):
                action_desc = getattr(attr, '_action_desc', '[unknown operation]')
                decorated = request_handler(self.device_id, action_desc)(attr)
                setattr(self, attr_name, decorated)


class OpenBadge(OpenBadgeMeta):
    """Represents an OpenBadge and implements methods that allow for interaction with that badge."""
    def __init__(self, device: BLEDevice or int, mac_address: str = None):
        super().__init__(device, mac_address)
        self.client = BleakClient(self.address, disconnected_callback=badge_disconnected)
        # self.rx_message = b''
        self.rx_list = []

    async def __aenter__(self):
        for _ in range(CONNECTION_RETRY_TIMES):
            try:
                await self.client.connect(timeout=10)
                await self.client.start_notify(utils.RX_CHAR_UUID, self.received_callback)
                return self
            except Exception as e:
                pass
        raise TimeoutError(f'Failed to connect to device after {CONNECTION_RETRY_TIMES} attempts.')

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()

    # Helper function to send a BadgeMessage `command_message` to a device, expecting a response
    # of class `response_type` that is a subclass of BadgeMessage, or None if no response is expected.

    @property
    def is_connected(self) -> bool:
        return self.client.is_connected

    @staticmethod
    def add_serialized_header(request_message: bp.Request) -> bytes or bytearray:
        """add serialized header to message"""
        serialized_request = request_message.encode()
        # Adding length header:
        serialized_request_len = struct.pack("<H", len(serialized_request))
        serialized_request: bytes = serialized_request_len + serialized_request
        return serialized_request

    @staticmethod
    async def send(client, message) -> None:
        """send message to client"""
        await client.write_gatt_char(utils.TX_CHAR_UUID, message, response=True)

    @staticmethod
    async def receive(client: BleakClient) -> bytes or bytearray:
        """receive message from client"""
        response_rx = b''
        for x in range(10):
            # if len(response_rx) > 0:
            #     break
            response_rx = await client.read_gatt_char(utils.RX_CHAR_UUID)
        return response_rx

    @staticmethod
    def message_is_duplicated(message_list: list, new_message: dict) -> bool:
        """check if message is duplicated with existing message list"""
        if len(message_list) == 0:
            return False
        last_message = message_list[-1]
        time_duplicated = abs(last_message['time'] - new_message['time']) < DUPLICATE_TIME_INTERVAL
        message_duplicated = last_message['message'] == new_message['message']
        return time_duplicated and message_duplicated

    def received_callback(self, sender: BleakGATTCharacteristic, message: bytearray):
        """callback function for receiving message. Note that this must be used in combination with the
        'receive' function to work properly."""
        if len(message) > 0:
            new_message = {'time': time.time(), 'message': message}
            if not self.message_is_duplicated(self.rx_list, new_message):
                print(f"RX changed {sender}: {message}" + str(time.time()))
                # self.rx_message = message
                self.rx_list.append(new_message)

    async def request_response(self, message: bp.Request, require_response: Optional[bool] = True):
        """request response from client"""
        serialized_request = self.add_serialized_header(message)
        # logger.debug("Sending: {}, Raw: {}".format(message, serialized_request.hex()))
        await self.send(self.client, serialized_request)
        response = await self.receive(self.client)
        return response if require_response else None

    @staticmethod
    def decode_response(response: bytearray or bytes):
        """decode response from client. First two bytes represent the length."""
        response_len = struct.unpack("<H", response[:2])[0]
        serialized_response = response[2:2 + response_len]
        return bp.Response.decode(serialized_response)

    def deal_response(self):
        """deal response from client. Currently, this only involves decoding."""
        serialized_response = self.rx_list.pop(0)['message']
        response_message = self.decode_response(serialized_response)
        return response_message

    @request_handler_marker(action_desc='get status')
    async def get_status(self, t=None, new_id: Optional[int] = None, new_group_number: Optional[int] = None)\
            -> bp.StatusResponse:
        """Sends a status request to this Badge. Optional fields new_id and new_group number will set
        the badge's id and group number. They must be sent together. Returns a StatusResponse()
        representing badge's response."""
        request = bp.Request()
        request.type.which = bp.Request_status_request_tag
        request.type.status_request = bp.StatusRequest()
        request.type.status_request.timestamp = bp_timestamp_from_time(t)
        if not ((new_id is None) or (new_group_number is None)):
            request.type.status_request.badge_assignement = bp.BadgeAssignement()
            request.type.status_request.badge_assignement.ID = new_id
            request.type.status_request.badge_assignement.group = new_group_number
            request.type.status_request.has_badge_assignement = True

        await self.request_response(request)
        return self.deal_response().type.status_response

    def set_id_at_start(self, badge_id, group_number):
        try:
            self.get_status(new_id=badge_id, new_group_number=group_number)
        except Exception as err:
            raise Exception(f"Could not set id {badge_id}, error:" + str(err))

    @request_handler_marker(action_desc='start microphone')
    async def start_microphone(self, t=None, mode=DEFAULT_MICROPHONE_MODE) -> bp.StartMicrophoneResponse:
        """Sends a request to the badge to start recording microphone data. Returns a StartRecordResponse()
        representing the badges' response."""
        request = bp.Request()
        request.type.which = bp.Request_start_microphone_request_tag
        request.type.start_microphone_request = bp.StartMicrophoneRequest()
        request.type.start_microphone_request.timestamp = bp_timestamp_from_time(t)
        request.type.start_microphone_request.mode = mode

        await self.request_response(request)
        return self.deal_response().type.start_microphone_response

    @request_handler_marker(action_desc='stop microphone')
    async def stop_microphone(self) -> None:
        """Sends a request to the badge to stop recording."""
        request = bp.Request()
        request.type.which = bp.Request_stop_microphone_request_tag
        request.type.stop_microphone_request = bp.StopMicrophoneRequest()

        await self.request_response(request, require_response=False)
        return None

    @request_handler_marker(action_desc='start scan')
    async def start_scan(self, t=None, window_ms=DEFAULT_SCAN_WINDOW, interval_ms=DEFAULT_SCAN_INTERVAL)\
            -> bp.StartScanResponse:
        """Sends a request to the badge to start performing scans and collecting scan data.
        window_miliseconds and interval_miliseconds controls radio duty cycle during scanning (0 for firmware default)
        radio is active for [window_miliseconds] every [interval_miliseconds]
        Returns a StartScanningResponse() representing the badge's response."""
        request = bp.Request()
        request.type.which = bp.Request_start_scan_request_tag
        request.type.start_scan_request = bp.StartScanRequest()
        request.type.start_scan_request.timestamp = bp_timestamp_from_time(t)
        request.type.start_scan_request.window = window_ms
        request.type.start_scan_request.interval = interval_ms

        await self.request_response(request)
        return self.deal_response().type.start_scan_response

    @request_handler_marker(action_desc='stop scan')
    async def stop_scan(self) -> None:
        """Sends a request to the badge to stop scanning."""
        request = bp.Request()
        request.type.which = bp.Request_stop_scan_request_tag
        request.type.stop_scan_request = bp.StopScanRequest()

        await self.request_response(request)
        return self.deal_response()

    @request_handler_marker(action_desc='start imu')
    async def start_imu(self, t=None, acc_fsr=DEFAULT_IMU_ACC_FSR, gyr_fsr=DEFAULT_IMU_GYR_FSR,
                        datarate=DEFAULT_IMU_DATARATE) -> bp.StartImuResponse:
        """Sends a request to the badge to start IMU. Returns the response object."""
        request = bp.Request()
        request.type.which = bp.Request_start_imu_request_tag
        request.type.start_imu_request = bp.StartImuRequest()
        request.type.start_imu_request.timestamp = bp_timestamp_from_time(t)
        request.type.start_imu_request.acc_fsr = acc_fsr
        request.type.start_imu_request.gyr_fsr = gyr_fsr
        request.type.start_imu_request.datarate = datarate

        await self.request_response(request)
        return self.deal_response().type.start_imu_response

    @request_handler_marker(action_desc='stop imu')
    async def stop_imu(self) -> None:
        """Sends a request to the badge to stop IMU."""
        request = bp.Request()
        request.type.which = bp.Request_stop_imu_request_tag
        request.type.stop_imu_request = bp.StopImuRequest()

        await self.request_response(request)
        return None

    @request_handler_marker(action_desc='identify')
    async def identify(self, duration_seconds=10) -> bool:
        """Send a request to the badge to light an LED to identify its self.
        If duration_seconds == 0, badge will turn off LED if currently lit.
        Returns True if request was successfully sent."""
        request = bp.Request()
        request.type.which = bp.Request_identify_request_tag
        request.type.identify_request = bp.IdentifyRequest()
        request.type.identify_request.timeout = duration_seconds

        await self.request_response(request)
        self.deal_response()
        return True

    @request_handler_marker(action_desc='restart')
    async def restart(self) -> bool:
        """Sends a request to the badge to restart the badge. Returns True if request was successfully sent."""
        request = bp.Request()
        request.type.which = bp.Request_restart_request_tag
        request.type.restart_request = bp.RestartRequest()

        await self.request_response(request)
        self.deal_response()
        return True

    @request_handler_marker(action_desc='get free sdc space')
    async def get_free_sdc_space(self) -> bp.FreeSDCSpaceResponse:
        """Sends a request to the badge to get a free sdc space. Returns the response object."""
        request = bp.Request()
        request.type.which = bp.Request_free_sdc_space_request_tag
        request.type.free_sdc_space_request = bp.FreeSDCSpaceRequest()

        await self.request_response(request)
        return self.deal_response().type.free_sdc_space_response

    async def start_recording_all_sensors(self):
        await self.get_status()
        await self.start_scan()
        await self.start_microphone()
        await self.start_imu()

    async def stop_recording_all_sensors(self):
        await self.start_scan()
        await self.stop_microphone()
        await self.stop_imu()

    @staticmethod
    def print_help():
        print(" Available commands:")
        print(" status ")
        print(" start_all_sensors")
        print(" stop_all_sensors")
        print(" start_microphone")
        print(" stop_microphone")
        print(" start_scan")
        print(" stop_scan")
        print(" start_imu")
        print(" stop_imu")
        print(" identify")
        print(" restart")
        print(" get_free_space")
        print(" help")
        print(" All commands use current system time as transmitted time.")
        sys.stdout.flush()
