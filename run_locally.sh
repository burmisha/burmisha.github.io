#!/usr/bin/env bash
set -xue -o pipefail -o posix
export PATH=$PATH:/c/Users/burmisha/AppData/Roaming/npm
# ./form_geojson.py 
# cp uk.geojson ~/Dropbox/Photo/2013/2013.08\ London/
# brew install ruby@3.3
bundle install
bundle exec jekyll serve

