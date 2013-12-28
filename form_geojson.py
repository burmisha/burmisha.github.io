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
	answer = requests.get(album_path).json()
	photos = answer["entries"]
	if "next" in answer["links"]:		
		photos.extend(get_photos(answer["links"]["next"]))
	return photos

def get_albums_info(user):
	return requests.get('http://api-fotki.yandex.ru/api/users/' + user + '/albums/published/', params=jsonParam()).json()

def find_album_by_name(albums, albumName):
	for album in albums:
		if album["title"] == albumName:
			return album

def find_albums_by_root(albums, rootName):
	for album in albums:
		if ("album" in album["links"]) and (album["links"]["album"] == rootName):
			yield album


def main():
	albums_info = get_albums_info('i-like-spam')["entries"]
	root_album_name = find_album_by_name(albums_info, "2013 UK")["links"]["self"]
	uk_albums_info = find_albums_by_root(albums_info, root_album_name)
	i = 0
	for album_info in uk_albums_info:
		if i > 10: 
			return
		else:
			i = i + 1
		photos = get_photos(album_info["links"]["self"].split('?', 1)[0] + 'photos/?format=json')
		print album_info["title"] + " -> " + str(len(photos))
	
if __name__ == "__main__":
	main()

