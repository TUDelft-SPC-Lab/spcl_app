from __future__ import division, absolute_import, print_function
import time
import logging
import struct
import queue
import bleak
from typing import Optional, Final
# from badge_protocol import Request as mRequest
import badge_protocol as bp
import utils

DEFAULT_SCAN_WINDOW: Final[int] = 250
DEFAULT_SCAN_INTERVAL: Final[int] = 1000

DEFAULT_IMU_ACC_FSR: Final[int] = 4  # Valid ranges: 2, 4, 8, 16
DEFAULT_IMU_GYR_FSR: Final[int] = 1000  # Valid ranges: 250, 500, 1000, 2000
DEFAULT_IMU_DATARATE: Final[int] = 50

DEFAULT_MICROPHONE_MODE: Final[int] = 1  # Valid options: 0=Stereo, 1=Mono

CONNECTION_RETRY_TIMES = 10
DUPLICATE_TIME_INTERVAL = 1
logger = logging.getLogger(__name__)

# -- Helper methods used often in badge communication --

# We generally define timestamp_seconds to be in number of seconds since UTC epoch
# and timestamp_miliseconds to be the miliseconds portion of that UTC timestamp.

# Returns the current timestamp as two parts - seconds and milliseconds

# def get_timestamps():
#     return get_timestamps_from_time(time.time())


# Returns the given time as two parts - seconds and milliseconds
def get_timestamps_from_time(t=None):
    if t is None:
        t = time.time()
    timestamp_seconds = int(t)
    timestamp_fraction_of_second = t - timestamp_seconds
    timestamp_ms = int(1000 * timestamp_fraction_of_second)
    return timestamp_seconds, timestamp_ms


# Convert badge timestamp representation to python representation
def timestamps_to_time(timestamp_seconds, timestamp_miliseconds):
    return float(timestamp_seconds) + (float(timestamp_miliseconds) / 1000.0)


def bp_timestamp_from_time(t=None):
    ts = bp.Timestamp()
    ts.seconds, ts.ms = get_timestamps_from_time(t)
    return ts


def badge_disconnected(b):
    print(f"Warning: disconnected badge")


