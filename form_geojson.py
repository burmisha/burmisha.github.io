#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import os
import requests
import pprint
import yaml
import datetime

import fitparse
import gpxpy.gpx

# https://stuvel.eu/flickrapi
import flickrapi

import logging
log = logging.getLogger(__file__)


class Secrets(object):
    def Init(self, filename):
        with open(filename) as f:
            self.Data = json.load(f)

    def Get(self, secretKey):
        return self.Data[secretKey]


secrets = Secrets()


def savePrettyJson(filename, data):
    try:
        result = json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False, sort_keys=True).encode('utf8')
    except:
        log.exception(data)
        raise
    with open(filename, 'w') as f:
        f.write(result)


class Photo(object):
    def __init__(self):
        self.HasGeo = False
        self.Title = None

    def SetTitle(self, title):
        self.Title = title

    def SetUrls(self, smallSquare=None, medium=None, original=None):
        self.SmallSquareUrl = smallSquare
        self.MediumUrl = medium
        self.OriginalUrl = original

    def SetCoordinates(self, coordinates={}, longitude=None, latitude=None):
        self.Latitude = coordinates.get('latitude', latitude)
        self.Longitude = coordinates.get('longitude', longitude)
        self.HasGeo = self.Latitude is not None and self.Longitude is not None

    # def __str__(self):
    #     return self.ToDict()

    def ToDict(self):
        result = {
            'HasGeo': self.HasGeo,
            'Title': self.Title,
            'SmallSquareUrl': self.SmallSquareUrl,
            'MediumUrl': self.MediumUrl,
            'OriginalUrl': self.OriginalUrl,
        }
        if self.HasGeo:
            result.update({
                'Latitude': self.Latitude,
                'Longitude': self.Longitude,
            })
        return result

    @staticmethod
    def FromDict(data):
        photo = Photo()
        photo.SetUrls(
            smallSquare=data['SmallSquareUrl'],
            medium=data['MediumUrl'],
            original=data['OriginalUrl'],
        )
        if data.get('title'):
            photo.SetTitle(data['title'])
        if data.get('HasGeo'):
            photo.SetCoordinates(longitude=data['Longitude'], latitude=data['Latitude'])
        return photo

    # def __repr__(self):
    #     return str(self.__str__())


class MinMax(object):
    def __init__(self):
        self.Min = None
        self.Max = None
        self.Values = []

    def __call__(self, value):
        self.Values.append(value)
        v = float(value)
        if self.Min is None or v < self.Min:
            self.Min = v
        if self.Max is None or v > self.Max:
            self.Max = v

    def Median(self):
        return (self.Min + self.Max) / 2

    def Mean(self):
        # TODO: index 1 or 2 mean
        self.Values.sort()
        return self.Values[len(self.Values) / 2]

    def Center(self, rejectRate):
        values = sorted(self.Values)
        left = values[int(len(values) * rejectRate)]
        right = values[int(len(values) * (1 - rejectRate))]
        return (float(left) + right) / 2


