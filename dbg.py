#!/usr/bin/python
# -*- coding: utf8 -*-

import os, sys, json
import datetime, time
from datetime import datetime, timedelta

offset = 0.0

__resource__ = os.path.join(  os.getcwd(), 'resources', 'lib' )
sys.path.insert(0, __resource__)

usr, psw = os.getenv('BSCLOGIN', 'user:pass').split(':')

def mk_info_string (e):
  s =  u'T: %s' % timesmk(e)
  if e['title']:
    s += u' title: %s' % e['title']
  if e['desc']:
    s += u' desc: %s' % e['desc']
  s += '[CR]'
  return s

def timesmk(v):
  ts = v.get('start', None)
  te = v.get('stop', None)
  if ts is None or te is None:
    return u''
  ts = datetime.fromtimestamp(time.mktime(time.strptime(ts.split()[0], '%Y%m%d%H%M%S'))) + timedelta(minutes=offset)
  te = datetime.fromtimestamp(time.mktime(time.strptime(te.split()[0], '%Y%m%d%H%M%S'))) + timedelta(minutes=offset)
  return u'%s %s' % (ts.strftime("%H:%M:%S"), te.strftime("%H:%M:%S"))

def get_prog_info(ch):
  s = u''
  pr = ch.get('program', None)
  if pr:
    if isinstance(pr, list):
        for entry in pr:
          s += mk_info_string(entry)
        s += '[CR]'
    elif isinstance(pr, dict):
      s += mk_info_string(pr)

  s += u'[COLOR 3300FF00]'
  if ch['channel']:
    s += u'[CR]channel: %s' % ch['channel']
  if ch.has_key('audio') and ch['audio']:
    s += u'[CR]audio: %s' % ch['audio']
  if ch['quality']:
    s += u'[CR]quality: %s' % ch['quality']
  s += u'[/COLOR]'
  return s

def clear_if_ver(path, app_ver):
  if os.path.exists(path):
    with open(p, 'r') as f:
      js = json.load(f)
    if not (js.has_key('app_version') and js['app_version'] == app_ver):
      for root, dirs, files in os.walk(os.path.dirname(p), topdown=False):
        for name in files:
          os.remove(os.path.join(root, name))
        for name in dirs:
          os.rmdir(os.path.join(root, name))

def progress_cb (a):
  print 'Cb: %s -> %s' % (a['str'], a['pr'])

if __name__ == '__main__':
  import bsc
  start_time = time.time()
  p = os.path.join(os.getcwd(), 'tmp', 'data.dat')
  v = '0.0.0'

  print usr, psw, p, v
  clear_if_ver(p, v)
  b = bsc.dodat(base = 'https://api.iptv.bulsat.com',
                login = {'usr': usr,'pass': psw},
                cachepath = p,
                cachetime = 60,
                dbg = True,
                timeout = 10,
                ver = v,
                proc_cb = progress_cb,
                )

  for g in b.get_genres():
    print '---------- %s ----------' % g.encode('utf-8', 'replace')
    for ch in b.get_all_by_genre(g):
      info = get_prog_info(ch)
      print ('Name: %s Quality: %s Info: %s' % (ch['title'], ch['quality'], ' '.join(info.split()))).encode('utf-8', 'replace')

  print("--- %s seconds ---" % (time.time() - start_time))
