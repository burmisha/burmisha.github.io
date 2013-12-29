#!/usr/bin/env python
import requests
import json
import urllib
import collections
import time
import argparse

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

def find_albums_by_root(albums, root_album_path):
	for album in albums:
		if ("album" in album["links"]) and (album["links"]["album"] == root_album_path):
			if album["title"].startswith('July') or album["title"].startswith('Aug'):
				yield album

def get_photos_from_albums(albums_info):
	for album_info in albums_info:
		for photo in get_photos(album_info["links"]["self"].split('?', 1)[0] + 'photos/?format=json'):
			yield photo

def get_coordinates(photo):
	c = photo["geo"]["coordinates"].split(" ")
	return [c[1], c[0]]

def get_point_from_photo(photo):
	return {
				"type": "Feature", 
				"geometry": { 
					"type": "Point",
					"coordinates": get_coordinates(photo),
					},
				"properties": {
					"M_url": photo["img"]["M"]["href"],
					"S_url": photo["img"]["S"]["href"],
				},
			}

def get_middle_point(photos, idx, reject_rate):
	coords = sorted([get_coordinates(p)[idx] for p in photos if "geo" in p]);
	left = float(coords[int(len(coords) * reject_rate)])
	right = float(coords[int(len(coords) * (1 - reject_rate))])
	return (left + right) / 2

def form_geojson(user, root_album_name):
	albums_info = get_albums_info(user)["entries"]
	root_album_path = find_album_by_name(albums_info, root_album_name)["links"]["self"]
	uk_albums_info = find_albums_by_root(albums_info, root_album_path)
	photos = list(get_photos_from_albums(uk_albums_info))
	return {
				"type": "FeatureCollection", 
				"view_point": [get_middle_point(photos, i, 0.4) for i in [1,0]],
				"features": [get_point_from_photo(photo) for photo in photos if "geo" in photo],
			}

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Form GeoJson file from one album with subalbums.")
	parser.add_argument("-u", "--user", dest='user', default="i-like-spam", help="username, default: %(default)s")
	parser.add_argument("-n", "--name", dest='name', default="2013 UK", help="root directory , default: %(default)s")
	parser.add_argument("-o", "--output", dest='output', default="uk.geojson", help="output file, default: %(default)s")
	args = parser.parse_args()
	geojson = form_geojson(args.user, args.name)
	with open(args.output, 'w') as fp:
		json.dump(geojson, fp, indent=2, separators=(',', ': '))
	
