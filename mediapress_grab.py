#!/usr/bin/python
# -*- coding: utf8 -*-

import os, sys
import requests
import time
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup as bs
from operator import itemgetter
import re

EPG_BASE_URL    = 'http://epg-bg.media-press.tv'
EPG_LEN         = 5
EPG_OFFSET      = '+0100'
CH_PACK         = [1, 4] #[1, 2, 3, 4, 5]
UA              = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0'}

__resource__ = os.path.join(  os.getcwd(), 'resources', 'lib' )
sys.path.insert(0, __resource__)
import xmltv

def log_info (s, a=None):
  if a == 0:
    b = '\033[94m'      #blue
    e = '\033[0m'
  elif a == 1:
    b = '\033[92m'      #green
    e = '\033[0m'
  elif a == 2:
    b = '\033[93m'      #yellow
    e = '\033[0m'
  elif a == 3:
    b = '\033[91m'      #red
    e = '\033[0m'
  else:
    b = ''
    e = ''
  print b + s + e

def get_ev_from_day(d, p):
  url = '%s/%s?group=%d' % (EPG_BASE_URL, d.strftime('%m-%d-%Y'), p, )
  r = requests.get(url, headers= UA)
  if r.status_code == requests.codes.ok:
    #pg = bs(r.text, 'lxml')
    pg = bs(r.text).find('div', id='gridBody')
    for ch in pg.findAll('a', href= re.compile(r'(\/event\/\d+\/.*\/)')):
      ev_url = '%s%s' % (EPG_BASE_URL, ch['href'],)
      yield ev_url

