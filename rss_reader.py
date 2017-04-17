#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Display currently _must_ be 4x20 LCD attached via I2C.
# If not some routines must be changed which currently assumes that.
# We are using:
#   1. RSS feed reader
#   2. Homematic CCU2 to read temperature from each thermostat in
#      our home
#   3. Weather forecast via openweathermap.org
#   4. System statistics derived from a freely available example
#      for RaspberryPi's
#

import time
import sys
import getopt
import lcddriver
import re
import subprocess
import os
import signal
import Adafruit_DHT
import ccu2_lib
import rss_lib
import weather_lib
import sysinfo_lib
import RPi.GPIO as GPIO
import feedparser
import thread

# I2C LCD settings
LCD_WIDTH = 20 		# Zeichen je Zeile
LCD_HEIGHT = 4      # Zeilen

# RSS feed settings
feed_url = 'http://www.tagesschau.de/xml/rss2'
feed_db = 'feeds.db'

# DISPLAY Settings
REFRESH_TIME = 4	# Seconds

# CCU2 url
ccu2_url = 'http://homematic-ccu2/config/xmlapi/'

# Temperature Sensor
dht11_pin = 10
sensor = Adafruit_DHT.DHT11
humidity = 0.0
temperature = 0.0

# Buttons
PIR_PIN = 17
SW0_PIN = 16
SW1_PIN = 20
SW2_PIN = 21

MODE_CLOCK=0
MODE_RSS=1
MODE_TEMP=2

last_motion = 'N/A'
last_button = 'N/A'
mode = MODE_CLOCK

def MOTION_FALLING(pin):
	global mode
	if pin == SW0_PIN:
		mode = MODE_CLOCK
	if pin == SW1_PIN:
		mode = MODE_RSS
	if pin == SW2_PIN:
		mode = MODE_TEMP

def MOTION_RISING(pin):
	global last_motion
	last_motion = time.strftime("%d.%m %H:%M") + ' GPIO' + str(pin)
	#print("RISING EDGE on PIN %d" % pin)
	#print("  last_motion: " + last_motion)

def init_buttons():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(PIR_PIN, GPIO.IN)
	GPIO.setup(SW0_PIN, GPIO.IN)
	GPIO.setup(SW1_PIN, GPIO.IN)
	GPIO.setup(SW2_PIN, GPIO.IN)

	try:
		GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=MOTION_RISING)
		for pin in (SW0_PIN, SW1_PIN, SW2_PIN):
			GPIO.add_event_detect(pin, GPIO.FALLING, callback=MOTION_FALLING,
				bouncetime=150)
	except:
		print("err: Registering Button GPIOs failed!")

# General stuff for debugging
verbose = False

def lcd_banner(lcd):
	"""" Print title banner, temperature and humidity """
	try:
		lcd.lcd_clear()
		lcd.lcd_display_string("Guten Morgen Justus,", 1)
		lcd.lcd_display_string("Alma und Susanne    ", 2)
		lcd.lcd_display_string("            äöüÄÖÜß°", 3)
		lcd.lcd_display_string(time.strftime("%d.%m %H:%M") + " " +
			'{0:0.0f}°C/{1:0.0f}%'.format(temperature, humidity), 4)
		time.sleep(2)
	except:
		print("Hoppla. Es ist etwas schief gelaufen!")

def lcd_print_text(lcd, text):
	""" print full screens with LCD_HEIGH lines """
	screen = 0
	i = 0
	remaining_lines = len(text)
	for screen in range(0, len(text)/LCD_HEIGHT):
		lcd.lcd_clear()
		for line in range(0, LCD_HEIGHT):
			lcd.lcd_display_string(text[i], 1 + line)
			remaining_lines -= 1
			i += 1
		time.sleep(REFRESH_TIME)
	# print remaing lines, if there are any ...
	if remaining_lines > 0:
		lcd.lcd_clear()
		for line in range(0, remaining_lines):
			lcd.lcd_display_string(text[i], 1 + line)
			remaining_lines -= 1
			i += 1
		time.sleep(REFRESH_TIME)

def lcd_temperatures(lcd):
	global temperature, humidity

	reader = ccu2_lib.ccu2_reader(ccu2_url)
	devices = reader.read_device_list()

	# Screen 0 .. n
	lcd_print_text(lcd, devices)

	# Screen n + 1
	lcd.lcd_clear()
	lcd.lcd_display_string(time.strftime("%d.%m %H:%M") + " " +
		'{0:0.0f}°C/{1:0.0f}%'.format(temperature, humidity), 1)
	lcd.lcd_display_string('Aktueller Raum', 2)
	lcd.lcd_display_string('Temperatur:   {0:0.1f}°C'.format(temperature), 3)
	lcd.lcd_display_string('Feuchtigkeit: {0:0.1f}%'.format(humidity), 4)
	time.sleep(REFRESH_TIME)

def lcd_weather(lcd):
	""" Gather todays weather info and print them on a 4x20 LCD display """
	reader = weather_lib.weather_reader()
	weather_list = reader.read_weather()
	lcd_print_text(lcd, weather_list)

