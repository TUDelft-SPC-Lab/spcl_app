from inspect import getsourcefile
import os
from os.path import abspath
from datetime import datetime
import shutil
import sys

def get_script_directory() -> str:
    sourceFile = getsourcefile(lambda: 0)
    if sourceFile == None:
        sys.exit(f"Stopping: could not get sourcefile")
    return os.path.dirname(abspath(sourceFile))


def getshortpath(path: str) -> str:
    return os.sep.join(os.path.normpath(path).split(os.sep)[-2:])


def getFileNameOfPath(path: str) -> str:
    return os.path.basename(path)


def create_path_if_not_exists(path: str, force: bool):
    shortpath = getshortpath(path)
    if os.path.exists(path) and len(os.listdir(path)) != 0 and force:
        print(f"removing path {shortpath}")
        shutil.rmtree(path)
    if not os.path.exists(path):
        print(f"creating non existing directory: {path}")
        os.makedirs(path)
        return
    if len(os.listdir(path)) != 0 and not force:
        sys.exit(
            f"Stopping: directory {shortpath} is not empty, retry with -f if you want to override the data"
        )


def fullTimeName(timestamp: int):
    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H:%M:%S")
    return f"{timestamp}_{date}"
