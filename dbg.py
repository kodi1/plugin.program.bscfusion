#!/usr/bin/python
# -*- coding: utf8 -*-

import os, sys, json, re
import datetime, time
from datetime import datetime, timedelta
import requests

offset = 0.0
dbg = True

UA = {
                'Host': 'api.iptv.bulsat.com',
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://test.iptv.bulsat.com/iptv.php',
                'Origin': 'https://test.iptv.bulsat.com',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                }

__resource__ = os.path.join(  os.getcwd(), 'resources', 'lib' )
sys.path.insert(0, __resource__)

usr, psw = os.getenv('BSCLOGIN', 'user:pass').split(':')

def url_update_1(u):
  if re.match(r'^.*smil\:.*\.smil\?scheme=m3u8.*$', u):
    for m in [
              {'re': r'http\:\/\/lb-sf', 'ch': 'http://edge-sf-1'},
              {'re': r'redirect\/', 'ch': ''},
              {'re': r'\/smil\:', 'ch': '/_definst_/smil:'},
              {'re': r'\?.*m3u8\&', 'ch': '/playlist.m3u8?'},
              ]:
      if dbg:
        print m
      u = re.sub(m['re'], m['ch'], u)
  else:
    for m in [
              {'re': r'http\:\/\/lb-sf', 'ch': 'http://edge-sf-1'},
              {'re': r'redirect\/', 'ch': ''},
              {'re': r'\:1935\/(.*?\/)', 'ch':'\g<0>_definst_/'},
              {'re': r'\?.*m3u8\&', 'ch': '/playlist.m3u8?'},
              ]:
      if dbg:
        print m
      u = re.sub(m['re'], m['ch'], u)

  u += '|User-Agent=%s' % (urllib.quote_plus(__ua_os[sys.argv[1]]['ua']))
  return u

def url_update_0(u):
  return u

__ua_os = {
  '0' : {'ua' : 'pcweb', 'osid' : 'pcweb', 'url_up': url_update_0},
  '1' : {'ua' : 'Mozilla/5.0 (SMART-TV; Linux; Tizen 2.3) AppleWebkit/538.1 (KHTML, like Gecko) SamsungBrowser/1.0 TV Safari/538.1', 'osid' : 'samsungtv', 'url_up': url_update_1},
  '2' : {'ua' : 'HLS Client/2.0 (compatible; LG NetCast.TV-2012)', 'osid' : 'lgtv', 'url_up': url_update_1},
  '3' : {'ua' : 'Mozilla/5.0 (FreeBSD; Viera; rv:34.0) Gecko/20100101 Firefox/34.0', 'osid' : 'panasonictv', 'url_up': url_update_1},
  '4' : {'ua' : 'Bulsatcom for android', 'osid' : 'androidtv', 'url_up': url_update_1},
}

def url_update(u):
  u = __ua_os[sys.argv[1]]['url_up'](u)
  if dbg:
    print '### %s os: %s -> %s' % ('xxx', __ua_os[sys.argv[1]]['osid'], u,)
  return u

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

def progress_cb (a):
  print 'Cb: %s -> %s' % (a['str'], a['pr'])

#if __name__ == '__main__':
  #if len(sys.argv) != 2:
    #for p in sys.argv:
      #print p
    #print '0 - pcweb, 1 - samsungtv'
    #sys.exit('wrong parameters')

  #if sys.argv[1] != '0':
    #UA['User-Agent'] = __ua_os[sys.argv[1]]['ua']

  #import bsc
  #start_time = time.time()
  #p = os.path.join(os.getcwd(), 'tmp')
  #v = '0.0.0'

  #map_url = 'http://snip.li/epgmap'

  #print usr, psw, p, v
  #b = bsc.dodat(base = 'https://api.iptv.bulsat.com',
                #login = {'usr': usr,'pass': psw},
                #path = p,
                #cachetime = 1,
                #dbg = dbg,
                #timeout = 10,
                #ver = v,
                #xxx = True,
                #os_id =  __ua_os[sys.argv[1]]['osid'],
                #agent_id = __ua_os[sys.argv[1]]['ua'],
                #app_ver = '0.2.17',
                #gen_m3u = True,
                #gen_epg = False,
                #compress = True,
                #map_url = map_url,
                #proc_cb = progress_cb,
            #)
  #b.gen_all(True)


def main():
    server.my_serv.start()
    try:
        while True:
            ch = raw_input("q - quit\nr - restart\n")
            print ch

            if ch == "q":
                break;
            if ch == "r":
                server.my_serv.restart()
    except KeyboardInterrupt:
        print "\nKeyboardInterrupt"
        pass

def __log(fmt, data):
    print fmt % data

if __name__ == "__main__":
    if len(sys.argv) != 2:
        for p in sys.argv:
            print p
        print '0 - pcweb, 1 - samsungtv'
        sys.exit('wrong parameters')
    import server
    server.log_cb = __log
    server.dumper_path = os.path.join(os.getcwd(), 'resources', 'dumper.template')
    kwargs = {
        'base': 'https://api.iptv.bulsat.com',
        'login': {'usr': usr,'pass': psw},
        'xxx': True,
        'os_id': __ua_os[sys.argv[1]]['osid'],
        'agent_id': __ua_os[sys.argv[1]]['ua'],
        'proc_cb': progress_cb,
        'app_ver': '0.2.17',
        'path': os.path.join(os.getcwd()),
        'timeout': 10,
        'dbg': True,
        'gen_epg': False
      }
    server.my_serv = server.serv(kwargs)

    main()
    del server.my_serv
