#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import os
import requests
import pprint
import yaml
import datetime

# https://stuvel.eu/flickrapi
import flickrapi

import logging
log = logging.getLogger('backend')


class Secrets(object):
    def Init(self, filename):
        log.info('Loading secrets from %r', filename)
        with open(filename) as f:
            self.Data = json.load(f)

    def Get(self, secretKey):
        return self.Data[secretKey]


secrets = Secrets()


def savePrettyJson(filename, data, force=True):
    if not isinstance(filename, (str, unicode)):
        raise RuntimeError('Invalid filename: {!r}'.format(filename))
    else:
        log.info('Saving to %r', filename)

    if os.path.exists(filename):
        if force:
            log.warn('Overwriting %r', filename)
        else:
            raise RuntimeError('File {!r} already exists')

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
        self.AlbumTitle = None

    def SetTitle(self, title):
        self.Title = title

    def SetAlbumTitle(self, albumTitle):
        self.AlbumTitle = albumTitle

    def SetUrls(self, smallSquare=None, medium=None, original=None):
        self.SmallSquareUrl = smallSquare
        self.MediumUrl = medium
        self.OriginalUrl = original

    def SetCoordinates(self, coordinates={}, longitude=None, latitude=None):
        self.Latitude = coordinates.get('latitude', latitude)
        self.Longitude = coordinates.get('longitude', longitude)
        self.HasGeo = self.Latitude is not None and self.Longitude is not None

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
        if self.AlbumTitle:
            result['AlbumTitle'] = self.AlbumTitle
        return result

    @staticmethod
    def FromDict(data):
        photo = Photo()
        photo.SetUrls(
            smallSquare=data['SmallSquareUrl'],
            medium=data['MediumUrl'],
            original=data['OriginalUrl'],
        )
        if data.get('AlbumTitle'):
            photo.SetAlbumTitle(data['AlbumTitle'])
        if data.get('title'):
            photo.SetTitle(data['title'])
        if data.get('HasGeo'):
            photo.SetCoordinates(longitude=data['Longitude'], latitude=data['Latitude'])
        return photo


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
            albumPath = albumInfo['links']['self']
        else:
            albumPath = url

        albumPath = albumPath.split('?', 1)[0] + 'photos/?format=json'
        log.info('Getting photos from %r', albumPath)

        index = -1
        for index, photoItem in enumerate(self.GetPhotosFromAlbumImpl(albumPath)):
            photo = Photo()
            result = {}
            for item, letter in [
                ('smallSquare', 'S'),
                ('medium', 'M'),
                ('original', 'orig'),
            ]:
                if letter in photoItem['img']:
                    result[item] = photoItem['img'][letter]['href']
                else:
                    result[item] = None
            photo.SetUrls(**result)
            photo.SetTitle(photoItem['title'])
            if 'geo' in photoItem:
                latitude, longitude = photoItem['geo']['coordinates'].split(' ')
                photo.SetCoordinates(
                    longitude=float(longitude),
                    latitude=float(latitude)
                )
            yield photo

        log.info('Got %d photos from %r', index + 1, albumPath)

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
        log.info('Flickr nsid: %s', self.Nsid)

    def GetAlbums(self):
        albums = self.FlickrAPI.photosets.getList(user_id=self.Nsid)
        albums = albums['photosets']['photoset']
        log.info('Got %d albums:', len(albums))
        for album in albums:
            albumTitle = album['title']['_content']
            log.info('  id: %s, title: %s (%r), photos: %d', album['id'], albumTitle, albumTitle, album['photos'])
        return albums

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
        while not ok and count <= 5:
            try:
                data = self.FlickrAPI.photos.geo.getLocation(photo_id=photoId)
                ok = True
            except flickrapi.exceptions.FlickrError as e:
                if str(e) == 'Error: 2: Photo has no location information.':
                    log.info('    Photo %s has no location information', photoId)
                    ok = True
                    return None
                else:
                    log.exception('FlickrError')
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
        log.info('Yielding %d photos from album %s', r['photoset']['total'], photosetId)
        for index, photoItem in enumerate(r['photoset']['photo']):
            photoId = photoItem['id']
            log.debug('  Getting photo %s (%-3d of %3d)', photoId, index + 1, r['photoset']['total'])
            photo = Photo()
            sizes = self.GetSizes(photoId, ['Large Square', 'Medium', 'Original'])
            photo.SetTitle(self.FlickrAPI.photos.getInfo(photo_id=photoId)['photo']['title']['_content'])
            photo.SetUrls(
                smallSquare=sizes['Large Square'],
                medium=sizes['Medium'],
                original=sizes['Original'],
            )
            location = self.GetLocation(photoId)
            if location:
                photo.SetCoordinates(location)
            yield photo
        log.info('Yielded %d photos from album %s', index + 1, r['photoset']['total'])


class PhotosDatabase(object):
    def __init__(self, yandexFotki=None, flickr=None):
        self.YandexFotki = yandexFotki
        self.Flickr = flickr
        self.Photos = []

    def Load(self, filename):
        with open(f) as f:
            self.Photos = json.load(f)

    # def Save(self, filename, force=False):
    def Save(self, filename, force=True):
        data = [photo.ToDict() for photo in self.Photos]
        savePrettyJson(filename, data, force=force)

    def GetAllPhotos(self):
        if self.YandexFotki:
            for albumInfo in self.YandexFotki.GetAlbumsInfo():
                albumUrl = albumInfo['links']['self']
                for photo in self.YandexFotki.GetPhotosFromAlbum(url=albumUrl):
                    photo.SetAlbumTitle(albumInfo['title'])
                    yield photo

        if self.Flickr:
            albums = self.Flickr.GetAlbums()
            for album in albums:
                albumId = album['id']
                for photo in self.Flickr.GetPhotos(albumId):
                    photo.SetAlbumTitle(album['title']['_content'])
                    yield photo

    def __call__(self):
        self.Photos = list(self.GetAllPhotos())


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
        '2018-04-Gent',
        '2018-12 Poland'
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


