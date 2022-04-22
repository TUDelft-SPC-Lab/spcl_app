import abc
import csv
import getopt
import json
import math
import sys
from datetime import datetime

import matplotlib.pyplot as plt


class Device(metaclass=abc.ABCMeta):
	def __init__(self, datarate, offset):
		self.datarate = datarate
		self.offset = offset

	@abc.abstractmethod
	def getData(self):
		"""get data from file"""

class Midge(Device):
	def __init__(self, id, offset):
		Device.__init__(self, 57, offset)
		self.id = id

	def getData(self, path, sensor):
		raw = []
		with open(path + "/" + str(self.id) + "/" + sensor + ".csv") as csvfile:
			reader = csv.reader(csvfile)
			next(reader, None)
			for row in reader:
				raw.append(row)

		print(datetime.strptime("2022-01-19 15:43:10", '%Y-%m-%d %H:%M:%S'))

		start = datetime.strptime(raw[0][1], '%Y-%m-%d %H:%M:%S.%f')

		fac = 9.80665 if sensor == 'accel' else 1

		data = [[
			datetime.strptime(item[1], '%Y-%m-%d %H:%M:%S.%f').timestamp() - start.timestamp() + self.offset, 
			[
				float(item[2].replace(',','.')) * fac, 
				float(item[3].replace(',','.')) * fac, 
				float(item[4].replace(',','.')) * fac
		]] for item in raw]

		return data

	def label(self):
		return f'Midge {self.id}'


class Phone(Device):
	def __init__(self, offset):
		Device.__init__(self, 100, offset)

	def label(self):
		return "Phone"

	def getData(self, path, sensor):
		raw = []
		# sensor = 'accel-lin' if sensor == 'accel' else sensor
		with open(path + "/phone/" + sensor + ".csv") as csvfile:
			reader = csv.reader(csvfile, delimiter=',')
			next(reader, None)
			for row in reader:
				raw.append(row)

		fac = 180 / math.pi if sensor == 'gyr' else 1

		data = [[
			float(item[0]) + self.offset, 
			[
				float(item[1]) * fac, 
				float(item[2]) * fac, 
				float(item[3]) * fac
		]] for item in raw]

		return data

def main(argv):

	devices = [
		# Midge(11, 0),
		Midge(14, -20),
		Midge(23, -18.2),
		Phone(-1)
	]

	opts, args = getopt.getopt(argv, "hi:o:",["ifile=","ofile="])

	for sensor in ['gyr', 'accel', 'mag']:

		figure, axis = plt.subplots(3, 1)

		for device in devices:
			print('Plotting for', device)
			data = device.getData(argv[0], "accel")
			for i in range(0,3):
				axis[i].plot([e[0] for e in data], [e[1][i] for e in data], label=device.label(), linewidth=.5)
				axis[i].set_title(['X', 'Y', 'Z'][i])
				axis[i].set_xlabel('t') 
				axis[i].set_ylabel('unit')


		# plt.xlabel('t') 
		# plt.ylabel('unit') 
		# figure.title('Plot')
		plt.legend()
		
		plt.savefig(argv[0] + '/plot-' + sensor + '.png')
		plt.savefig(argv[0] + '/plot-' + sensor + '.svg')

if __name__ == "__main__":
   main(sys.argv[1:])
