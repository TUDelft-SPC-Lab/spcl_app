#! /usr/bin/python3
import os
from time import time
from constants import MAX_TIMESTAMP_HUMAN_READABLE
import sys
from constants import OUTPUT_DIRECTORY, OUTPUT_RAW_DIRECTORY
from parser_plotter import ParserPlotter
from file_copier import FileCopier
from parser_utils import (
    fullTimeName,
    getshortpath,
)
from constants import (
    OUTPUT_RAW_DIRECTORY,
    ACCELERATION_POSTFIX,
    GYROSCOPE_POSTFIX,
    MAGNETOMETER_POSTFIX,
    ROTATION_POSTFIX,
)


print(f"Max timestamp for data is {MAX_TIMESTAMP_HUMAN_READABLE} local time")


def processDirectory(directory: str) -> list[int]:
    if not os.path.isdir(directory):
        sys.exit(f"Stopping: The given path is not a directory")
    shortpath: str = getshortpath(directory)

    print(f"using files from directory: {shortpath}")
    filenames_in_directory = [
        f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))
    ]

    non_empty_files_in_directory: list[str] = []
    for file in filenames_in_directory:
        if os.path.getsize(os.path.join(directory, file)) <= 0:
            print(f"File {file: <22} is empty, not analysing this file")
            continue
        non_empty_files_in_directory.append(file)

    if len(non_empty_files_in_directory) == 0:
        sys.exit(
            f"Stopping: no non empty files where found in directory: {shortpath}")

    unique_timestamps_of_files: list[int] = []
    for file in non_empty_files_in_directory:
        possible_timestamp_part: str = file.split("_")[0]
        try:
            timestamp = int(possible_timestamp_part)
            if not timestamp in unique_timestamps_of_files:
                print(
                    f"found file with the following timestamp: {timestamp} (these files will be used if enabled: {timestamp}{ACCELERATION_POSTFIX}, {timestamp}{GYROSCOPE_POSTFIX}, {timestamp}{MAGNETOMETER_POSTFIX} and {timestamp}{ROTATION_POSTFIX})"
                )
                unique_timestamps_of_files.append(timestamp)
        except:
            continue
    return unique_timestamps_of_files


def main(
    path_directory: str,
    experimentName: str,
    acc: bool,
    mag: bool,
    gyr: bool,
    rot: bool,
    plot: bool,
    copy: bool,
    force: bool,
    trim: bool,
):
    unique_timestamps_of_files = processDirectory(path_directory)
    create_path = True
    for timestamp in unique_timestamps_of_files:
        parser: ParserPlotter
        if copy:
            sdfiles = FileCopier(
                input_directory=path_directory,
                timestamp=timestamp,
                force=force,
                experimentName=experimentName,
                create_path=create_path,
            )
            sdfiles.moveFiles()
            parser = sdfiles.parserFromCopiedFiles()
        else:
            parser = ParserPlotter(
                input_directory=path_directory,
                full_file_name=fullTimeName(timestamp),
                experimentName=experimentName,
                force=force,
                create_path=create_path,
            )
        if acc:
            parser.parse_accel()
            if trim:
                parser.accel_df = parser.trim(
                    parser.accel_df, timestamp_start=timestamp)
        if mag:
            parser.parse_mag()
            if trim:
                parser.mag_df = parser.trim(
                    parser.mag_df, timestamp_start=timestamp)
        if gyr:
            parser.parse_gyro()
            if trim:
                parser.gyro_df = parser.trim(
                    parser.gyro_df, timestamp_start=timestamp)
        if rot:
            parser.parse_rot()
            if trim:
                parser.rot_df = parser.trim(
                    parser.rot_df, timestamp_start=timestamp)

        parser.save_dataframes(acc, mag, gyr, rot)
        if plot:
            parser.plot_and_save(acc=acc, mag=mag, gyr=gyr, rot=rot)
        # after first run, the directories should not be deleted and recreated
        create_path = False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Parser and copier for the IMU data obtained from Midges\
    (Acceleration, Gyroscope, Magnetometer, Rotation)"
    )
    parser.add_argument(
        "directory", help="Enter the path to the directory to read from"
    )
    parser.add_argument(
        "experimentName", nargs="?", default="", type=str, help="Enter the name of the experiment (Will be used in the plots, and appended to the directory)"
    )
    parser.add_argument(
        "--no-acc",
        action="store_false",
        help="add this flag to not parse accelerometer data ",
    )
    parser.add_argument(
        "--no-mag",
        action="store_false",
        help="add this flag to not parse magnetometer data ",
    )
    parser.add_argument(
        "--no-gyr",
        action="store_false",
        help="add this flag to not parse gyroscope data  ",
    )
    parser.add_argument(
        "--no-rot",
        action="store_false",
        help="add this flag to not parse rotation data from the DMP ",
    )
    parser.add_argument(
        "--no-plot",
        action="store_false",
        help="add this flag to not plot the data from the accelerometer, gyroscope, magnetometer and DMP ",
    )
    parser.add_argument(
        "--no-copy",
        action="store_false",
        help=f"add this flag to not copy the data from the source to the {OUTPUT_RAW_DIRECTORY}, but to read it directly ",
    )
    parser.add_argument(
        "-f",
        action="store_true",
        help=f"add this flag to override the subdirectories in '{OUTPUT_DIRECTORY}' and '{OUTPUT_RAW_DIRECTORY}' ",
    )
    parser.add_argument(
        "--no-trim",
        action="store_false",
        help=f"Add this flag to trim all the data from before the start signal was given from the hub",
    )
    args = parser.parse_args()
    print(args.experimentName)
    main(
        path_directory=args.directory.removesuffix("/"),
        experimentName=args.experimentName,
        acc=args.no_acc,
        mag=args.no_mag,
        gyr=args.no_gyr,
        rot=args.no_rot,
        copy=args.no_copy,
        plot=args.no_plot,
        force=args.f,
        trim=args.no_trim
    )
