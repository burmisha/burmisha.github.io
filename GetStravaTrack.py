#!/usr/bin/env python
import requests
import argparse
import sys

def get_track_info(track_id):
	headers = {'Authorization': 'Bearer 3496af3a7307ea53ec7875a6249761a696429add'}
	return requests.get('https://www.strava.com/api/v3/activities/' + track_id + '/streams/latlng', headers=headers).json()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Form lnglat info via Strava TrackId")
	parser.add_argument("-i", "--track_id", dest='track_id', default="160251932", help="Strava TrackId, default: %(default)s")
	args = parser.parse_args()
	data = get_track_info(args.track_id);
	latlng = None
	for d in data:
		if d["type"] == "latlng":
			latlng = d["data"]
	lat = [l[0] for l in latlng]
	lng = [l[1] for l in latlng]
	
	i = 1;
	sys.stdout.write("map:\n")
	sys.stdout.write("  strava: %s\n" % args.track_id)
	sys.stdout.write("  center: \"[%(lat)s, %(lng)s]\"\n" % {"lat":sum(lat)/len(lat), "lng":sum(lng)/len(lng)})
	# sys.stdout.write("  track: >\n    ")
	# for l in latlng:
	# 	sys.stdout.write("[%(lng).6f,%(lat).6f]," % {"lng": l[0], "lat": l[1]})
	# 	if not i % 7: 
	# 		sys.stdout.write("\n    ")
	# 	i += 1
	sys.stdout.write("\n")

	with open("data/tracks/%s.geojson" % args.track_id, "w") as track_file:
		track_file.write("""{
  		"type": "Feature",
  		"geometry": {
    		"type": "LineString",
    		"coordinates": [""")
		i = 1
		for l in latlng:
			track_file.write("%(p)s[%(lng).6f,%(lat).6f]" % {"p": "" if i == 1 else ",", "lng": l[0], "lat": l[1]})
			if not i % 7: 
				track_file.write("\n    ")
			i += 1
		track_file.write("]}}")