# Represents an OpenBadge currently connected via the BadgeConnection 'connection'.
#    The 'connection' should already be connected when it is used to initialize this class.
# Implements methods that allow for interaction with that badge.
class OpenBadge(object):
    def __init__(self, device: bleak.BLEDevice):
        self.device = device
        self.id = utils.get_device_id(device)
        self.client = bleak.BleakClient(self.device, disconnected_callback=badge_disconnected)
        self.rx_message = b''
        self.rx_queue = queue.Queue()
        self.rx_list = []
        # self.status_response_queue = queue.Queue()
        # self.start_microphone_response_queue = queue.Queue()
        # self.start_scan_response_queue = queue.Queue()
        # self.start_imu_response_queue = queue.Queue()
        # self.free_sdc_space_response_queue = queue.Queue()

    async def __aenter__(self):
        for _ in range(CONNECTION_RETRY_TIMES):
            try:
                await self.client.connect()
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
    def is_connected(self):
        return self.client.is_connected

    @staticmethod
    def add_serialized_header(request_message: bp.Request):
        serialized_request = request_message.encode()
        # Adding length header:
        serialized_request_len = struct.pack("<H", len(serialized_request))
        serialized_request: bytes = serialized_request_len + serialized_request
        return serialized_request

    @staticmethod
    async def send(client, message):
        await client.write_gatt_char(utils.TX_CHAR_UUID, message, response=True)

    @staticmethod
    async def receive(client):
        response_rx = b''
        for x in range(10):
            # if len(response_rx) > 0:
            #     break
            response_rx = await client.read_gatt_char(utils.RX_CHAR_UUID)
        return response_rx

    @staticmethod
    def message_is_duplicated(message_list: list, new_message) -> bool:
        if len(message_list) == 0:
            return False
        last_message = message_list[-1]
        time_duplicated = abs(last_message['time'] - new_message['time']) < DUPLICATE_TIME_INTERVAL
        message_duplicated = last_message['message'] == new_message['message']
        return time_duplicated and message_duplicated

    def received_callback(self, sender: bleak.BleakGATTCharacteristic, message: bytearray):
        if len(message) > 0:
            new_message = {'time': time.time(), 'message': message}
            if not self.message_is_duplicated(self.rx_list, new_message):
                print(f"RX changed {sender}: {message}" + str(time.time()))
                self.rx_message = message
                self.rx_list.append(new_message)
            # for b in data:
            #     self.rx_queue.put(b)

    async def request_response(self, message: bp.Request, require_response: Optional[bool] = True):
        serialized_request = self.add_serialized_header(message)
        # logger.debug("Sending: {}, Raw: {}".format(message, serialized_request.hex()))
        await self.send(self.client, serialized_request)
        response = await self.receive(self.client)
        return response if require_response else None

    @staticmethod
    def decode_response(response: bytearray or bytes):
        response_len = struct.unpack("<H", response[:2])[0]
        serialized_response = response[2:2 + response_len]
        return bp.Response.decode(serialized_response)

    def deal_response(self):
        serialized_response = self.rx_list.pop(0)['message']
        response_message = self.decode_response(serialized_response)
        return response_message

    # Sends a status request to this Badge.
    #   Optional fields new_id and new_group number will set the badge's id
    #     and group number. They must be sent together.
    # Returns a StatusResponse() representing badge's response.
    async def get_status(self, t=None, new_id: Optional[int] = None, new_group_number: Optional[int] = None):
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

    # Sends a request to the badge to start recording microphone data.
    # Returns a StartRecordResponse() representing the badges' response.
    async def start_microphone(self, t=None, mode=DEFAULT_MICROPHONE_MODE):
        request = bp.Request()
        request.type.which = bp.Request_start_microphone_request_tag
        request.type.start_microphone_request = bp.StartMicrophoneRequest()
        request.type.start_microphone_request.timestamp = bp_timestamp_from_time(t)
        request.type.start_microphone_request.mode = mode

        await self.request_response(request)
        return self.deal_response().type.start_microphone_response

    # Sends a request to the badge to stop recording.
    # Returns True if request was successfully sent.
    async def stop_microphone(self):
        request = bp.Request()
        request.type.which = bp.Request_stop_microphone_request_tag
        request.type.stop_microphone_request = bp.StopMicrophoneRequest()

        await self.request_response(request, require_response=False)
        return None

    # Sends a request to the badge to start performing scans and collecting scan data.
    #   window_miliseconds and interval_miliseconds controls radio duty cycle during scanning (0 for firmware default)
    #     radio is active for [window_miliseconds] every [interval_miliseconds]
    # Returns a StartScanningResponse() representing the badge's response.
    async def start_scan(self, t=None, window_ms=DEFAULT_SCAN_WINDOW, interval_ms=DEFAULT_SCAN_INTERVAL):
        request = bp.Request()
        request.type.which = bp.Request_start_scan_request_tag
        request.type.start_scan_request = bp.StartScanRequest()
        request.type.start_scan_request.timestamp = bp_timestamp_from_time(t)
        request.type.start_scan_request.window = window_ms
        request.type.start_scan_request.interval = interval_ms

        await self.request_response(request)
        return self.deal_response()

    # Sends a request to the badge to stop scanning.
    # Returns True if request was successfully sent.
    async def stop_scan(self):
        request = bp.Request()
        request.type.which = bp.Request_stop_scan_request_tag
        request.type.stop_scan_request = bp.StopScanRequest()

        await self.request_response(request)
        return self.deal_response()

    async def start_imu(self, t=None, acc_fsr=DEFAULT_IMU_ACC_FSR,
                        gyr_fsr=DEFAULT_IMU_GYR_FSR, datarate=DEFAULT_IMU_DATARATE):

        request = bp.Request()
        request.type.which = bp.Request_start_imu_request_tag
        request.type.start_imu_request = bp.StartImuRequest()
        request.type.start_imu_request.timestamp = bp_timestamp_from_time(t)
        request.type.start_imu_request.acc_fsr = acc_fsr
        request.type.start_imu_request.gyr_fsr = gyr_fsr
        request.type.start_imu_request.datarate = datarate

        await self.request_response(request)
        return self.deal_response()

    async def stop_imu(self):
        request = bp.Request()
        request.type.which = bp.Request_stop_imu_request_tag
        request.type.stop_imu_request = bp.StopImuRequest()

        await self.request_response(request)
        return self.deal_response()

    # Send a request to the badge to light an LED to identify its self.
    #   If duration_seconds == 0, badge will turn off LED if currently lit.
    # Returns True if request was successfully sent.
    async def identify(self, duration_seconds=10):
        request = bp.Request()
        request.type.which = bp.Request_identify_request_tag
        request.type.identify_request = bp.IdentifyRequest()
        request.type.identify_request.timeout = duration_seconds

        await self.request_response(request)
        self.deal_response()
        return True

    async def restart(self):
        request = bp.Request()
        request.type.which = bp.Request_restart_request_tag
        request.type.restart_request = bp.RestartRequest()

        await self.request_response(request)
        self.deal_response()
        return True

    async def get_free_sdc_space(self):
        request = bp.Request()
        request.type.which = bp.Request_free_sdc_space_request_tag
        request.type.free_sdc_space_request = bp.FreeSDCSpaceRequest()

        await self.request_response(request)
        return self.deal_response().type.free_sdc_space_response
