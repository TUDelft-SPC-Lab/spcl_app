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
    logger.info("Connecting to the midges for starting the recordings.")
    # TODO: uncomment the recording function
    # start_recording_all_devices(df)
    logger.info("Loop for starting the devices is finished.")


def stop_recording_cmd(logger):
    logger.info("Stopping the recording of all devices.")
    sys.stdout.flush()
    # TODO: uncomment the stop recording function
    # stop_recording_all_devices(df)
    logger.info("Devices are stopped.")
    sys.stdout.flush()


def interactive_cmd(logger, df):
    while True:
        logger.info(
            "Interactive shell of midge sensor. Please type the id of the midge you want to connect. Type exit to quit."
        )
        sys.stdout.write("> ")
        sys.stdout.flush()
        command = sys.stdin.readline()[:-1]
        if command == "exit":
            break

        # Check valid input id
        try:
            midge_id = int(command)
        except ValueError:
            logger.warning('Invalid id! Only integers are allowed.')
            continue

        try:
            current_mac_addr = df.loc[df["Participant Id"] == midge_id]["Mac Address"]
            current_mac_addr = current_mac_addr.values[0]
        except Exception as e:
            logger.info('Mac address for the midge ' + str(midge_id) + ' is not found.')
            continue

        # try connection
        try:
            # TODO: uncomment the connection function
            # cur_connection = Connection(int(command), current_mac_addr)
            logger.info('placeholder for connection')
        except Exception as error:
            logger.warning("While connecting to midge " + str(command)
                           + ", following error occurred:" + str(error))
            sys.stdout.flush()
            continue

        single_sensor_cmd(logger, midge_id)


def single_sensor_cmd(logger, midge_id):
    while True:
        logger.info("Connected to the midge " + str(midge_id) + "."
                    + " For available commands, please type help.")
        sys.stdout.flush()
        # sys.stdout.write("Now connected to the midge\n > ")
        command = sys.stdin.readline()[:-1]
        command_args = command.split(" ")
        if command == "exit":
            # TODO: uncomment the disconnect function
            # cur_connection.disconnect()
            logger.info("Disconnected from the midge.")
            break
        elif command == "help":
            # TODO: uncomment the print help function
            # cur_connection.print_help()
            continue
        else:
            handle_function_choice(logger)
            continue


def handle_function_choice(logger):
    try:
        # TODO: uncomment the choose function
        # out = choose_function(cur_connection, command_args[0])
        # if out is not None:
        #     logger.info("Midge returned following status: " + str(out))
        sys.stdout.flush()
    except Exception as error:
        logger.warning(str(error))
        sys.stdout.flush()


def synchronization_cmd(logger):
    logger.info("Synchronization is starting. Please wait till it ends")
    # TODO: uncomment the synchronization function
    # synchronise_and_check_all_devices(df)
    logger.info("Synchronization is finished.")
    sys.stdout.flush()


def command_line():
    df = pd.read_csv("mappings2.csv")
    logger = get_logger("hub_main")
    recording_started = False
    while True:
        logger.info("Interactive shell of midge hub. Type 'help' for options.")
        sys.stdout.write("> ")
        sys.stdout.flush()
        command = sys.stdin.readline()[:-1]
        if command == "start":
            if not recording_started:
                recording_started = True
                start_recording_cmd(logger)
            else:
                logger.warning("Recording already started.")
        elif command == "stop":
            if recording_started:
                stop_recording_cmd(logger)
                recording_started = False
            else:
                logger.warning("Cannot stop. Recording not started.")
        elif command == "sync":
            if recording_started:
                synchronization_cmd(logger)
            else:
                logger.warning("Cannot synchronize. Recording not started.")
        elif command == "int":
            interactive_cmd(logger, df)
        elif command == "help":
            # TODO: add help
            logger.info("help placeholder")
        elif command == "exit":
            break
        else:
            logger.warning('Command not recognized.')
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
    # os.chdir('/home/zonghuan/tudelft/projects/spcl_app/BadgeFramework')
    # asyncio.run(main_v2())
    # main()
    # df = pd.read_csv('mappings2.csv')
    command_line()
