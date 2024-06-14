import pandas as pd
import sys
import os
from hub_utilities import (
    start_recording_all_devices,
    stop_recording_all_devices,
    timeout_input,
    choose_function,
    synchronise_and_check_all_devices,
    get_logger
)
import asyncio


def start_recording_cmd(logger):
    sys.stdout.write("in start\n")


def stop_recording_cmd(logger):
    logger.info("Stopping the recording of all devices.")
    sys.stdout.flush()
    # TODO: uncomment the stop recording function
    # stop_recording_all_devices(df)
    logger.info("Devices are stopped.")
    sys.stdout.flush()


def interactive_cmd(logger, df):
    logger.info(
        "Welcome to the interactive shell. Please type the id of the"
        + " midge you want to connect."
    )
    logger.info(
        "Type exit if you would like to stop recording for all devices."
    )
    sys.stdout.write("> ")
    sys.stdout.flush()
    command = sys.stdin.readline()[:-1]
    # try:
    #     current_mac_addr = (
    #         df.loc[df["Participant Id"] == int(command)]["Mac Address"]
    #     ).values[0]
    # except Exception:
    #     logger.info('Mac address for the midge ' + str(command)
    #                 + ' is not found.')
    #     continue
    try:
        # TODO: uncomment the connection function
        # cur_connection = Connection(int(command), current_mac_addr)
        logger.info('placeholder for connection')
    except Exception as error:
        logger.info("While connecting to midge " + str(command)
                    + ", following error occurred:" + str(error))
        sys.stdout.flush()
        return True
    logger.info("Connected to the midge " + str(command) + "."
                + " For available commands, please type help.")
    sys.stdout.flush()
    while True:
        sys.stdout.write("Now connected to the midge\n > ")
        command = sys.stdin.readline()[:-1]
        command_args = command.split(" ")
        if command == "exit":
            # TODO: uncomment the disconnect function
            # cur_connection.disconnect()
            logger.info("Disconnected from the midge.")
            break
        try:
            # TODO: uncomment the choose function
            # out = choose_function(cur_connection, command_args[0])
            # if out is not None:
            #     logger.info("Midge returned following"
            #                 + " status: " + str(out))
            sys.stdout.flush()
        except Exception as error:
            logger.info(str(error))
            sys.stdout.flush()
            # TODO: uncomment the print help function
            # cur_connection.print_help()
            continue


def synchronization_cmd(logger):
    logger.info("Synchronisation is starting. Please wait till it ends")
    # TODO: uncomment the synchronization function
    # synchronise_and_check_all_devices(df)
    logger.info("Synchronisation is finished.")
    sys.stdout.flush()


def command_line(logger):
    df = pd.read_csv("mappings2.csv")
    flag = True
    while True:
        logger.info("Type start to start data collection or stop to finish data "
                    + "collection.")
        sys.stdout.write("> ")
        sys.stdout.flush()
        command = sys.stdin.readline()[:-1]
        if command == "start":
            start_recording_cmd(logger)
            while flag:
                ti = timeout_input(poll_period=0.05)
                s = ti.input(
                    prompt="Type int if you would like to enter interactive shell.\n"
                           + ">",
                    timeout=10.0,
                    extend_timeout_with_input=False,
                    require_enter_to_confirm=True,
                )
                if s == "int":
                    flag = interactive_cmd(logger, df)
                elif s == "sync":
                    synchronization_cmd(logger)
        elif command == "stop":
            stop_recording_cmd(logger)
            break
    logger.info("Interactive session is finished.")


def main():
    df = pd.read_csv("mappings2.csv")
    logger = get_logger("hub_main")
    while True:
        logger.info("Type start to start data collection or stop to finish data "
                    + "collection.")
        sys.stdout.write("> ")
        sys.stdout.flush()
        command = sys.stdin.readline()[:-1]
        if command == "start":
            logger.info("Connecting to the midges for starting the recordings.")
            # TODO: uncomment the recording function
            # start_recording_all_devices(df)
            logger.info("Loop for starting the devices is finished.")
            while True:
                ti = timeout_input(poll_period=0.05)
                s = ti.input(
                    prompt="Type int if you would like to enter interactive shell.\n"
                           + ">",
                    timeout=10.0,
                    extend_timeout_with_input=False,
                    require_enter_to_confirm=True,
                )
                if s == "int":
                    logger.info(
                        "Welcome to the interactive shell. Please type the id of the"
                        + " midge you want to connect."
                    )
                    logger.info(
                        "Type exit if you would like to stop recording for all devices."
                    )
                    sys.stdout.write("> ")
                    sys.stdout.flush()
                    command = sys.stdin.readline()[:-1]
                    if command == "exit":
                        logger.info("Stopping the recording of all devices.")
                        sys.stdout.flush()
                        # TODO: uncomment the stop recording function
                        # stop_recording_all_devices(df)
                        logger.info("Devices are stopped.")
                        sys.stdout.flush()
                        break
                    command_args = command.split(" ")
                    try:
                        current_mac_addr = (
                            df.loc[df["Participant Id"] == int(command)]["Mac Address"]
                        ).values[0]
                    except Exception:
                        logger.info('Mac address for the midge ' + str(command)
                                    + ' is not found.')
                        continue
                    try:
                        # TODO: uncomment the connection function
                        # cur_connection = Connection(int(command), current_mac_addr)
                        logger.info('placeholder for connection')
                    except Exception as error:
                        logger.info("While connecting to midge " + str(command)
                                    + ", following error occurred:" + str(error))
                        sys.stdout.flush()
                        continue
                    logger.info("Connected to the midge " + str(command) + "."
                                + " For available commands, please type help.")
                    sys.stdout.flush()
                    while True:
                        sys.stdout.write("> ")
                        command = sys.stdin.readline()[:-1]
                        command_args = command.split(" ")
                        if command == "exit":
                            # TODO: uncomment the disconnect function
                            # cur_connection.disconnect()
                            logger.info("Disconnected from the midge.")
                            break
                        try:
                            # TODO: uncomment the choose function
                            # out = choose_function(cur_connection, command_args[0])
                            # if out is not None:
                            #     logger.info("Midge returned following"
                            #                 + " status: " + str(out))
                            sys.stdout.flush()
                        except Exception as error:
                            logger.info(str(error))
                            sys.stdout.flush()
                            # TODO: uncomment the print help function
                            # cur_connection.print_help()
                            continue
                else:
                    logger.info("Synchronisation is starting. Please wait till it ends")
                    # TODO: uncomment the synchronization function
                    # synchronise_and_check_all_devices(df)
                    logger.info("Synchronisation is finished.")
                    sys.stdout.flush()
        elif command == "stop":
            logger.info("Stopping data collection.")
            sys.stdout.flush()
            quit(0)
        else:
            logger.info(
                "Command not found, please type start or stop to start or stop data "
                + "collection."
            )
            sys.stdout.flush()


async def main_v2():
    # print(os.getcwd())
    df = pd.read_csv('mappings2.csv')
    # await synchronise_and_check_all_devices(df)
    await start_recording_all_devices(df)
    await stop_recording_all_devices(df)


if __name__ == "__main__":
    os.chdir('/home/zonghuan/tudelft/projects/spcl_app/BadgeFramework')
    # asyncio.run(main_v2())
    main()
