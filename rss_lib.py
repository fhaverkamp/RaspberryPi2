#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Reads RSS feed and formats it to fit onto an LCD display.
# Returns list of post, where each post is a list of strings
# with appropriate length.
#

import feedparser
import time
import sys
import getopt
import html2text
import re

url = 'http://www.tagesschau.de/xml/rss2'
db = 'feeds.db'
limit = 12 * 3600 * 1000

#
# functions to get the current time
#
current_time_millis = lambda: int(round(time.time() * 1000))
current_timestamp = current_time_millis()

class rss_reader:
	url = ''
	db = ''
	text_list = []
	width = 20

	def __init__(self, url, db, width=20):
		self.url = url
		self.db = db
		self.text_list = []
		self.width = width

	def post_is_in_db(self, title):
		""" Check if title is already in database """
		try:
			with open(self.db, 'r') as database:
				for line in database:
					if title in line:
						return True
		except:
			return False
		return False

	def post_is_in_db_with_old_timestamp(self, title):
		""" true if the title is in the db with timestamp > limit """
		try:
			with open(self.db, 'r') as database:
				for line in database:
					if title in line:
						ts_as_string = line.split('|', 1)[1]
						ts = long(ts_as_string)
						if current_timestamp - ts > limit:
							return True
		except:
			return False
		return False

	def parse_feeds(self):
		""" get the feed data from the url """
		feed = feedparser.parse(self.url)
		posts_to_print = []
		posts_to_skip = []

		for post in feed.entries:
			# if post is already in the database, skip it
			# TODO check the time
			title = post.title
			if self.post_is_in_db_with_old_timestamp(title):
				posts_to_skip.append(title)
			else:
				posts_to_print.append(post)

		# add all the posts we're going to print to the database with the
		# current timestamp (but only if they're not already in there)
		f = open(self.db, 'a')
		for post in posts_to_print:
			if not self.post_is_in_db(post.title):
				f.write(post.title.encode("utf-8") + "|" +
						str(current_timestamp) + "\n")
		f.close

		# output all of the new posts
		count = 1
		for post in posts_to_print:
			h2t = html2text.HTML2Text()
			h2t.inline_links = False
			h2t.ignore_links = True
			h2t.ignore_images = True
			h2t.ignore_emphasis = True
			h2t.skip_internal_links = True
			h2t.body_width = self.width
			text = []
			date = time.strftime("%d.%m %H:%M") + ' ' + '[' + str(count) + ']'
			text.append(date)

			title = h2t.handle(post.title)
			for line in title.split('\n'):
				if not line.strip():
					pass
				else:
					text.append(str(line.encode('utf-8')))

			# Try to filter out links even before passing to the formatter
			# Example: <a href='http://earth.google.com/'>world</a>
			pattern =r'\[*<a.*?>.*?</a>\]*'
			result = re.sub(pattern , "", post.description)
	
			description = h2t.handle(result)
			for line in description.split('\n'):
				if line.startswith("  *"):
					pass
				elif not line.strip():
					pass
				else:
					text.append(str(line.encode('utf-8')))

			self.text_list.append(text)
			count += 1
		return self.text_list

if __name__ == "__main__":
	rss = rss_reader(url, db, 20)
	post_list = rss.parse_feeds()
	for post in post_list:
		print('*' * 22)
		for line in post:
			# print(type(line))
			print('  ' + line)
