#!/bin/bash
set -x 
lessc css/colortheme.less.css css/colortheme.css
bundle exec jekyll serve

