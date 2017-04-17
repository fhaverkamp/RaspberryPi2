#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Collect system information and return them in form of a list
# which can be printed on an LCD 20x4.
#

import re
import subprocess
import os
import signal
import time
import Adafruit_DHT

# DHT11 temperature sensor
dht11_pin = 10

# DS1820 Temperature sensor
ds1820_path = ''

def bytestomb(b):
	mb = round(float(b) / (1024 * 1024), 1)
	return mb

class sysinfo_reader:
	""" Gather system statistics return a list of infos """

	sysinfo_list = []
	
	def __init__(self, _dht11_pin=dht11_pin, _ds1820_path=ds1820_path):
		self.dht11_pin = _dht11_pin
		self.dht11_sensor = Adafruit_DHT.DHT11
		self.ds1820_path = _ds1820_path
		self.sysinfo_list = []
			
	def get_ram(self):
		"""Returns a tuple (total ram, available ram) in megabytes. See www.linuxatemyram.com"""
		try:
			s = subprocess.check_output(["free","-m"])
			lines = s.split('\n')       
			return ( int(lines[1].split()[1]), int(lines[2].split()[3]) )
		except:
			return 0

	def get_up_stats(self):
		"""Returns a tuple (uptime, 5 min load average)"""
		try:
			s = subprocess.check_output(["uptime"])
			load_split = s.split('load average: ')
			load_five = float(load_split[1].split(',')[1])
			up = load_split[0]
			up_pos = up.rfind(',', 0, len(up) - 4)
			up = up[:up_pos].split('up ')[1]
			return ( up , load_five )       
		except:
			return ( "" , 0 )

	def get_sysload(self):
		s = os.getloadavg()
		return s

	def get_network_bytes(self, interface):
		""" Read network statistics """
		try:
			output = subprocess.Popen(['/sbin/ifconfig', interface],
							stdout=subprocess.PIPE,
							stderr=subprocess.PIPE).communicate()[0]
		except:
			output = ["RX bytes:0 TX bytes:0"]

		if len(output) != 0:
			rx_bytes = re.findall('RX bytes:([0-9]*) ', output)[0]
			tx_bytes = re.findall('TX bytes:([0-9]*) ', output)[0]
		else:
			rx_bytes = 0
			tx_bytes = 0
		return (bytestomb(rx_bytes), bytestomb(tx_bytes))

	def get_temperature(self):
		"""Returns the temperature in degrees C"""
		try:
			s = subprocess.check_output(["/opt/vc/bin/vcgencmd",
									"measure_temp"])
			return float(s.split('=')[1][:-3])
		except:
			return 0

	def read_ds1820(self):
		"""function: read and parse sensor data file"""
		value = "U"
		try:
			f = open(self.ds1820_path, "r")
			line = f.readline()
			if re.match(r"([0-9a-f]{2} ){9}: crc=[0-9a-f]{2} YES", line):
				line = f.readline()
				m = re.match(r"([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
			if m:
				value = str(float(m.group(2)) / 1000.0)
				f.close()
		except (IOError), e:
			print(time.strftime("%x %X"), "Error reading", path, ": ", e)
		return value

	def get_cpu_speed(self):
		"""Returns the current CPU speed"""
		f = os.popen('/opt/vc/bin/vcgencmd measure_clock arm')
		cpu = f.read()
		return int(cpu.split('=')[1])

	def read_sysinfo(self):
		rx_bytes, tx_bytes = self.get_network_bytes('eth0')
		rx1_bytes, tx1_bytes = self.get_network_bytes('wlan0')
		cpu_speed = self.get_cpu_speed() / 1000000
		ram = self.get_ram()[0]
		humidity, temperature = Adafruit_DHT.read_retry(self.dht11_sensor, self.dht11_pin)
	
		# Screen 1
		self.sysinfo_list = [
			time.strftime("%d.%m %H:%M") + " " + '{0:0.0f}°C/{1:0.0f}%'.format(temperature, humidity),
			'Uptime: ' + self.get_up_stats()[0],
			'Free: ' + str(self.get_ram()[1]) + '/' + str(ram) + 'MB',
			'CPU: ' + str(self.get_temperature()) +'°C ' + str(cpu_speed) + 'MHz',
			'Load: '  + str(os.getloadavg()[0]) + '/' + str(os.getloadavg()[1]),
			'wlan0: ' + str(rx1_bytes) + '/' + str(tx1_bytes) + 'MB',
			'eth0:  ' + str(rx_bytes)  + '/' + str(tx_bytes) + 'MB',
		]
		return self.sysinfo_list

if __name__ == "__main__":
	reader = sysinfo_reader()
	sysinfo_list = reader.read_sysinfo()
	print('01234567890123456789')
	for w in sysinfo_list:
		#print(type(w))
		print(w)

