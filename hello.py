#!/usr/bin/env python
import argparse
import flask
import json
import re
import os

import logging
log = logging.getLogger(__file__)

app = flask.Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/user/<string:username>')
def user(username, methods=['GET']):
    return 'Hello, {}!'.format(username)


class MapRenderer():
    def __init__(self):
        self.Format = 'http://beta.burmisha.com/static/{}'

    def SetFormat(self, fmt):
        self.Format = fmt

    def __call__(self, mapName):
        scales = {
            'uk.geojson': 7,
            'tur.geojson': 14,
            'germany14-1.geojson': 16,
        }
        return flask.render_template(
            'map.html',
            geojson=self.Format.format(mapName),
            scale=scales[mapName],
        )


mapRenderer = MapRenderer()


@app.route('/db/map')
def DbMap():
    return mapRenderer('uk.geojson')


@app.route('/istanbul/map')
def IstanbulMap():
    return mapRenderer('tur.geojson')


@app.route('/2014/1')
def Germany():
    return mapRenderer('germany14-1.geojson')


class PostLoader(object):
    def __init__(self, filename):
        log.debug('Loading post from %r', filename)
        with open(filename) as f:
            self.Data = json.load(f)
        self.Items = []
        self.AllPhotos = set()
        self.CaptionIsUsed = [False for _ in self.Data['captions']]

    def TryToAddCaption(self, newPhotos=set()):
        for i, (text, photos, isText) in enumerate(self.Data['captions']):
            if not self.CaptionIsUsed[i]:
                item = None
                if isText:
                    log.debug('Text should go before new photos')
                    if all(photo in self.AllPhotos | newPhotos for photo in photos):
                        item = {'text': text}
                else:
                    if all(photo in self.AllPhotos for photo in photos):
                        item = {'caption': text}
                if item:
                    self.CaptionIsUsed[i] = True
                    self.Items.append(item)

    def __call__(self):
        for titles in self.Data['series']:
            photos = []
            newPhotos = set()
            for title in titles:
                photos.append({'url': self.Data['photos'][title]['OriginalUrl'], 'title': title})
                newPhotos.add(title)

            self.TryToAddCaption(newPhotos)
            self.AllPhotos = self.AllPhotos | newPhotos
            if len(photos) == 1:
                item = { 'photo': photos[0] }
            else:
                item = { 'photos': photos }
            self.Items.append(item)
            self.TryToAddCaption()

        return {
            'title': self.Data['title'],
            'series': self.Items,
        }



@app.route('/post/<path:postId>')
def Post(postId):
    try:
        postRe = '^\d{2}(\d{2}/){3}[-\w]+(\.html)?$'
        if not re.match(postRe, postId):
            raise RuntimeError('Invalid post id: {!r}'.format(postId))
        postLoader = PostLoader(os.path.join('tmp', postId.replace('/', '-')))
        return flask.render_template(
            'base.html',
            page=postLoader(),
        )
    except Exception as e:
        log.exception('Error on %r', postId)
        return flask.render_template(
            'error.html',
            message=str(e),
        )


def CreateArgumentsParser():
    parser = argparse.ArgumentParser(
        description='Form GeoJson file from one album with subalbums.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--local', help='Enable local mode (for debug)', action='store_true')

    loggingGroup = parser.add_argument_group('Logging arguments')
    loggingGroup.add_argument('--log-format', help='Logging str', default='%(asctime)s %(name)15s:%(lineno)3d [%(levelname)s] %(message)s')
    loggingGroup.add_argument('--log-separator', help='Logging string separator', choices=['space', 'tab'], default='space')
    loggingGroup.add_argument('--verbose', help='Enable debug logging', action='store_true')

    return parser


def main(args):
    if args.local:
        port = 8080
        debug = True
        mapRenderer.SetFormat('/static/{}')
        log.info('Running in local mode: http://localhost:%d/', port)
    else:
        port = None
        debug = None
    app.run(port=port, debug=debug)


if __name__ == '__main__':
    parser = CreateArgumentsParser()
    args = parser.parse_args()

    logFormat = args.log_format.replace('\t', ' ')
    logFormat = logFormat.replace(' ', {'space': ' ', 'tab': '\t'}[args.log_separator])
    logLevel = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=logLevel, format=logFormat)

    log.info('Start')
    main(args)
    log.info('Finish')
