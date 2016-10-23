# -*- coding: utf8 -*-
"""
Very simple HTTP server in python.
Usage::
    ./dummy-web-server.py [<port>]
Send a GET request::
    curl http://localhost:8888
Send a HEAD request::
    curl -I curl http://localhost:8888
Send a POST request::
    curl -d "foo=bar&bin=baz" curl http://localhost:8888
"""

from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import threading
import bsc
import os
import simplejson as json

ch_cb = None
log_cb = None
my_serv = None

def my_log (fmt, data):
    if log_cb:
        log_cb(fmt, data)

def reboot(s, arg= None):
    s.send_response(200)
    s.send_header("Content-type", "text/html")
    s.end_headers()
    s.wfile.write(b"<html><body><h1>restart!</h1></body></html>")

    def rst(arg):
        thr = threading.current_thread()
        arg.restart()
        my_log ("%s Reboot server", thr.getName())

    t = threading.Thread(target=rst, name="Httpd_reboot", kwargs={"arg": my_serv})
    #t.setDaemon(True)
    t.start()

def get_id(s, arg):
    if check_ua(s):
        s.send_response(302)
        s.send_header("Content-type", "application/x-mpegurl")
        s.send_header("Location", s.server.d.get('dat', {}).get(arg, {'url': 'http://google.bg'})['url'])
        s.end_headers()
    else:
        err_responce(s)

def err_responce(s):
    s.send_response(404)
    s.send_header("Content-type", "text/html")
    s.end_headers()
    s.wfile.write(b"<html><body><h1>Error!</h1></body></html>")
    s.wfile.write(bytes("Path:\n%s\nHeader:\n%s" % (s.path, s.headers), 'utf-8'))

def pls(s):
    with open(os.path.join(s.server.d['path'], 'mapch.json'), 'r') as f:
      ch_map = json.load(f)
    if check_ua(s):
        _list = '#EXTM3U\n\n'
        for k, v in s.server.d['dat'].items():
            _radio = 'False'
            if 'Радио' in v['group']:
                _radio = 'True'

            remap = ch_map.get(v['id'], {'id': v['id'], 'logo': '%s.png' % v['id'], 'title': v['title'], 'group': v['group']})

            nameepg = remap.get('id', v['id'])
            logo = remap.get('logo', '%s.png' % v['id'])
            title = remap.get('title', v['title'])
            group = remap.get('group' , v['group'])

            _list += '#EXTINF:-1 radio="%s" tvh-tags="%s" tvg-id="%s" tvg-logo="%s" tvh-epg="off",%s\n' % (_radio, group, nameepg, logo, title,)
            #_list += 'http://%s/id/%s|User-Agent=%s\n' % ( s.headers['Host'], v['id'], s.server.d['ua'])
            _list += 'pipe:///usr/bin/ffmpeg -loglevel fatal -ignore_unknown -headers "User-Agent: %s" -i http://%s/id/%s -map 0 -c copy -metadata service_provider=bsc -metadata service_name=%s -tune zerolatency -f mpegts pipe:1\n'  % (s.server.d['ua'], s.headers['Host'], v['id'], v['id'])

        s.send_response(200)
        s.send_header("Content-type", "application/x-mpegurl")
        s.end_headers()
        s.wfile.write(_list.encode('utf-8'))
    else:
        err_responce(s)

def check_ua(s):
    if s.headers['User-Agent'] in s.server.d['ua']:
        return True

    for a in ['Kodi', 'TVH']:
        if a in s.headers['User-Agent']:
            return True

map_cmd = {
    'reboot' : reboot,
    'id': get_id,
    'bsc' : pls,
    }

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
      spath = self.path.split("/")
      if len(spath) == 2:
          map_cmd.get(spath[1], err_responce)(self)
          return
      elif len(spath) == 3:
          map_cmd.get(spath[1], err_responce)(self, spath[2])
          return
      err_responce(self)

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format, *args):
        if ch_cb:
          ch_cb(self.path)
        my_log("%s", self.headers['User-Agent'])
        my_log(format, args)

def worker(serv, stop):
    thr = threading.current_thread()
    while not stop.is_set():
        serv.serve_forever()
        my_log ("%s Exit server", thr.getName())

class myServer(HTTPServer):
    def __init__(self, s, h, d):
        HTTPServer.__init__(self, s, h)
        self.d = d

class serv():
    def __init__(self, kwargs, server="", port=8888, log=None):
        self._kwa = kwargs
        self._port = port
        self._server = server
        self._datas = {
            'path' : kwargs['path']
          }
        self._server = myServer((self._server, self._port), MyHandler, self._datas)

    def start (self):
        my_log("%s", "Start server")

        self.b = bsc.dodat(**self._kwa)
        self._datas['dat'], self._datas['ua']= self.b.gen_all()

        self._stop = threading.Event()
        self._work = threading.Thread(target=worker, name="Httpd", kwargs={"serv": self._server, "stop":  self._stop})
        self._work.start()

    def __stop (self):
        my_log("%s", "Stop server")
        self.b.log_out()
        self._stop.set()
        self._server.shutdown()
        self._work.join()

    def restart(self):
        self.__stop ()
        self.start()

    def __del__(self):
        my_log("%s", "Del server")
        self.__stop()