class YandexFotki(object):
    def __init__(self, username, rootAlbumName=None, prefixes=[]):
        self.Username = username
        self.RootAlbumName = rootAlbumName
        self.Prefixes = prefixes
        self.AlbumsInfo = None

    def GetAlbumsInfo(self):
        if self.AlbumsInfo:
            return self.AlbumsInfo

        albumsInfo = requests.get(
            'http://api-fotki.yandex.ru/api/users/{}/albums/published/'.format(self.Username),
            params={'format': 'json'}
        ).json()
        answer = albumsInfo['entries']
        while 'next' in albumsInfo['links']:
            albumsInfo = requests.get(albumsInfo['links']['next']).json()
            answer.extend(albumsInfo['entries'])
        self.AlbumsInfo = answer
        return self.AlbumsInfo

    def GetPhotosFromAlbumImpl(self, albumPath):
        answer = requests.get(albumPath).json()
        photos = answer['entries']
        if 'next' in answer['links']:
            photos.extend(self.GetPhotosFromAlbumImpl(answer['links']['next']))
        return photos

    def FindAlbum(self, albumName=None, albumId=None):
        matched = []
        for album in self.GetAlbumsInfo():
            if albumName and album['title'] == albumName:
                log.info('Got album %r', album['title'])
                matched.append(album)
            if albumId and album['id'] == 'urn:yandex:fotki:{}:album:{}'.format(self.Username, albumId):
                log.info('Got album %r', album['title'])
                matched.append(album)

        if len(matched) != 1:
            pprint.pprint(self.GetAlbumsInfo())
            raise RuntimeError('Error searching album: {}, {}: {}'.format(albumName, albumId, matched))
        link = matched[0]['links']['self']
        log.info('Link: %r', link)
        return link

    def FindAlbumsByRoot(self, rootAlbumPath):
        for album in self.GetAlbumsInfo():
            if ('album' in album['links']) and (album['links']['album'] == rootAlbumPath):
                if self.Prefixes:
                    if any(album['title'].startswith(prefix) for prefix in self.Prefixes):
                        yield album
                else:
                    yield album

    def GetPhotosFromAlbum(self, albumInfo=None, url=None):
        if albumInfo:
            log.info('Getting photos from %r', albumInfo['title'])
            albumPath = albumInfo['links']['self']
        else:
            log.info('Getting photos from %r', url)
            albumPath = url

        albumPath = albumPath.split('?', 1)[0] + 'photos/?format=json'
        log.info('Getting photos from %r', albumPath)

        for photoItem in self.GetPhotosFromAlbumImpl(albumPath):
            photo = Photo()
            photo.SetUrls(
                smallSquare=photoItem['img']['S']['href'],
                medium=photoItem['img']['M']['href'],
                original=photoItem['img']['orig']['href'],
            )
            photo.SetTitle(photoItem['title'])
            if 'geo' in photoItem:
                latitude, longitude = photoItem['geo']['coordinates'].split(' ')
                photo.SetCoordinates(
                    longitude=float(longitude),
                    latitude=float(latitude)
                )
            yield photo

    def GetPhoto(self, photoInfo=None, url=None):
        if photoInfo:
            photoPath = photoInfo['links']['self']
        else:
            photoPath = url
        return requests.get(photoPath).json()

    def FindPhotos(self):
        rootAlbumPath = self.FindAlbum(albumName=self.RootAlbumName)
        chosenAlbumsInfo = self.FindAlbumsByRoot(rootAlbumPath)
        for albumInfo in chosenAlbumsInfo:
            for photo in self.GetPhotosFromAlbum(albumInfo=albumInfo):
                yield photo


class Flickr(object):
    def __init__(self, username):
        apiKey = secrets.Get('FlickrApiKey')
        apiSecret = secrets.Get('FlickrApiSecret')
        self.FlickrAPI = flickrapi.FlickrAPI(apiKey, apiSecret, format='parsed-json')

        nsid = self.FlickrAPI.people.findByUsername(username=username)
        self.Nsid = nsid['user']['nsid']
        log.info('nsid: %s', self.Nsid)

    def GetSizes(self, photoId, sizes):
        data = self.FlickrAPI.photos.getSizes(photo_id=photoId)
        result = {}
        availableSizes = dict((size['label'], size) for size in data['sizes']['size'])
        for size in sizes:
            result[size] = availableSizes[size]['source']
        return result

    def GetLocation(self, photoId):
        count = 0
        ok = False
        while not ok and count <= 3:
            try:
                data = self.FlickrAPI.photos.geo.getLocation(photo_id=photoId)
                ok = True
            except flickrapi.exceptions.FlickrError:
                log.info('failure')
                count += 1
        if not ok:
            raise RuntimeError()

        result = {}
        for key in ['latitude', 'longitude']:
            result[key] = float(data['photo']['location'][key])
        return result

    def GetPhotos(self, photosetId):
        r = self.FlickrAPI.photosets.getPhotos(photoset_id=photosetId, user_id=self.Nsid)
        assert len(r['photoset']['photo']) == r['photoset']['total']
        for index, photoItem in enumerate(r['photoset']['photo']):
            photoId = photoItem['id']
            log.info('Getting photo %s (%d)', photoId, index + 1)
            photo = Photo()
            sizes = self.GetSizes(photoId, ['Large Square', 'Medium', 'Original'])
            photo.SetUrls(
                smallSquare=sizes['Large Square'],
                medium=sizes['Medium'],
                original=sizes['Original'],
            )
            photo.SetCoordinates(self.GetLocation(photoId))
            yield photo


