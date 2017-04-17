#! /usr/bin/python
# -*- coding: utf-8 -*-

#
# Uses api.openweathermap.org to determine today's weather. It is
# formatted as a list of strings to be printed onto an LCD.
# To get this working users need to register at openweathermap.org
# to get a unique API-key.
#

import sys
import json
from pprint import pprint
import datetime
import codecs
import urllib2
from time import sleep

def formatTimestamp(timestampString):
	return datetime.datetime.fromtimestamp(int(timestampString)).strftime('%m-%d %H:%M')

lon = "9.05222"
lat = "48.522659"
appId = "aaaa3cad3020d0669852eca703e1185bba28"
todayUrl = 'http://api.openweathermap.org/data/2.5/weather?lat=' + lat + '&lon=' + lon + '&lang=de&units=metric&appid=' + appId
forecastUrl = 'http://api.openweathermap.org/data/2.5/forecast?lat=' + lat + '&lon=' + lon +  '&lang=de&units=metric&appid=' + appId

class weather_reader:
	todayUrl = todayUrl
	forecastUrl = forecastUrl
	weather_list = []
	
	def __init__(self, _todayUrl=todayUrl, _forecastUrl=forecastUrl):
		self.todayUrl = _todayUrl
		self.forecastUrl = _forecastUrl
		self.weather_list = []

	def read_today(self):
		try:
			jsonFile = urllib2.urlopen(self.todayUrl)
			jsonFileContent = jsonFile.read().decode('utf-8')
			jsonObject = json.loads(jsonFileContent)
		except:
			print("err: Could not open " + self.todayUrl)
			return []

		temperature = jsonObject['main']['temp']
		humidity = jsonObject['main']['humidity']
		pressure = jsonObject['main']['pressure']
		weather = jsonObject['weather'][0]['description']
		try:
			windDirection = jsonObject['wind']['deg']
		except:
			windDirection = 'N/A'

		windSpeed = jsonObject['wind']['speed']
		sunRise = jsonObject['sys']['sunrise']
		sunSet= jsonObject['sys']['sunset']

		self.weather_list = [
			"{}: {}{}".format("Temperatur", temperature, "°C"),
			"{}: {}{}".format("Luftfeuchte", humidity, "%"),
			"{}: {}{}".format("Luftdruck", pressure, "hPa"),
			str(weather.encode('utf-8')),
			"{}: {}{}".format("Wind-Richtung", windDirection, "°"),
			"{}: {}{}".format("Wind-Speed", windSpeed, "km/h"),
			"{}: {}".format("Sunrise", formatTimestamp(sunRise)),
			"{}: {}".format("Sunset ", formatTimestamp(sunSet)) ]
		return self.weather_list

	def read_forecast(self):
		try:
			jsonFile = urllib2.urlopen(self.forecastUrl)
			jsonFileContent = jsonFile.read().decode('utf-8')
			jsonObject = json.loads(jsonFileContent)
		except:
			print("err: Could not open " + self.forecastUrl)
			return []
		
		days = jsonObject['list']
		for day in [ days[0], days[1], days[2], days[3] ]:
			dt_txt = day['dt_txt']
			temperature = day['main']['temp']
			humidity = day['main']['humidity']
			pressure = day['main']['pressure']
			weather = day['weather'][0]['description']
			weather_list = [
				str(dt_txt),
				"{}: {}{}".format("Temperatur", temperature, "°C"),
				#"{}: {}{}".format("Luftfeuchte", humidity, "%"),
				"{}: {}{}".format("Luftdruck", pressure, "hPa"),
				str(weather.encode('utf-8')) ]
			for l in weather_list:
				self.weather_list.append(l)

		return self.weather_list

	def read_weather(self):
		self.read_today()
		self.read_forecast()
		return self.weather_list

	def get_weather_list(self):
		return self.weather_list
 
if __name__ == "__main__":
	reader = weather_reader(todayUrl, forecastUrl)
	weather_list = reader.read_weather()
	for w in weather_list:
		# print(type(w))
		print(w)

