#!/usr/bin/python
# -*- coding: utf8 -*-

import simplejson as j

map_file_name = 'mapch.json'
new_map = {}

with open('ch_dump', 'rb') as f:
  dump = j.load(f)

with open(map_file_name, 'rb') as f:
  mapch = j.load(f)

for d in dump:
  _id = d['epg_name']
  if _id not in list(mapch.keys()):
    print('add key: %s' % (_id))
    mapch[_id] = {
                              'title': d['title'],
                              'id': '',
                              'logo': '',
                            }
  elif mapch[_id]['title'] != d['title']:
    print('%s diff: %s --> %s' % (_id, d['title'], mapch[_id]['title']))

  new_map[_id] = mapch[_id]

with open(map_file_name, 'wb') as f:
  f.write(j.dumps(new_map, indent=2, sort_keys=True, ensure_ascii=False, encoding='utf-8').encode('utf-8'))