class GeoJson(object):
    def FormCoordinates(self, photo):
        # platform dependent
        return [photo.Latitude, photo.Longitude]

    def GeoPoint(self, photo):
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': self.FormCoordinates(photo),
            },
            'properties': {
                'M_url':    photo.MediumUrl,
                'S_url':    photo.SmallSquareUrl,
                'orig_url': photo.OriginalUrl,
            },
        }

    def Form(self, photos):
        features = []
        minMaxLongitude = MinMax()
        minMaxLatitude = MinMax()
        for photo in photos:
            minMaxLongitude(photo.Longitude)
            minMaxLatitude(photo.Latitude)
            features.append(self.GeoPoint(photo))

        rejectRate = 0.2
        photoMock = Photo()
        photoMock.SetCoordinates(
            longitude=minMaxLongitude.Center(rejectRate),
            latitude=minMaxLatitude.Center(rejectRate),
        )
        data = {
            'type': 'FeatureCollection',
            'features': features,
            'view_point': self.FormCoordinates(photoMock),
        }
        return data

    def FormAndSave(self, photos, filename):
        log.info('Saving %d photos to %r', len(photos), filename)
        geojson = self.Form(photos)
        savePrettyJson(filename, geojson)


DefaultConfig = {
    'YandexFotkiUser': 'i-like-spam',
    'RootNames': {
        '2013 UK':          'uk.geojson',
        '2014.01 Istanbul': 'tur.geojson',
    },
    'AllowedPrefixes': [
        'July',
        'Aug',
        '2014',
    ],
    'FlickrUser': 'burmisha',
    'FlickrAlbums': {
        '72157650399997108': 'germany14-1.geojson',
    },
    'GpxFolders': [
        '2014-05-Baltic',
        '2014-07-Hungary',
        '2014-07-NNov',
        '2014-08-Moldova',
        '2014-11-Germany',
        '2014-12-Switzerland',
        '2015-01-Prague',
        '2015-05-Italy',
        '2015-07-Greece',
        '2015-07-Klyazma',
        '2015-08-Karelia',
        '2016-05-Montenegro',
        '2016-07-Baku',
        '2016-08-Georgia',
        '2017-09-Italy',
        '2017-11-Germany',
        '2017-12-Germany',
    ],
}


def findAllPhotos():
    for rootName, basename in DefaultConfig['RootNames'].iteritems():
        yandexFotki = YandexFotki(
            DefaultConfig['YandexFotkiUser'],
            rootAlbumName=rootName,
            prefixes=DefaultConfig['AllowedPrefixes'],
        )
        photos = [photo for photo in yandexFotki.FindPhotos() if photo.HasGeo]
        yield photos, basename

    flickr = Flickr(DefaultConfig['FlickrUser'])
    for albumKey, basename in DefaultConfig['FlickrAlbums'].iteritems():
        photos = list(flickr.GetPhotos(albumKey))
        yield photos, basename


class Filename(object):
    def __init__(self, dirname):
        self.Dirname = dirname

    def __call__(self, basename):
        return os.path.join(self.Dirname, basename)


def downloadPhotos(args):
    filename = Filename(args.dir)
    geoJson = GeoJson()
    for photos, basename in findAllPhotos():
        geoJson.FormAndSave(photos, filename(basename))


class Strava(object):
    def __init__(self, bearer):
        self.Bearer = bearer

    def GetTrack(self, trackId):
        headers = {'Authorization': 'Bearer {}'.format(self.Bearer)}
        url = 'https://www.strava.com/api/v3/activities/{}/streams/latlng'.format(trackId)
        return requests.get(url, headers=headers).json()

    def FormPage(self, filename, trackId):
        data = self.GetTrack(trackId)
        latlng = None
        for d in data:
            if d['type'] == 'latlng':
                latlng = d['data']
        assert latlng is not None
        count = len(latlng)

        log.info('''Add snippet to your page
map:
  strava: {}
  center: "[{}, {}]"
'''.format(
    trackId,
    sum([l[0] for l in latlng]) / count,
    sum([l[1] for l in latlng]) / count)
)

        data = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': latlng,
            }
        }
        savePrettyJson(filename, data)


