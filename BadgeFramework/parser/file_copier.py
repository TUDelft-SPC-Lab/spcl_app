import os
import shutil
from parser_utils import create_path_if_not_exists, fullTimeName, get_script_directory
from constants import (
    OUTPUT_RAW_DIRECTORY,
    ACCELERATION_POSTFIX,
    GYROSCOPE_POSTFIX,
    MAGNETOMETER_POSTFIX,
    ROTATION_POSTFIX,
)
from parser_plotter import ParserPlotter


class FileCopier(object):
    def __init__(
        self,
        input_directory: str,
        timestamp: int,
        force: bool,
        experimentName: str,
        create_path: bool = True
    ):
        self.force = force
        self.full_file_name = f"{fullTimeName(timestamp)}_{experimentName}"
        self.experimentName = experimentName
        self.create_path = create_path
        self.raw_output_directory = os.path.join(
            get_script_directory(), OUTPUT_RAW_DIRECTORY, self.full_file_name
        )
        full_path = os.path.join(input_directory, str(timestamp))
        self.path_accel_sd = full_path + ACCELERATION_POSTFIX
        self.path_gyro_sd = full_path + GYROSCOPE_POSTFIX
        self.path_mag_sd = full_path + MAGNETOMETER_POSTFIX
        self.path_rotation_sd = full_path + ROTATION_POSTFIX

    def outputfile(self, postfix: str):
        return os.path.join(
            self.raw_output_directory, f"{self.full_file_name}{postfix}"
        )

    def moveFiles(self):
        print(f"moving raw files to {self.raw_output_directory}")
        if self.create_path:
            create_path_if_not_exists(
                self.raw_output_directory, force=self.force)

        shutil.copy2(self.path_accel_sd, self.outputfile(ACCELERATION_POSTFIX))
        shutil.copy2(self.path_gyro_sd, self.outputfile(GYROSCOPE_POSTFIX))
        shutil.copy2(self.path_mag_sd, self.outputfile(MAGNETOMETER_POSTFIX))
        shutil.copy2(self.path_rotation_sd, self.outputfile(ROTATION_POSTFIX))

    def parserFromCopiedFiles(self):
        return ParserPlotter(
            input_directory=self.raw_output_directory,
            full_file_name=self.full_file_name,
            force=self.force,
            create_path=self.create_path,
            experimentName=self.experimentName
        )
