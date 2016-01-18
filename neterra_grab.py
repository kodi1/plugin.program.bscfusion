#!/usr/bin/python
# -*- coding: utf8 -*-

import os, sys, time
import simplejson as json
import requests
import io
import datetime
import itertools

EPG_BASE_URL    = 'http://www.neterra.tv/content/tv_guide'
EPG_LEN         = 6
EPG_OFFSET      = '+0200'

__resource__ = os.path.join(  os.getcwd(), 'resources', 'lib' )
sys.path.insert(0, __resource__)
import xmltv

def get_day(idx):
    r = requests.get('%s/%d' % (EPG_BASE_URL, idx,))
    if r.status_code == requests.codes.ok:
        with io.open(os.path.join(os.getcwd(), '', 'src_%d.dump' % idx), 'w+') as f:
          f.write(unicode(json.dumps(r.json(),
                  sort_keys = True,
                  indent = 1,
                  ensure_ascii=False)))
        return r.json()
    else:
        print 'Status code %s' % (r.status_code, )
        return None

def fill_xml(json_epg):
    for id in json_epg['media']:
        json_epg['media'][id]['epg'] = [g.next() for k,g in itertools.groupby(json_epg['media'][id]['epg'], lambda x: x['start_time_unix'])]
        w.addChannel(
            {'display-name': [(json_epg['media'][id]['media_name'], u'bg')],
            #'icon': [{'src': 'TODO'}],
            'id': json_epg['media'][id]['media_file_tag'],
            'url': [EPG_BASE_URL]}
            )

    for id in json_epg['media']:
        for ent in json_epg['media'][id]['epg']:
            p = {}
            p['start'] = '%s %s' % (datetime.datetime.fromtimestamp(float(ent['start_time_unix'])).strftime('%Y%m%d%H%M%S'), EPG_OFFSET)
            p['stop'] = '%s %s' % (datetime.datetime.fromtimestamp(float(ent['end_time_unix'])).strftime('%Y%m%d%H%M%S'), EPG_OFFSET)
            p['title'] = [(ent['epg_prod_name'], u'')]
            p['channel'] =  json_epg['media'][id]['media_file_tag']

            if ent['description']:
                p['desc'] = [(ent['description'], u'')]

            w.addProgramme(p)

if __name__ == '__main__':
  json_epg = None
  w = xmltv.Writer(encoding='UTF-8',
          date=str(time.time()),
          source_info_url=EPG_BASE_URL,
          source_info_name="",
          generator_info_name=os.path.basename(__file__),
          generator_info_url="")

  for idx in range(0, EPG_LEN):
      r = get_day(idx)
      if not json_epg:
          json_epg = r
      else:
          for id in r['media']:
              json_epg['media'][id]['epg'].extend(r['media'][id]['epg'])

  fill_xml(json_epg)
  out = open(os.path.join(os.getcwd(), '', 'neterra.xml'), 'wb+')
  w.write(out, pretty_print=True)
  out.close()
