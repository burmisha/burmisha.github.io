#!/usr/bin/env python

import argparse
import json
import requests

import logging
log = logging.getLogger(__file__)

class YandexFotki(object):
    def __init__(self, username, rootAlbumName=None, prefixes=[]):
        self.Username = username
        self.RootAlbumName = rootAlbumName
        self.Prefixes = prefixes

    def GetAlbumsInfo(self):
        albumsInfo = requests.get(
            'http://api-fotki.yandex.ru/api/users/{}/albums/published/'.format(self.Username),
            params={'format': 'json'}
        ).json()
        return albumsInfo

    def GetPhotosFromAlbum(self, albumPath):
        answer = requests.get(albumPath).json()
        photos = answer['entries']
        if 'next' in answer['links']:
            photos.extend(self.GetPhotosFromAlbum(answer['links']['next']))
        return photos

    def FindAlbumByName(self, albums, albumName):
        for album in albums:
            if album['title'] == albumName:
                log.info('Got album %r', album['title'])
                return album

    def FindAlbumsByRoot(self, albums, rootAlbumPath):
        for album in albums:
            if ('album' in album['links']) and (album['links']['album'] == rootAlbumPath):
                if self.Prefixes:
                    if any(album['title'].startswith(prefix) for prefix in self.Prefixes):
                        yield album
                else:
                    yield album

    def GetPhotosFromAlbums(self, albumsInfo):
        for albumInfo in albumsInfo:
            log.info('Getting photos from %r', albumInfo['title'])
            albumPath = albumInfo['links']['self'].split('?', 1)[0] + 'photos/?format=json'
            for photo in self.GetPhotosFromAlbum(albumPath):
                yield photo


    def FindPhotos(self):
        albumsInfo = self.GetAlbumsInfo()['entries']
        rootAlbumPath = self.FindAlbumByName(albumsInfo, self.RootAlbumName)['links']['self']
        chosenAlbumsInfo = self.FindAlbumsByRoot(albumsInfo, rootAlbumPath)
        for photo in self.GetPhotosFromAlbums(chosenAlbumsInfo):
            yield photo


class GeoJson(object):
    def GetCoordinates(self, photo):
        c = photo['geo']['coordinates'].split(' ')
        return [c[1], c[0]]

    def GeoPoint(self, photo):
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': self.GetCoordinates(photo),
            },
            'properties': {
                'M_url':    photo['img']['M']['href'],
                'S_url':    photo['img']['S']['href'],
                'orig_url': photo['img']['orig']['href'],
            },
        }

    def GetMiddlePoint(self, photos, idx, rejectRate):
        coords = sorted([self.GetCoordinates(p)[idx] for p in photos if 'geo' in p]);
        left = float(coords[int(len(coords) * rejectRate)])
        right = float(coords[int(len(coords) * (1 - rejectRate))])
        return (left + right) / 2

    def Form(self, photos):
        return {
            'type': 'FeatureCollection',
            'view_point': [self.GetMiddlePoint(photos, i, 0.4) for i in [1, 0]],
            'features': [self.GeoPoint(photo) for photo in photos],
        }

    def FormAndSave(self, photos, filename):
        log.info('Saving %d photos to %r', len(photos), filename)
        geojson = self.Form(photos)
        with open(filename, 'w') as f:
            json.dump(geojson, f, indent=4, separators=(',', ': '))


def main(args):
    rootName = args.root_name
    yandexFotki = YandexFotki(args.user, rootAlbumName=rootName, prefixes=args.prefixes)
    photos = list(yandexFotki.FindPhotos())
    geoPhotos = [photo for photo in photos if 'geo' in photo]
    geoJson = GeoJson()
    resultFile = args.geojson
    if not resultFile:
        resultFile = DEFAULTS['RootNames'][rootName]
    geoJson.FormAndSave(geoPhotos, resultFile)


DEFAULTS = {
    'RootNames': {
        '2013 UK':          'uk.geojson',
        '2014.01 Istanbul': 'tur.geojson',
    },
    'AllowedPrefixes': ['July', 'Aug', '2014'],
}

def CreateArgumentsParser():
    parser = argparse.ArgumentParser(
        description='Form GeoJson file from one album with subalbums.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--debug', help='Enable debug logging', action='store_true')
    parser.add_argument('--log-format', help='Custom logging format', default='%(asctime)s [%(levelname)s] %(message)s')
    parser.add_argument('--user', help='Username for Yandex.Fotki', default='i-like-spam')
    parser.add_argument('--root-name', help='Root album name', choices=DEFAULTS['RootNames'], default='2013 UK')
    parser.add_argument('--prefixes', help='Allowed prefixes', default=DEFAULTS['AllowedPrefixes'], action='append')
    parser.add_argument('--geojson', help='Custom output file with geojson')
    return parser


if __name__ == '__main__':
    parser = CreateArgumentsParser()
    args = parser.parse_args()
    logging.basicConfig(format=args.log_format)
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)
    log.info('Start')
    main(args)
    log.info('Finish')