class Wantr(object):
    def __init__(self):
        self.ApiUrl = 'http://api.wantr.ru/0.1'

    def Save(self, filename, username):
        user  = requests.get('{}/user/{}'.format(self.ApiUrl, username)).json()
        wishlist  = requests.get('{}/wishlist/{}'.format(self.ApiUrl, user['id'])).json()
        y = {'wishes':[]}

        for t in w['wishes']:
            items = []
            for wish in w['wishes'][t]['content']:
                items.append(w['wishes'][t]['content'][wish])
            y['wishes'].append({'name'  : w['wishes'][t]['name'],
                                'items' : items})

        with open(filename, 'w') as yaml_file:
            yaml_file.write("""---
layout: default
title: Wishlist
""")
        yaml_file.write(yaml.safe_dump(y, allow_unicode=True, default_flow_style=False))
        yaml_file.write(r"""---
<div id="wishlist">
{% for category in page.wishes %}
<h2>{{ category.name }}</h2>
<ul>
{% for item in category.items %}
  <li>
    {% if item.link %}
    <a href="{{ item.link }}">{{ item.title }}</a>
    {% else %}
      {{ item.title }}
    {% endif %}
    {% if item.price %}
      – {{ item.price }}&nbsp;руб.
    {% endif %}
  </li>
{% endfor %}
</ul>
{% endfor %}
</div>

<p>
Это иногда обновляемая копия моего wishlist'а (далеко не всегда актуальна)
на <a href=http://wantr.ru/burmisha>Wantrе</a> (актуален),
который, в свою очередь, является копей странички
<a href=http://mywishlist.ru/wishlist/burmisha>mywishlist</a> (он неактуален).
</p>
""")


class Converter(object):
    def __init__(self):
        self.YandexFotki = YandexFotki(DefaultConfig['YandexFotkiUser'])

    def YaFotkiUrl(self, url):
        return 'http://img-fotki.yandex.ru/get/{}_orig'.format(url)

    def ReadYaml(self, filename):
        lines = []
        tail = []
        inTail = False
        with open(filename) as f:
            for line in f:
                if line == '---\n':
                    if lines:
                        inTail = True
                else:
                    if inTail:
                        tail.append(line.rstrip('\n').decode('utf-8'))
                    else:
                        lines.append(line)

        postProps = yaml.load(''.join(lines))
        if tail and tail[0] == '<p>':
            tail = tail[1:]
        if tail and tail[-1] == '</p>':
            tail = tail[:-1]
        return postProps, tail

    def Load(self, filename):
        log.info('Reading %r', filename)
        date = os.path.basename(filename)[:10]
        postProps, tail = self.ReadYaml(filename)

        yaFotki = None
        knownPhotos = {}
        if 'YaFotki' in postProps:
            yaFotki = postProps['YaFotki']
            albumPath = self.YandexFotki.FindAlbum(albumId=yaFotki)
            for photo in self.YandexFotki.GetPhotosFromAlbum(url=albumPath):
                knownPhotos[photo.OriginalUrl] = photo

        title = None
        twitterPhoto = None
        twitterText = None
        mapStrava = None
        mapCenter = None
        mapScale = None
        series = []
        captions = []
        mainPhotos = []
        usedPhotos = {}
        for key, value in postProps.iteritems():
            if key == 'YaFotki':
                log.debug('Already processed')
            elif key == 'Dropbox':
                log.warn('Dropbox links are deprecated')
            elif key == 'main_photos':
                for photo in value:
                    mainPhotos.append(knownPhotos[self.YaFotkiUrl(photo)].Title)
            elif key == 'tags':
                log.warn('Got tags: {}'.format(value))
            elif key == 'layout':
                assert value == 'default'
            elif key == 'photos':
                usedTitles = set()
                for index, item in enumerate(value):
                    urls = []
                    caption = None
                    isText = False
                    for photoKey, photoValue in item.iteritems():
                        if photoKey == 'url':
                            urls.append(photoValue)
                        elif photoKey == 'urls':
                            urls.extend(photoValue)
                        elif photoKey == 'caption':
                            caption = photoValue.rstrip()
                        elif photoKey == 'text':
                            caption = photoValue.rstrip()
                            isText = True
                        else:
                            raise RuntimeError('Unknown photo key: {!r}'.format(photoKey))
                    matchedTitles = []
                    for url in urls:
                        yaFotkiUrl = self.YaFotkiUrl(url)
                        matchedTitle = knownPhotos.get(yaFotkiUrl).Title
                        if not matchedTitle:
                            raise RuntimeError('No title for {}: {}'.format(yaFotkiUrl, knownPhotos))
                        matchedTitles.append(matchedTitle)
                    if matchedTitles:
                        usedTitles |= set(matchedTitles)
                        series.append(matchedTitles)

                    if caption:
                        if series:
                            captions.append((caption, series[-1], isText))
                        else:
                            if index >= 1:
                                raise RuntimeError('Caption and no photos: {!r}, {}, {}'.format(caption, index, item))
                            else:
                                captions.append((caption, [], isText))
                                log.warn('Text in the beginning')
                        log.debug('%r, %r, %r', caption, matchedTitles, isText)

                for photoUrl, photo in knownPhotos.iteritems():
                    if photo.Title in usedTitles:
                        usedPhotos[photo.Title] = photo.ToDict()
                    else:
                        log.warn('Photo %r missing in post: %r', photo.Title, photo.OriginalUrl)

            elif key == 'title':
                title = value
            elif key == 'twitter':
                for twitterKey, twitterValue in value.iteritems():
                    if twitterKey == 'photo':
                        twitterPhoto = knownPhotos[self.YaFotkiUrl(twitterValue)].Title
                    elif twitterKey == 'text':
                        twitterText = twitterValue
                    else:
                        raise RuntimeError('Unknown twitter key: {!r}'.format(twitterKey))
            elif key == 'map':
                for mapKey, mapValue in value.iteritems():
                    if mapKey == 'strava':
                        mapStrava = 'https://www.strava.com/activities/{}'.format(mapValue)
                    elif mapKey == 'center':
                        mapCenter = mapValue
                    elif mapKey == 'scale':
                        mapScale = mapValue
                    else:
                        raise RuntimeError('Unknown map key: {!r}'.format(mapKey))
            else:
                raise RuntimeError('Unknown key {!r}'.format(key))

        return {
            'date': date,
            'title': title,
            'mainPhotos': mainPhotos,
            'twitterPhoto': twitterPhoto,
            'twitterText': twitterText,
            'mapStrava': mapStrava,
            'mapCenter': mapCenter,
            'mapScale': mapScale,
            'series': series,
            'captions': captions,
            'tail': tail,
            'yaFotki': yaFotki,
            'photos': usedPhotos,
        }