def downloadGeoJson(args):
    filename = Filename(args.dir)
    geoJson = GeoJson()
    for photos, basename in findAllPhotos():
        geoJson.FormAndSave(photos, filename(basename))


def downloadPhotos(args):
    photosDatabase = PhotosDatabase(
        yandexFotki=YandexFotki(DefaultConfig['YandexFotkiUser']),
        flickr=Flickr(DefaultConfig['FlickrUser']),
    )
    photosDatabase()
    photosDatabase.Save(args.filename)


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



def downloadStrava(args):
    strava = Strava(secrets.Get('StravaBearer'))
    for trackId in args.track_id:
        strava.FormPage('data/tracks/{}_2.geojson'.format(trackId), trackId)


def downloadWantr(args):
    wantr = Wantr()
    wantr.Save(args.output, args.username)


def walkFiles(dirname, extensions=[], dirsOnly=False):
    logName = 'dirs' if dirsOnly else 'files'
    log.info('Looking for {} of types {} in {}'.format(logName, extensions, dirname))
    count = 0
    for root, dirs, files in os.walk(str(dirname)):
        if dirsOnly:
            for directory in dirs:
                count += 1
                yield os.path.join(root, directory)
        else:
            for filename in files:
                if not extensions or any(filename.endswith(extension) for extension in extensions):
                    count += 1
                    yield os.path.join(root, filename)
    log.info('Found {} {} in {}'.format(count, logName, dirname))



def convertPost(args):
    converter = Converter()
    srcDir = args.src_dir
    dstDir = args.dst_dir
    for filename in walkFiles(srcDir):
        post = converter.Load(filename)
        resultFile = os.path.join(dstDir, os.path.basename(filename).split('.')[0] + '.json')
        savePrettyJson(resultFile, post)


def CreateArgumentsParser():
    fmtClass = {'formatter_class': argparse.ArgumentDefaultsHelpFormatter}
    parser = argparse.ArgumentParser(description='Form GeoJson file from one album with subalbums.', **fmtClass)
    parser.add_argument('--secrets', help='Secrets json', default='secrets.json')
    parser.add_argument('--dir', help='Dir name to store results', default='static')

    loggingGroup = parser.add_argument_group('Logging arguments')
    loggingGroup.add_argument('--log-format', help='Logging str', default='%(asctime)s.%(msecs)03d %(name)10s:%(lineno)-3d %(levelname)-7s %(message)s')
    # loggingGroup.add_argument('--log-format', help='Logging str', default='%(relativeCreated)d %(name)15s:%(lineno)-3d %(levelname)-7s %(message)s')
    loggingGroup.add_argument('--log-separator', help='Logging string separator', choices=['space', 'tab'], default='space')
    loggingGroup.add_argument('--verbose', help='Enable debug logging', action='store_true')

    subparsers = parser.add_subparsers()

    photoParser = subparsers.add_parser('geojson', help='Download photos locations')
    photoParser.set_defaults(func=downloadGeoJson)

    photosParser = subparsers.add_parser('photos', help='Download all photos info', **fmtClass)
    photosParser.add_argument('--filename', help='File to save to', default='tmp.json')
    photosParser.set_defaults(func=downloadPhotos)

    stravaParser = subparsers.add_parser('strava', help='Download strava track', **fmtClass)
    stravaParser.add_argument('--track-id', default=[160251932], help='track id', type=int, action='append')
    stravaParser.set_defaults(func=downloadStrava)

    wantrParser = subparsers.add_parser('wantr', help='Download wantr wishlist', **fmtClass)
    wantrParser.add_argument('--username', help='username', default='burmisha')
    wantrParser.add_argument('--output', help='output file', default='wishlist/index.html')
    wantrParser.set_defaults(func=downloadWantr)

    convertParser = subparsers.add_parser('convert', help='Convert old post to new one', **fmtClass)
    # convertParser.add_argument('--input', help='input yaml file', default='_posts/2011-08-15-tartu.html')
    # convertParser.add_argument('--output', help='result file', default='tmp.yaml')
    convertParser.add_argument('--src-dir', help='input', default='_posts')
    convertParser.add_argument('--dst-dir', help='results', default='tmp')
    convertParser.set_defaults(func=convertPost)

    return parser


if __name__ == '__main__':
    parser = CreateArgumentsParser()
    args = parser.parse_args()

    logFormat = args.log_format.replace('\t', ' ')
    logFormat = logFormat.replace(' ', {'space': ' ', 'tab': '\t'}[args.log_separator])
    logLevel = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=logLevel, format=logFormat,
        datefmt='%H:%M:%S'
    )

    for logName, logLevel in [
        ('urllib3.connectionpool', logging.WARN),
        ('flickrapi.core', logging.WARN),
        ('requests_oauthlib.oauth1_auth', logging.WARN),
        ('oauthlib.oauth1.rfc5849', logging.WARN),
    ]:
        logging.getLogger(logName).setLevel(logLevel)

    log.info('Start')
    secrets.Init(args.secrets)
    args.func(args)
    log.info('Finish')
