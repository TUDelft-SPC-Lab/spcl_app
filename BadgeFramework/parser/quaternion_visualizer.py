import pandas as pd
import numpy as np
from pandas.core.frame import DataFrame
import matplotlib.pyplot as plt
from squaternion import Quaternion


def convertToEuler(row):
    euler = Quaternion(w=row["a"], x=row["b"], y=row["c"],
                       z=row["d"]).to_euler(degrees=True)
    mag = np.linalg.norm(euler)
    return pd.Series(
        dict(time=row["time"], x=euler[0], y=euler[1], z=euler[2], mag=mag)
    )


class QuaternionVisualizer:
    def __init__(self, dataframe: pd.DataFrame, outputPathNoExtension: str, experimentName: str) -> None:
        self.dataframe = dataframe
        self.outputPathNoExtension = outputPathNoExtension
        self.experimentName = experimentName
        pass

    def plot(self):
        eulerDataFrame = self.dataframe.apply(convertToEuler, axis=1)

        eulerDataFrame.plot(
            x="time", title=f"{self.experimentName}: DMP Euler Rotation", subplots=True)
        plt.tight_layout()
        fig = plt.gcf()

        fig.savefig(self.outputPathNoExtension + "_euler.png")

    def plot2(self):

        self.dataframe.plot(
            x="time", title=f"{self.experimentName}: DMP Quaternion", subplots=True)
        plt.tight_layout()
        fig = plt.gcf()

        fig.savefig(self.outputPathNoExtension + "_quaternion.png")