class GeoPoint(object):
    def __init__(self, longitude=None, latitude=None, altitude=None, timestamp=None):
        self.Longitude = longitude
        self.Latitude = latitude
        self.Altitude = altitude
        self.Timestamp = timestamp

    def GetDatetime(self):
        return datetime.datetime.fromtimestamp(self.Timestamp)

    def __repr__(self):
        return str(self.__str__())

    def __str__(self):
        return {
            'Lng': self.Longitude,
            'Lat':  self.Latitude,
            'Alt':  self.Altitude,
            'Ts': self.Timestamp,
            'Dt': self.GetDatetime(),
        }


class FitParser(object):
    def __init__(self):
        pass

    def FromSemicircles(self, value):
        # https://forums.garmin.com/forum/developers/garmin-developer-information/60220-
        return float(value) * 180 / (2 ** 31)

    def __call__(self, filename):
        log.debug('Reading {}'.format(filename))
        fitFile = fitparse.FitFile(filename)
        fitFile.parse()
        failures = []
        count = 0
        for index, message in enumerate(fitFile.get_messages(name='record')):
            count = index + 1
            values = message.get_values()
            timestamp = int((values['timestamp'] - datetime.datetime(1970, 1, 1)).total_seconds())
            try:
                assert timestamp > 100000000
                if 'enhanced_altitude' in values:
                    assert values['enhanced_altitude'] == values['altitude']
                if 'position_long' not in values:
                    failures.append(count)
                    continue
                geoPoint = GeoPoint(
                    longitude=self.FromSemicircles(values['position_long']),
                    latitude=self.FromSemicircles(values['position_lat']),
                    altitude=values['altitude'],
                    timestamp=timestamp,
                )
                yield geoPoint
            except:
                log.exception('Complete failure on {}'.format(count))
                pprint.pprint(values)
                raise

        log.info('File {} has {} points and {} failures: {}...'.format(filename, count, len(failures), failures[:3]))
        if len(failures) > 150 or len(failures) > 0.2 * count:
            raise RuntimeError('A lot of failures')


