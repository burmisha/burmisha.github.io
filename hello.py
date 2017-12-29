#!/usr/bin/env python
import argparse
import flask

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


def CreateArgumentsParser():
    parser = argparse.ArgumentParser(
        description='Form GeoJson file from one album with subalbums.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--local', help='Enable local mode (for debug)', action='store_true')
    parser.add_argument('--debug', help='Enable debug mode', action='store_true')
    parser.add_argument('--log-format', help='Custom logging format', default='%(asctime)s [%(levelname)s] %(message)s')
    return parser


if __name__ == '__main__':
    parser = CreateArgumentsParser()
    args = parser.parse_args()
    logging.basicConfig(format=args.log_format)
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)
    log.info('Start')
    if args.local:
        log.info('Running in local mode')
        port = 8080
        debug = True
        mapRenderer.SetFormat('/static/{}')
    else:
        port = None
        debug = None
    app.run(port=port, debug=debug)
    log.info('Finish')


