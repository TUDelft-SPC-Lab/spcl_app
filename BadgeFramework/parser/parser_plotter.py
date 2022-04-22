import struct
from datetime import datetime as dt
import numpy as np
import pandas as pd
import os
import sys
from quaternion_visualizer import QuaternionVisualizer
from parser_utils import (
    getFileNameOfPath,
    create_path_if_not_exists,
    get_script_directory,
    fullTimeName
)
from constants import (
    OUTPUT_DIRECTORY,
    OUTPUT_RAW_DIRECTORY,
    ACCELERATION_POSTFIX,
    GYROSCOPE_POSTFIX,
    MAGNETOMETER_POSTFIX,
    ROTATION_POSTFIX,
    MAX_TIMESTAMP,
    CHUNK_SIZE,
    MAX_TIMESTAMP_HUMAN_READABLE,
)


class ParserPlotter(object):
    def __init__(
        self, input_directory: str, full_file_name: str, force: bool, create_path: bool, experimentName: str
    ):
        self.force = force
        self.create_path = create_path
        self.file_base_path = input_directory
        self.experimentName = experimentName
        self.raw_output_directory = os.path.join(
            get_script_directory(), OUTPUT_RAW_DIRECTORY,full_file_name
        )
        full_path = os.path.join(input_directory, str(full_file_name))
        self.path_accel = full_path + ACCELERATION_POSTFIX
        self.path_gyro = full_path + GYROSCOPE_POSTFIX
        self.path_mag = full_path + MAGNETOMETER_POSTFIX
        self.path_rotation = full_path + ROTATION_POSTFIX
        self.check_if_file_exists(self.path_accel)
        self.check_if_file_exists(self.path_gyro)
        self.check_if_file_exists(self.path_mag)
        self.check_if_file_exists(self.path_rotation)
        self.accel_df: pd.DataFrame
        self.gyro_df: pd.DataFrame
        self.mag_df: pd.DataFrame
        self.rot_df: pd.DataFrame
        # REMOVE THIS
        self.file_base_name = getFileNameOfPath(self.file_base_path)
        self.output_directory_path = os.path.join(
            get_script_directory(), OUTPUT_DIRECTORY, f"{self.file_base_name}_{experimentName}"
        )

    def check_if_file_exists(self, path: str):
        if not os.path.exists(path):
            sys.exit(f"Stopping: the following file does not exist: {path}")

    def trim(self, dataframe: pd.DataFrame, timestamp_start: int) -> pd.DataFrame:
        # add an hour for the difference in timezone
        datetime_start = pd.to_datetime(
            timestamp_start, unit='s') + pd.DateOffset(hours=1)
        return dataframe[dataframe.time > datetime_start]

    def parse_generic(self, sensorname: str):
        data = []
        timestamps = []
        correct_timestamps = 0
        wrong_timestamps = 0
        with open(sensorname, "rb") as f:
            byte = f.read()
            i = 0
            while True:
                ts_bytes = byte[0 + i: 8 + i]
                data_bytes = byte[8 + i: 20 + i]
                if (len(data_bytes)) == 12 and (len(ts_bytes) == 8):
                    ts = struct.unpack("<Q", ts_bytes)
                    x, y, z = struct.unpack("<fff", data_bytes)
                    if float(ts[0]) > MAX_TIMESTAMP:
                        wrong_timestamps += 1
                    else:
                        correct_timestamps += 1
                        data.append([x, y, z])
                        timestamps.append(ts[0])
                    sys.stdout.flush()
                    i = i + CHUNK_SIZE
                else:
                    break
        data_xyz = np.asarray(data)
        timestamps = np.asarray(timestamps)
        timestamps_dt = [dt.fromtimestamp(float(x) / 1000) for x in timestamps]
        df = pd.DataFrame(timestamps_dt, columns=["time"])
        if wrong_timestamps != 0:
            print(
                f"""
                In File {getFileNameOfPath(sensorname)}:\nThere where {wrong_timestamps} timestamp  out of {correct_timestamps} timestamps ({round(wrong_timestamps/(wrong_timestamps+correct_timestamps)*100,3)}%) in the file exeeds the max timestamp: {MAX_TIMESTAMP_HUMAN_READABLE}. 
                If the data is recorded after the max timestamp, increase it, otherwise check the data format."""
            )
        df["X"] = data_xyz[:, 0]
        df["Y"] = data_xyz[:, 1]
        df["Z"] = data_xyz[:, 2]
        return df

    def parse_accel(self):
        self.accel_df = self.parse_generic(self.path_accel)

    def parse_gyro(self):
        self.gyro_df = self.parse_generic(self.path_gyro)

    def parse_mag(self):
        self.mag_df = self.parse_generic(self.path_mag)

    def parse_rot(self):
        rotation = []
        timestamps = []
        correct_timestamps = 0
        wrong_timestamps = 0
        with open(self.path_rotation, "rb") as f:
            byte = f.read()
            i = 0
            while True:
                ts_bytes = byte[0 + i: 8 + i]
                rot_bytes = byte[8 + i: 24 + i]
                if (len(rot_bytes)) == 16 and (len(ts_bytes) == 8):
                    ts = struct.unpack("<Q", ts_bytes)
                    q1, q2, q3, q4 = struct.unpack("<ffff", rot_bytes)
                    if float(ts[0]) > MAX_TIMESTAMP:
                        wrong_timestamps += 1
                    else:
                        correct_timestamps += 1

                        rotation.append([q1, q2, q3, q4])
                        timestamps.append(ts[0])
                    i = i + CHUNK_SIZE
                else:
                    break
        rotation_xyz = np.asarray(rotation)
        timestamps = np.asarray(timestamps)
        timestamps_dt = [dt.fromtimestamp(float(x) / 1000) for x in timestamps]
        if wrong_timestamps != 0:
            print(
                f"""
                In rotation:\n There where {wrong_timestamps} timestamp  out of {correct_timestamps} timestamps ({round(wrong_timestamps/(correct_timestamps+wrong_timestamps)*100,3)}%) in the file exeeds the max timestamp: {MAX_TIMESTAMP_HUMAN_READABLE}. 
                If the data is recorded after the max timestamp, increase it, otherwise check the data format."""
            )
        df = pd.DataFrame(timestamps_dt, columns=["time"])
        df["a"] = rotation_xyz[:, 0]
        df["b"] = rotation_xyz[:, 1]
        df["c"] = rotation_xyz[:, 2]
        df["d"] = rotation_xyz[:, 2]
        self.rot_df = df

    def plot_and_save(self, acc: bool, gyr: bool, mag: bool, rot: bool) -> None:
        if acc:
            acc_file_path = os.path.join(
                self.output_directory_path,
                f"{self.file_base_name}_{ACCELERATION_POSTFIX}.png",
            )
            ax = self.accel_df.plot(
                x="time", title=f"{self.experimentName}: Accelerometer")
            fig = ax.get_figure()
            fig.savefig(acc_file_path)
        if gyr:
            gyr_file_path = os.path.join(
                self.output_directory_path,
                f"{self.file_base_name}_{GYROSCOPE_POSTFIX}.png",
            )
            ax = self.gyro_df.plot(
                x="time", title=f"{self.experimentName}: Gyroscope")
            fig = ax.get_figure()
            fig.savefig(gyr_file_path)
        if mag:
            mag_file_path = os.path.join(
                self.output_directory_path,
                f"{self.file_base_name}_{MAGNETOMETER_POSTFIX}.png",
            )
            ax = self.mag_df.plot(
                x="time", title=f"{self.experimentName}: Magnetometer")
            fig = ax.get_figure()
            fig.savefig(mag_file_path)
        if rot:
            rot_file_path = os.path.join(
                self.output_directory_path,
                f"{self.file_base_name}_{ROTATION_POSTFIX}",
            )
            qv = QuaternionVisualizer(
                dataframe=self.rot_df, outputPathNoExtension=rot_file_path, experimentName=self.experimentName)
            qv.plot()
            qv.plot2()

    def save_dataframes(self, acc: bool, gyr: bool, mag: bool, rot: bool) -> None:
        if self.create_path:
            create_path_if_not_exists(
                self.output_directory_path, force=self.force)
        print(f"saving parsed data to: {self.output_directory_path}")

        if acc:
            acc_file_path = os.path.join(
                self.output_directory_path,
                f"{self.file_base_name}{ACCELERATION_POSTFIX}",
            )
            self.accel_df.to_pickle(acc_file_path + ".pkl")
            self.accel_df.to_csv(acc_file_path + ".csv")
        if gyr:
            gyr_file_path = os.path.join(
                self.output_directory_path, f"{self.file_base_name}{GYROSCOPE_POSTFIX}"
            )
            self.gyro_df.to_pickle(gyr_file_path + ".pkl")
            self.gyro_df.to_csv(gyr_file_path + ".csv")
        if mag:
            mag_file_path = os.path.join(
                self.output_directory_path,
                f"{self.file_base_name}{MAGNETOMETER_POSTFIX}",
            )
            self.mag_df.to_pickle(mag_file_path + ".pkl")
            self.mag_df.to_csv(mag_file_path + ".csv")
        if rot:
            rot_file_path = os.path.join(
                self.output_directory_path, f"{self.file_base_name}{ROTATION_POSTFIX}"
            )
            self.rot_df.to_pickle(rot_file_path + ".pkl")
            self.rot_df.to_csv(rot_file_path + ".csv")
