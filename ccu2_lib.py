#!/usr/bin/python
#
# Read out temperature from all thermostats connected to our Homatic
# CCU2. Use all where we find the datapoint "ACTUAL_TEMPERATURE".
#
# (c) Frank Haverkamp 2016
#

import urllib2
from xml.dom.minidom import parse
import xml.dom.minidom

# Default URL for test-purposes
ccu2_url = 'http://homematic-ccu2/config/xmlapi/'

class ccu2_reader:
	url = ''
	device_list = []

	def __init__(self, url):
		self.url = url
		self.device_list = []

	def read_device(self, name, ise_id):
		try:
			response = urllib2.urlopen(self.url + 'state.cgi?device_id=' +
				str(ise_id))
			device_xml = response.read()
		except URLError as e:
			print(e.reason)

		DOMTree = xml.dom.minidom.parseString(device_xml)
		collection = DOMTree.documentElement

		datapoints = collection.getElementsByTagName("datapoint")
		for datapoint in datapoints:
			if datapoint.hasAttribute("type"):
				_type = datapoint.getAttribute("type")
				if _type == "ACTUAL_TEMPERATURE":
					value = datapoint.getAttribute("value")
					valueunit = datapoint.getAttribute("valueunit")
					tmp = ("%12s: %0.1f%s" % (name, float(value), valueunit))
					self.device_list.append(tmp.encode('utf-8'))

	def read_device_list(self):
		try:
			response = urllib2.urlopen(self.url + 'devicelist.cgi')
			ccu2_xml = response.read()
		except urllib2.URLError as e:
			print(e.reason)
			return []

		DOMTree = xml.dom.minidom.parseString(ccu2_xml)
		collection = DOMTree.documentElement

		if collection.hasAttribute("deviceList"):
			print "Root element : %s" % collection.getAttribute("deviceList")

		devices = collection.getElementsByTagName("device")
		for device in devices:
			if device.hasAttribute("name"):
				name = device.getAttribute("name")
			if device.hasAttribute("ise_id"):
				ise_id = device.getAttribute("ise_id")
				self.read_device(name, ise_id)

		return self.device_list

if __name__ == "__main__":
	reader = ccu2_reader(ccu2_url)
	device_list = reader.read_device_list()
	for device in device_list:
		# print(type(device))
		print(device)

