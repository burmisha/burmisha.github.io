#!/bin/bash
set -x 
lessc style/style.less.css style/style.css
bundle exec jekyll serve

