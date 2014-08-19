#!/usr/bin/env bash
set -xue -o pipefail -o posix
export PATH=$PATH:/c/Users/burmisha/AppData/Roaming/npm
# ./form_geojson.py 
# cp uk.geojson ~/Dropbox/Photo/2013/2013.08\ London/
lessc css/colortheme.less.css css/colortheme.css
bundle exec jekyll serve

