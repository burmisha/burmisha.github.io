#!/usr/bin/env python
import requests
import json
import urllib
import collections
import time

def jsonParam():
	params = collections.OrderedDict()
	params["format"] = "json"
	return urllib.urlencode(params)

def get_photos(album_path):
	previous = ""
	answer = {'entries':[],'links':{'next':album_path}}
	photos = []
	more = True
	# print album_path
	try:
		while more and (previous != answer["links"]["next"]):
			previous = answer["links"]["next"]
			# print previous
			answer = requests.get(previous).json()
			# print len(answer["entries"])
			photos.extend(answer["entries"])
	except KeyError as e:
		more = False
		# print 
	# print type(photos)
	return photos

def get_albums_info(user):
	return requests.get('http://api-fotki.yandex.ru/api/users/' + user + '/albums/published/', params=jsonParam()).json()

def find_album_by_name(albums, albumName):
	for album in albums:
		if album["title"] == albumName:
			return album

def find_albums_by_root(albums, rootName):
	for album in albums:
		try:
			if album["links"]["album"] == rootName:
				yield album
		except KeyError as e:
			pass

def main():
	albums_info = get_albums_info('i-like-spam')["entries"]
	root_album_name = find_album_by_name(albums_info, "2013 UK")["links"]["self"]
	uk_albums_info = find_albums_by_root(albums_info, root_album_name)
	i = 0
	for album_info in uk_albums_info:
		# requests.get(album_info["links"]["self"]).json()
		if i > 10: 
			return
		else:
			i = i + 1
		photos = get_photos(album_info["links"]["self"].split('?', 1)[0] + 'photos/?format=json')
		print album_info["title"] + " -> " + str(len(photos))
	
if __name__ == "__main__":
	main()