class GpxWriter(object):
    def __call__(self, points=[], filename=None):
        if not points:
            raise RuntimeError('No points')

        gpx = gpxpy.gpx.GPX()

        # Create first track in our GPX:
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        # Create points:
        for geoPoint in points:
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
                latitude=geoPoint.Latitude,
                longitude=geoPoint.Longitude,
                elevation=geoPoint.Altitude,
                time=geoPoint.GetDatetime(),
            ))

        log.info('Writing {} points to {}'.format(len(points), filename))
        with open(filename, 'w') as f:
            f.write(gpx.to_xml())


def downloadStrava(args):
    strava = Strava(secrets.Get('StravaBearer'))
    trackId = args.track_id
    strava.FormPage('data/tracks/{}_2.geojson'.format(trackId), trackId)


def downloadWantr(args):
    wantr = Wantr()
    wantr.Save(args.output, args.username)


def walkFiles(dirname, extensions=[], dirsOnly=False):
    log.debug('Looking for {} of types {} in {}'.format('dirs' if dirsOnly else 'files', extensions, dirname))
    for root, dirs, files in os.walk(str(dirname)):
        if dirsOnly:
            for directory in dirs:
                yield os.path.join(root, directory)
        else:
            for filename in files:
                if not extensions or any(filename.endswith(extension) for extension in extensions):
                    yield os.path.join(root, filename)


def convertPost(args):
    converter = Converter()
    for filename in walkFiles('_posts'):
        post = converter.Load(filename)
        resultFile = os.path.join('tmp', os.path.basename(filename))
        savePrettyJson(resultFile, post)


def joinTracks(dirname, resultFile):
    fitParser = FitParser()
    geoPoints = []
    for filename in walkFiles(dirname, ['.FIT']):
        geoPoints.extend(list(fitParser(filename)))

    if geoPoints:
        gpxWriter = GpxWriter()
        gpxWriter(points=geoPoints, filename=resultFile)
    else:
        log.warn('No valid FIT files in {}'.format(dirname))


def parseFit(args):
    tracksDir = secrets.Get('TracksDir')
    for dirname in DefaultConfig['GpxFolders']:
        assert os.path.basename(dirname) == dirname
        resultFile = os.path.join(tracksDir, dirname, '{}-joined.gpx'.format(dirname))
        if args.force or not os.path.exists(resultFile):
            joinTracks(os.path.join(tracksDir, dirname), resultFile)
        else:
            log.info('Skipping {}: result exists'.format(dirname))


def CreateArgumentsParser():
    parser = argparse.ArgumentParser(
        description='Form GeoJson file from one album with subalbums.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--debug', help='Enable debug logging', action='store_true')
    parser.add_argument('--secrets', help='Secrets json', default='secrets.json')
    parser.add_argument('--log-format', help='Custom logging format', default='%(asctime)s [%(levelname)s] %(message)s')
    parser.add_argument('--dir', help='Dir name to store results', default='static')
    subparsers = parser.add_subparsers()

    photoParser = subparsers.add_parser('geojson', help='Download photos locations')
    photoParser.set_defaults(func=downloadPhotos)

    stravaParser = subparsers.add_parser('strava', help='Download strava track', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    stravaParser.add_argument('--track-id', default='160251932', help='track id', type=int)
    stravaParser.set_defaults(func=downloadStrava)

    wantrParser = subparsers.add_parser('wantr', help='Download wantr wishlist', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    wantrParser.add_argument('--username', help='username', default='burmisha')
    wantrParser.add_argument('--output', help='output file', default='wishlist/index.html')
    wantrParser.set_defaults(func=downloadWantr)

    convertParser = subparsers.add_parser('convert', help='Convert old post to new one', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    convertParser.add_argument('--input', help='input yaml file', default='_posts/2011-08-15-tartu.html')
    convertParser.add_argument('--output', help='result file', default='tmp.yaml')
    convertParser.set_defaults(func=convertPost)

    parseFitParser = subparsers.add_parser('parse-fit', help='Parse fit files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parseFitParser.add_argument('--force', help='Force generation for existing files', action='store_true')
    parseFitParser.set_defaults(func=parseFit)

    return parser


if __name__ == '__main__':
    parser = CreateArgumentsParser()
    args = parser.parse_args()
    logging.basicConfig(format=args.log_format)
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)
    log.info('Start')
    secrets.Init(args.secrets)
    args.func(args)
    log.info('Finish')
