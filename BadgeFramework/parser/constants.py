from datetime import datetime as dt

from typing import Final


OUTPUT_DIRECTORY: Final[str] = "output"
OUTPUT_RAW_DIRECTORY: Final[str] = "output_raw"

ACCELERATION_POSTFIX: Final[str] = "_accel"
GYROSCOPE_POSTFIX: Final[str] = "_gyr"
MAGNETOMETER_POSTFIX: Final[str] = "_mag"
ROTATION_POSTFIX: Final[str] = "_rotation"

TRIM_SIZE: Final[int] = 140_000
"""
The amount of milliseconds to trim.
"""

CHUNK_SIZE: Final[int] = 24
"""
The chunk size of the binary frames produced by the midge. 
The chunksize of the most recent firmware (used in Nice) is 24 bytes as of 06-01-2022 
The chunksize of the version before that is 32 bytes.
"""


MAX_TIMESTAMP: Final[int] = 1767139200000
"""
A timestamp in milliseconds used to verify that the timestamp is plausible

"""
MAX_TIMESTAMP_HUMAN_READABLE: Final[dt] = dt.fromtimestamp(
    MAX_TIMESTAMP / 1000)
