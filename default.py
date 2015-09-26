# -*- coding: utf-8 -*-
import os, sys
import re

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

import urllib, time, json
#import error _strptime - workaround
import _strptime
from datetime import datetime, timedelta
from ga import ga

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon').decode("utf-8")
__language__ = __addon__.getLocalizedString
__cwd__ = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__resource__ = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
__icon_msg__ = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'bulsat.png' ) ).decode("utf-8")
__data__ = xbmc.translatePath( os.path.join( __profile__, '', 'data.dat') ).decode("utf-8")
sys.path.insert(0, __resource__)

dp = xbmcgui.DialogProgressBG()
dp.create(heading = __scriptname__)

def progress_cb (a):
  dp.update(int(a['pr'] * 100), message = a['str'])

def Notify (msg1, msg2):
  xbmc.executebuiltin((u'Notification(%s,%s,%s,%s)' % (msg1, msg2, '5000', __icon_msg__)).encode('utf-8'))

if os.path.exists(__data__):
  with open(__data__, 'r') as f:
    js = json.load(f)
  if not (js.has_key('app_version') and js['app_version'] == __version__):
    u = __addon__.getSetting("username")
    p = __addon__.getSetting("password")

    for root, dirs, files in os.walk(os.path.dirname(__data__), topdown=False):
      for name in files:
        os.remove(os.path.join(root, name))
      for name in dirs:
        os.rmdir(os.path.join(root, name))
    __addon__.setSetting("firstrun", "true")

if __addon__.getSetting("firstrun") == "true":
  Notify('Settings', 'empty')
  __addon__.openSettings()
  __addon__.setSetting("firstrun", "false")

refresh = __addon__.getSetting("refresh")
timeout = __addon__.getSetting("timeout")
base = __addon__.getSetting("base")
offset = int(__addon__.getSetting("offset"))

if __addon__.getSetting("dbg") == 'true':
  dbg = True
else:
  dbg = False

if __addon__.getSetting("xxx") == 'true':
  xxx = True
else:
  xxx = False

if not __addon__.getSetting("username"):
  Notify('User', 'empty')
if not __addon__.getSetting("password"):
  Notify('Password', 'empty')

import traceback
try:
  import bsc
  b = bsc.dodat(base = base,
                login = {'usr': __addon__.getSetting("username"),
                        'pass': __addon__.getSetting("password")
                        },
                cachepath = __data__,
                cachetime = refresh,
                dbg = dbg,
                timeout=float(timeout),
                ver = __version__,
                xxx = xxx,
                proc_cb = progress_cb)

except Exception, e:
  Notify('Module Import', 'Fail')
  traceback.print_exc()
  update('exception', e.args[0], sys.exc_info())
  pass

def update(name, dat, crash=None):
  payload = {}
  payload['an'] = __scriptname__
  payload['av'] = __version__
  payload['ec'] = name
  payload['ea'] = 'tv_start'
  payload['ev'] = '1'
  payload['dl'] = urllib.quote_plus(dat.encode('utf-8'))
  ga().update(payload, crash)

def mk_info_string (e):
  s =  u'%s' % timesmk(e)
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

def indexch(cat):
  try:
    c = {}
    for c in b.get_all_by_genre(cat):
      addch(c)

  except Exception, e:
    if e.args[0] == 'LoginFail':
      Notify('LoginFail', 'Check login data')
    else:
      Notify('Data', 'Fetch Fail')
    traceback.print_exc()
    update('exception', '%s->%s' % (e.args[0], c.get('title', None)), sys.exc_info())
    pass

def indexcat():
  c = {}
  try:
    for c in b.get_genres():
      addcat(c, 'DefaultFolder.png', 'https://test.iptv.bulsat.com/images/logos/fusion-tv.png')

  except Exception, e:
    if e.args[0] == 'LoginFail':
      Notify('LoginFail', 'Check login data')
    else:
      Notify('Data', 'Fetch Fail')
    traceback.print_exc()
    update('exception', '%s->%s' % (e.args[0], c.get('genre', None)), sys.exc_info())
    pass

def playch(url, name):
  li = xbmcgui.ListItem(path=url)
  # li.addStreamInfo('video', { 'duration': 3600})
  # li.addStreamInfo('subtitle', { 'language': 'en' })
  xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
  update(name, url)

def addch(dat):
  u = sys.argv[0] + "?url=" + urllib.quote_plus(dat['sources']) + "&mode=" + str(1) + "&name=" + urllib.quote_plus(dat['title'].encode('utf-8'))
  liz = xbmcgui.ListItem(dat['title'], iconImage=dat['logo_mobile_selected'], thumbnailImage=dat['logo_selected'])
  info = get_prog_info(dat)

  liz.setInfo(type="video", infoLabels={"Title": dat['title'], "plot": ' '.join(info.split())})
  liz.setInfo('video', { 'title': name})
  liz.setProperty('fanart_image', dat['logo_epg'])
  liz.setProperty("IsPlayable" , "true")
  return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)

def addcat(cat, iconimage, fanart):
  u = sys.argv[0] + "?url=" + urllib.quote_plus('ddd') + "&mode=" + str(2) + "&cat=" + urllib.quote_plus(cat.encode('utf-8'))

  liz=xbmcgui.ListItem(cat, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
  liz.setInfo( type="Video", infoLabels={ "Title": cat})
  liz.setProperty('fanart_image', fanart)
  return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def setviewmode():
  if (xbmc.getSkinDir() != "skin.confluence") or __addon__.getSetting("viewset") != 'true':
    return
  mode = {
            '0': '52',
            '1': '502',
            '2': '51',
            '3': '500',
            '4': '501',
            '5': '508',
            '6': '504',
            '7': '503',
            '8': '515'
          }
  xbmc.executebuiltin('Container.SetViewMode(%s)' % mode[__addon__.getSetting("viewmode")])

def get_params():
  param = []
  paramstring = sys.argv[2]
  if len(paramstring) >= 2:
    params = sys.argv[2]
    cleanedparams = params.replace('?', '')
    if (params[len(params) - 1] == '/'):
      params = params[0:len(params) - 2]
    pairsofparams = cleanedparams.split('&')
    param = {}
    for i in range(len(pairsofparams)):
      splitparams = {}
      splitparams = pairsofparams[i].split('=')
      if (len(splitparams)) == 2:
        param[splitparams[0]] = splitparams[1]
    return param

params = get_params()
url = None
name = None
mode = None

try:
  url = urllib.unquote_plus(params["url"])
except:
  pass
try:
  name = urllib.unquote_plus(params["name"])
except:
  pass
try:
  mode = int(params["mode"])
except:
  pass
try:
  cat = urllib.unquote_plus(params["cat"]).decode('utf-8')
except:
  pass

if mode == None or url == None or len(url) < 1:
  indexcat()
elif mode == 1:
  playch(url, name)
elif mode == 2:
  indexch(cat)

dp.close()
xbmcplugin.setContent(int(sys.argv[1]), 'movies')
setviewmode()
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