def lcd_statistics(lcd):
	""" Gather system statistics and print them on a 4x20 LCD display """
	
	global last_motion
	reader = sysinfo_lib.sysinfo_reader()
	sysinfo_list = reader.read_sysinfo()
	sysinfo_list.append(last_motion)
	lcd_print_text(lcd, sysinfo_list)

# Set up the custom character maps
segs = [[0b11111, 0b11111, 0b11111, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
		[0b11100, 0b11110, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111],
		[0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b01111, 0b00111],
		[0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111, 0b11111, 0b11111],
		[0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11110, 0b11100],
		[0b11111, 0b11111, 0b11111, 0b00000, 0b00000, 0b00000, 0b11111, 0b11111],
		[0b11111, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111, 0b11111, 0b11111],
		[0b00111, 0b01111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111, 0b11111]]

def lcd_create_bigfont(lcd):
	for i in range(8):
		lcd.lcd_clear()
		lcd.lcd_create_char(i, segs[i])

# Create digits and stuff from the custom characters
digits = [["\x07\x00\x01", "\x02\x03\x04"], # 0
		  ["\xfe\x00\x01", "\xfe\xfe\xff"], # 1
		  ["\x05\x05\x01", "\x02\x06\x06"], # 2
		  ["\x05\x05\x01", "\x06\x06\x04"], # 3
		  ["\x02\x03\x01", "\xfe\xfe\xff"], # 4
		  ["\xff\x05\x05", "\x06\x06\x04"], # 5
		  ["\x07\x05\x05", "\x02\x06\x04"], # 6
		  ["\x00\x00\x01", "\xfe\x07\xfe"], # 7
		  ["\x07\x05\x01", "\x02\x06\x04"], # 8
		  ["\x07\x05\x01", "\xfe\xfe\xff"]] # 9

colon = ["\xa5", "\xa5"]
space = ["\xfe", "\xfe"]

# Append a "big" character to two lines of text for the LCD
def writeChar(glyph, lines):
	lines[0] += glyph[0] #+ "\xfe"
	lines[1] += glyph[1] #+ "\xfe"

# Quick and dirty clock implementation
def writeTime(lcd):
	lines = ["", ""]
	
	h = int(time.strftime("%H"))
	m = int(time.strftime("%M"))
	s = int(time.strftime("%S"))
	
	h1 = int(h / 10)
	h2 = h - (h1 * 10)
	m1 = int(m / 10)
	m2 = m - (m1 * 10)
	s1 = int(s / 10)
	s2 = s - (s1 * 10)

	writeChar(digits[h1], lines)
	writeChar(digits[h2], lines)
	writeChar(colon, lines)
	writeChar(digits[m1], lines)
	writeChar(digits[m2], lines)
	writeChar(colon, lines)
	writeChar(digits[s1], lines)
	writeChar(digits[s2], lines)

	for i in range(0, 2):
		lcd.message(lines[i], i + 2)

def measure_temperature( threadName, delay):
	global humidity, temperature
	while True:
		humidity, temperature = Adafruit_DHT.read_retry(sensor, dht11_pin)
		time.sleep(delay)

def init_temperature_measurement():
	# Create temperature measurement thread
	try:
		thread.start_new_thread(measure_temperature, ("Temperature Thread", 5))
	except:
		print "Error: unable to start temperature measurement thread"

def lcd_bigfont_clock(lcd):
	global mode

	lcd.lcd_clear()
	while mode == MODE_CLOCK:
		lcd.lcd_display_string("      " + time.strftime("%a %d.%m.%Y"), 1)
		writeTime(lcd)
		lcd.lcd_display_string('{0:0.0f}°C/{1:0.0f}%'.format(temperature, humidity), 4)
		time.sleep(0.10)

def usage():
	print("rss_ready.py [-h] [-v]")

def main(argv):
	global mode

	try:
		opts, args = getopt.getopt(argv, "rh",
			[ "help", "verbose" ])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit()
		elif opt in ("-v", "--verbose"):
			global verbose
			verbose = True
	source = "".join(args)

	init_temperature_measurement()
	init_buttons()

	lcd = lcddriver.lcd()
	lcd.lcd_create_umlaute()
	lcd_banner(lcd)

	rss = rss_lib.rss_reader(feed_url, feed_db, LCD_WIDTH)
	post_list = rss.parse_feeds()

	while True:
		if mode == MODE_CLOCK:
			lcd.lcd_clear()
			lcd_create_bigfont(lcd)
			lcd_bigfont_clock(lcd)

		if mode == MODE_RSS:
			lcd.lcd_clear()
			lcd.lcd_create_umlaute()
			if len(post_list) == 0:
				post_list = rss.parse_feeds()
			if len(post_list) != 0:
				post = post_list[0]
				post_list.pop(0)
			lcd_print_text(lcd, post)

		if mode == MODE_TEMP:
			lcd.lcd_clear()
			lcd.lcd_create_umlaute()
			lcd_statistics(lcd)
			lcd_temperatures(lcd)
			lcd_weather(lcd)

if __name__ == "__main__":
	main(sys.argv[1:])
