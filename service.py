# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
import re
import simplejson as json
import urllib
from ga import ga
import time

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon').decode('utf-8')
__language__ = __addon__.getLocalizedString
__cwd__ = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode('utf-8')
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode('utf-8')
__resource__ = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode('utf-8')
__icon_msg__ = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'bulsat.png' ) ).decode('utf-8')
__data__ = xbmc.translatePath(os.path.join( __profile__, '', 'dat') ).decode('utf-8')
__r_path__ = xbmc.translatePath(__addon__.getSetting('w_path')).decode('utf-8')

sys.path.insert(0, __resource__)
import server

def Notify (msg1, msg2):
  xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (msg1, msg2, '5000', __icon_msg__)).encode('utf-8'))

def check_plg():
  js_resp = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddons", "id":1}')
  if int(xbmc.getInfoLabel("System.BuildVersion" )[0:2]) > 14: ln = 1
  else: ln = 2

  if len(re.findall(r'bscf', js_resp)) > ln:
    Notify ('%s %s' % (__scriptname__, __version__) , '[COLOR FFFF0000]confilct ![/COLOR]')
    return False
  else:
    return True

def update(name, dat, crash=None):
  payload = {}
  payload['an'] = __scriptname__
  payload['av'] = __version__
  payload['ec'] = name
  payload['ea'] = dat
  payload['ev'] = '1'
  payload['dl'] = None
  ga().update(payload, crash)

__ua_os = {
  '0' : {'ua' : 'pcweb', 'osid' : 'pcweb'},
  '1' : {'ua' : 'Mozilla/5.0 (SMART-TV; Linux; Tizen 2.3) AppleWebkit/538.1 (KHTML, like Gecko) SamsungBrowser/1.0 TV Safari/538.1', 'osid' : 'samsungtv'},
  '2' : {'ua' : 'HLS Client/2.0 (compatible; LG NetCast.TV-2012)', 'osid' : 'lgtv'},
  '3' : {'ua' : 'Mozilla/5.0 (FreeBSD; Viera; rv:34.0) Gecko/20100101 Firefox/34.0', 'osid' : 'panasonictv'},
  '4' : {'ua' : 'Bulsatcom for android', 'osid' : 'androidtv'},
}

if __addon__.getSetting('firstrun') == 'true':
  Notify('Settings', 'empty')
  __addon__.openSettings()
  __addon__.setSetting('firstrun', 'false')

if __addon__.getSetting('dbg') == 'true':
  dbg = True
else:
  dbg = False

if not __addon__.getSetting('username'):
  Notify('User', 'empty')
if not __addon__.getSetting('password'):
  Notify('Password', 'empty')

def __log(fmt, data):
  if dbg:
    print fmt % data

def _ch_cb(d):
  update('bsc_serv', d)

def dbg_msg(msg):
  if dbg:
    print'### %s: %s' % (__scriptid__, msg)

def m_start():
  kwargs = {
      'base': 'https://api.iptv.bulsat.com',
      'login': {'usr': __addon__.getSetting('username'),
                'pass': __addon__.getSetting('password')
                },
      'xxx': True,
      'os_id': __ua_os[__addon__.getSetting('dev_id')]['osid'],
      'agent_id': __ua_os[__addon__.getSetting('dev_id')]['ua'],
      'proc_cb': None,
      'app_ver': __addon__.getSetting('app_ver'),
      'path': __data__,
      'timeout': float(__addon__.getSetting('timeout')),
      'dbg': dbg,
      'gen_epg': False
    }

  server.my_serv = server.serv(kwargs)
  server.my_serv.start()

def m_stop():
  del server.my_serv

class MyMonitor(xbmc.Monitor):
  def __init__(self, *args, **kwargs):
    xbmc.Monitor.__init__(self)
    m_start()

  def __del__(self):
    m_stop()

  def onSettingsChanged(self):
    m_stop()
    m_start()


server.ch_cb = _ch_cb
server.log_cb = __log
server.ddd = xbmcgui.DialogProgressBG
server.name = __scriptname__
server.dumper_path = os.path.join(__cwd__, 'resources', 'dumper.template')

if __name__ == '__main__':

  _ch_cb('start')

  for files in ['epg_fetch', 'map_to_hts.py']:
    _file = os.path.join(__cwd__, files)
    if not os.access(_file, os.X_OK):
      os.chmod(_file, 0777)

  import traceback
  if not check_plg():
    raise Exception('Version Error')

  monitor = MyMonitor()

  try:
    t_check = time.time() + (float(__addon__.getSetting('refresh')) * 3600)
    while True:
      # Sleep/wait for abort for 3 seconds
      if t_check < time.time():
        server.my_serv.restart()
        t_check = time.time() + (float(__addon__.getSetting('refresh')) * 3600)
      if monitor.waitForAbort(3):
        # Abort was requested while waiting. We should exit
        break

    del monitor
  except Exception, e:
    Notify('Fusion Service', 'Fail')
    traceback.print_exc()
    update('exception', str(e.args[0]), sys.exc_info())
    pass
