#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import requests
import yaml

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Form nice yaml for wishlist at wantr of a given user")
	parser.add_argument("-u", "--user", dest='user', default="burmisha", help="username, default: %(default)s")
	parser.add_argument("-o", "--output", dest='output', default="wishlist/index.html", help="output file, default: %(default)s")
	args = parser.parse_args()
	u  = requests.get('http://api.wantr.ru/0.1/user/%(user)s' % {'user': args.user}).json()
	w  = requests.get('http://api.wantr.ru/0.1/wishlist/%(uid)s' % {'uid': u["id"]}).json()
	y = {'wishes':[]}

	for t in w['wishes']:
		items = []
		for wish in w['wishes'][t]['content']:
			items.append(w['wishes'][t]['content'][wish])
		y['wishes'].append({'name'  : w['wishes'][t]['name'], 
							'items' : items})

	with open(args.output, 'w') as yaml_file:
		yaml_file.write("""---
layout: default
title: Wishlist
""")
		yaml_file.write(yaml.safe_dump(y, allow_unicode=True, default_flow_style=False))
		yaml_file.write("""---
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
Это иногда обновляемая копия моего wishlist'а 
на <a href=http://wantr.ru/burmisha>Wantrе</a>, 
который, в свою очередь, является копей странички 
<a href=http://mywishlist.ru/wishlist/burmisha>mywishlist</a>. 
</p>
""")
