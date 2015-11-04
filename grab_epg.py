#!/usr/bin/python
# -*- coding: utf8 -*-

import os, sys, json, re
import datetime, time
from datetime import datetime, timedelta
import requests
import getopt, argparse

offset = 0.0
dbg = True

__resource__ = os.path.join(  os.getcwd(), 'resources', 'lib' )
sys.path.insert(0, __resource__)

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

__ua_os = {
  '0' : {'ua' : 'pcweb', 'osid' : 'pcweb'},
  '1' : {'ua' : 'samsunghas-agent/1.1', 'osid' : 'samsungtv'},
  '2' : {'ua' : 'HLS Client/2.0 (compatible; LG NetCast.TV-2012)'},
  '3' : {'ua' : 'Mozilla/5.0 (FreeBSD; Viera; rv:34.0) Gecko/20100101 Firefox/34.0', 'osid' : 'panasonictv'},
  '4' : {'ua' : 'stagefright', 'osid' : 'androidtv'},
}

def progress_cb (a):
  print 'Cb: %s -> %s' % (a['str'], a['pr'])

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Grab bulsat EPG  data')
  parser.add_argument("-d", help="0 - pcweb 1 - samsungtv 2 - LG 3 - panasonic 4 - android", default='0', choices=['0', '1', '2', '3', '4'], metavar="device id", dest="ua")
  parser.add_argument("-u", help="User", required=True, dest="usr")
  parser.add_argument("-p", help="Password", required=True, dest="psw")
  parser.add_argument("-o", help="Output path", default=os.getcwd(), dest="path")
  parser.add_argument("-c", help="Don't use compression", default=True, dest="compress", action='store_false')
  parser.add_argument("-e", help="Generate Epg", default=False, dest="epg", action='store_true')
  parser.add_argument("-m", help="Generate m3u", default=False, dest="m3u", action='store_true')
  parser.add_argument("-v", help="Debug", default=False, dest="dbg", action='store_true')
  args = parser.parse_args()

  print args

  if args.ua != '0':
    UA['User-Agent'] = __ua_os[args.ua]['ua']

  if not os.path.exists(args.path):
    sys.exit('%s - Not exists' % (args.path,))

  import bsc
  b = bsc.dodat(base = 'https://api.iptv.bulsat.com',
                login = {'usr': args.usr,'pass': args.psw},
                path = args.path,
                cachetime = 1,
                dbg = args.dbg,
                timeout = 10,
                ver = '0.0.0',
                xxx = True,
                os_id =  __ua_os[args.ua]['osid'],
                agent_id = __ua_os[args.ua]['ua'],
                app_ver = '0.2.17',
                gen_m3u = args.m3u,
                gen_epg = args.epg,
                compress = args.compress,
                proc_cb = progress_cb,
            )
  b.gen_all(True)