def get_ev_info(url, date):
  ch = {}
  prog = {}
  cred = {}
  ep = None

  print url
  r = requests.get(url, headers= UA)
  if r.status_code == requests.codes.ok:
    #ii = bs(r.text, 'lxml').findAll('div', id= re.compile(r'((?:left|right)Column)'))
    ii = bs(r.text).findAll('div', id= re.compile(r'((?:left|right)Column)'))

    #log_info(ii[0].prettify(), 1)
    #log_info(ii[1].prettify(), 2)

    c = ii[0].h1.find_next_siblings()
    m = re.match(r'.*?(\d{2}:\d{2}).*?(\d{2}:\d{2})', c[0].get_text(), re.DOTALL)

    tmp = m.group(1).split(':')
    ds = date.replace(hour= int(tmp[0]), minute= int(tmp[1]), second= 0)
    prog['start'] = '%s %s' % (ds.strftime('%Y%m%d%H%M%S'), EPG_OFFSET)

    tmp = m.group(2).split(':')
    de = date.replace(hour= int(tmp[0]), minute= int(tmp[1]), second= 0)
    if ds > de:
      de += timedelta(days=1)
    prog['stop'] = '%s %s' % (de.strftime('%Y%m%d%H%M%S'), EPG_OFFSET)

    id = c[1].get_text(strip=True)
    for rm in ['.', '(', ')']:
      id = id.replace(rm, '')
    ch['id'] = id.lower().replace (' ', '_')
    ch['display-name'] = [(id, u'bg')]
    ch['url'] = [EPG_BASE_URL]

    fsk = c[3].div.get_text(strip=True).split(' ')
    if len(fsk) == 2:
      prog['rating'] = [{'system': fsk[0], 'value': fsk[1]}]

    for d in c[5].findAll('dl'):
      _dt = d.dt.get_text().lower().encode('utf-8')
      for _d in d.dd.get_text('|', strip=True).split('|'):
        if 'загл' in _dt:
          prog['sub-title'] = [(_d, u'')]
        elif 'год' in _dt:
          prog['date'] = _d
        elif 'реж' in _dt:
          if 'director' in cred:
            cred['director'].append(_d)
          else:
            cred['director'] = [_d]
        elif 'сцен' in _dt:
          if 'writer' in cred:
            cred['writer'].append(_d)
          else:
            cred['writer'] = [_d]
        elif 'епизод' in _dt:
          ep = [('.%s.' % (_d,), 'xmltv_ns')]
        elif 'mode' in _dt:
          if 'presenter' in cred:
            cred['presenter'].append(_d)
          else:
            cred['presenter'] = [_d]
        elif 'муз' in _dt:
          if 'composer' in cred:
            cred['composer'].append(_d)
          else:
            cred['composer'] = [_d]
        else:
          log_info(d.prettify(), 1)

    ddd = c[4].get_text(strip=True)
    if ddd:
      prog['desc'] = [(ddd, u'')]

    ot = c[2].div.get_text(strip=True)
    if ot:
      prog['category'] = [(ot, u'')]

    prog['url'] = [url]
    prog['channel'] = ch['id']

    inf = ii[1].img
    if inf:
      if not inf['src'].startswith('http'):
        inf['src'] = '%s%s' % (EPG_BASE_URL, inf['src'],)
      prog['icon'] = [{'src': inf['src']}]

    for m in ii[1].findAll('dl'):
      _dt = m.dt.get_text().lower().encode('utf-8')
      if 'акт' in _dt:
        for a in m.findAll('dd'):
          d = a.get_text(strip=True)
          if 'actor' in cred:
            cred['actor'].append(d)
          else:
            cred['actor'] = [d]
      elif 'гост' in _dt:
        for a in m.findAll('dd'):
          d = a.get_text(', ', strip=True)
          if 'guest' in cred:
            cred['guest'].append(d)
          else:
            cred['guest'] = [d]
      elif 'тем' in _dt:
        for a in m.findAll('dd'):
          for d in a.get_text('|', strip=True).split('|'):
            if 'sub-title' in prog:
              prog['sub-title'].append((d, u''))
            else:
              prog['sub-title'] = [(d, u'')]
      else:
        log_info(m.prettify(), 0)

  title = ii[0].h1.get_text(strip=True).encode('utf-8')
  if ep:
    prog['episode-num'] = ep
  else:
    s_ep = re.split(r'\(еп(.*)\)', title)
    if len(s_ep) > 1:
      ep = []
      title = s_ep[0]
      for e in s_ep[1].split(','):
        ep.append(('.%s.' % (e.strip(),), 'xmltv_ns'))
      prog['episode-num'] = ep

  prog['title'] = [(title.decode('utf-8').strip(), u'')]
  ret = {'prog': prog, 'ch': ch}
  if cred:
    ret['prog']['credits'] = cred
  return ret

if __name__ == '__main__':
  #if True:
    #url = 'http://epg-bg.media-press.tv/event/4976269/BBOA/'
    #print get_ev_info(url, datetime.now())
    #sys.exit(0)
  data = {}
  now = datetime.now()
  w = xmltv.Writer(encoding='UTF-8',
        date=str(time.time()),
        source_info_url=EPG_BASE_URL,
        source_info_name='',
        generator_info_name=os.path.basename(__file__),
        generator_info_url='')

  for idx in range(0, EPG_LEN):
    date = now + timedelta(days=idx)
    for pack in CH_PACK:
      for ev_url in get_ev_from_day(date, pack):
        ev = get_ev_info(ev_url, date)
        if ev['ch']['id'] not in data:
          data.setdefault(ev['ch']['id'], {'prog': ev['ch'], 'data': [ev['prog']]})
        else:
          data[ev['ch']['id']]['data'].extend([ev['prog']])
        #break
      #break
    #break

  for k in  data.keys():
    data[k]['data'] = sorted(data[k]['data'], key=itemgetter('start'))
    w.addChannel(data[k]['prog'])

  for k in  data.keys():
    for c in data[k]['data']:
      w.addProgramme(c)

  out = open(os.path.join(os.getcwd(), '', 'media_press.xml'), 'wb+')
  w.write(out, pretty_print=True)
  out.close()
