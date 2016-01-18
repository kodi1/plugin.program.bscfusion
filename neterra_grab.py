#!/usr/bin/python
# -*- coding: utf8 -*-

import os, sys, time
import simplejson as json
import requests
import io
import datetime
import itertools

EPG_BASE_URL    = 'http://www.neterra.tv/content/tv_guide'
EPG_LEN         = 5
EPG_OFFSET      = '+0200'

__resource__ = os.path.join(  os.getcwd(), 'resources', 'lib' )
sys.path.insert(0, __resource__)
import xmltv

r = requests.get('%s/%d' % (EPG_BASE_URL, EPG_LEN,))
if r.status_code == requests.codes.ok:
  json_epg = r.json()
  with io.open(os.path.join(os.getcwd(), '', 'src.dump'), 'w+') as f:
    f.write(unicode(json.dumps(json_epg,
                    sort_keys = True,
                    indent = 1,
                    ensure_ascii=False)))

  w = xmltv.Writer(encoding='UTF-8',
                  date=str(time.time()),
                  source_info_url="",
                  source_info_name="",
                  generator_info_name="",
                  generator_info_url="")

  for id in json_epg['media']:
        json_epg['media'][id]['epg'] = [g.next() for k,g in itertools.groupby(json_epg['media'][id]['epg'], lambda x: x['start_time_unix'])]
    w.addChannel(
            {'display-name': [(json_epg['media'][id]['media_name'], u'bg')],
            'icon': [{'src': 'TODO'}],
            'id': json_epg['media'][id]['media_file_tag'],
            'url': [EPG_BASE_URL]}
            )
    for ent in json_epg['media'][id]['epg']:
      desc = ent['description']
      if not desc:
        desc = 'None'

      start_t = '%s %s' % (datetime.datetime.fromtimestamp(float(ent['start_time_unix'])).strftime('%Y%m%d%H%M%S'), EPG_OFFSET)
      end_t = '%s %s' % (datetime.datetime.fromtimestamp(float(ent['end_time_unix'])).strftime('%Y%m%d%H%M%S'), EPG_OFFSET)

      w.addProgramme(
              {'start': start_t,
              'stop': end_t,
              'title': [(ent['epg_prod_name'], u'')],
              'desc': [(desc, u'')],
              'channel': json_epg['media'][id]['media_file_tag'],
              }
            )

  out = open(os.path.join(os.getcwd(), '', 'neterra.xml'), 'wb+')
  w.write(out, pretty_print=True)
  out.close()

else:
  print 'Status code %s' % (r.status_code, )
