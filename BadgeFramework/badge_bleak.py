from __future__ import division, absolute_import, print_function
import time
import logging
import sys
import struct
import queue
from typing import Optional, Final
from badge_protocol import Request as mRequest

DEFAULT_SCAN_WINDOW: Final[int] = 250
DEFAULT_SCAN_INTERVAL: Final[int] = 1000

DEFAULT_IMU_ACC_FSR: Final[int] = 4  # Valid ranges: 2, 4, 8, 16
DEFAULT_IMU_GYR_FSR: Final[int] = 1000  # Valid ranges: 250, 500, 1000, 2000
DEFAULT_IMU_DATARATE: Final[int] = 50

DEFAULT_MICROPHONE_MODE: Final[int] = 1  # Valid options: 0=Stereo, 1=Mono

from badge_protocol import *

logger = logging.getLogger(__name__)


def get_timestamps():
    return get_timestamps_from_time(time.time())


def get_timestamps_from_time(t):
    timestamp_seconds = int(t)
    timestamp_fraction_of_second = t - timestamp_seconds
    timestamp_ms = int(1000 * timestamp_fraction_of_second)
    return (timestamp_seconds, timestamp_ms)


def timestamps_to_time(timestamp_seconds, timestamp_miliseconds):
    return float(timestamp_seconds) + (float(timestamp_miliseconds) / 1000.0)


class OpenBadge(object):
    def __init__(self, connection):
        self.connection = connection
        self.status_response_queue = queue.Queue()
        self.start_microphone_response_queue = queue.Queue()
        self.start_scan_response_queue = queue.Queue()
        self.start_imu_response_queue = queue.Queue()
        self.free_sdc_space_response_queue = queue.Queue()

    def send_request(self, request_message: mRequest):
        print(type(request_message))
        serialized_request = request_message.encode()

        # Adding length header:
        serialized_request_len = struct.pack("<H", len(serialized_request))
        serialized_request: bytes = serialized_request_len + serialized_request

        logger.debug(
            "Sending: {}, Raw: {}".format(request_message, serialized_request.hex())
        )

        self.connection.send(serialized_request, response_len=0)

    def receive_response(self):
        response_len = struct.unpack("<H", self.connection.await_data(2))[0]
        logger.debug("Wait response len: " + str(response_len))
        serialized_response = self.connection.await_data(response_len)

        response_message = Response.decode(serialized_response)

        queue_options = {
            Response_status_response_tag: self.status_response_queue,
            Response_start_microphone_response_tag: self.start_microphone_response_queue,
            Response_start_scan_response_tag: self.start_scan_response_queue,
            Response_start_imu_response_tag: self.start_imu_response_queue,
            Response_free_sdc_space_response_tag: self.free_sdc_space_response_queue,
        }
        response_options = {
            Response_status_response_tag: response_message.type.status_response,
            Response_start_microphone_response_tag: response_message.type.start_microphone_response,
            Response_start_scan_response_tag: response_message.type.start_scan_response,
            Response_start_imu_response_tag: response_message.type.start_imu_response,
            Response_free_sdc_space_response_tag: response_message.type.free_sdc_space_response,
        }
        queue_options[response_message.type.which].put(
            response_options[response_message.type.which]
        )

    # Sends a status request to this Badge.
    #   Optional fields new_id and new_group number will set the badge's id
    #     and group number. They must be sent together.
    # Returns a StatusResponse() representing badge's response.
    def get_status(
        self,
        t=None,
        new_id: Optional[int] = None,
        new_group_number: Optional[int] = None,
    ):
        if t is None:
            (timestamp_seconds, timestamp_ms) = get_timestamps()
        else:
            (timestamp_seconds, timestamp_ms) = get_timestamps_from_time(t)

        request = Request()
        request.type.which = Request_status_request_tag
        request.type.status_request = StatusRequest()
        request.type.status_request.timestamp = Timestamp()
        request.type.status_request.timestamp.seconds = timestamp_seconds
        request.type.status_request.timestamp.ms = timestamp_ms
        if not ((new_id is None) or (new_group_number is None)):
            request.type.status_request.badge_assignement = BadgeAssignement()
            request.type.status_request.badge_assignement.ID = new_id
            request.type.status_request.badge_assignement.group = new_group_number
            request.type.status_request.has_badge_assignement = True

        self.send_request(request)

        # Clear the queue before receiving
        with self.status_response_queue.mutex:
            self.status_response_queue.queue.clear()

        while self.status_response_queue.empty():
            self.receive_response()

        return self.status_response_queue.get()