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

from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import time
import threading
import bsc
import simplejson as json
import os

ch_cb = None
log_cb = None
my_serv = None
name = None
ddd = None
dumper_path = None
dmp = 'dumper'

def my_log (fmt, data):
    if log_cb:
        log_cb(fmt, data)

def add_dumper(s):
    if os.path.exists(dumper_path):
        with open(dumper_path, 'r') as t:
          l = t.read() % s._datas['ua']

        path = os.path.join(s._kwa['path'], dmp)
        if os.path.exists(path):
            with open(path, 'r+b') as f:
                if l == f.read():
                    return
                else:
                    f.seek(0)
                    f.write(l)

        with open(path, 'w') as f:
            f.write(l)
            os.chmod(path, 0777)
    else:
        raise Exception('%s\nTemplate non found:' % dumper_path)

def reboot(s, arg= None):
    s.send_response(200)
    s.send_header("Content-type", "text/html")
    s.end_headers()
    s.wfile.write("<html><body><h1>restart!</h1></body></html>")

    def rst(arg):
        thr = threading.current_thread()
        arg.restart()
        my_log ("%s Reboot server", thr.getName())

    t = threading.Thread(target=rst, name="Httpd_reboot", kwargs={"arg": my_serv})
    #t.setDaemon(True)
    t.start()

def get_id(s, arg):
    s.send_response(302)
    s.send_header("Location", s.server.d.get('dat', {}).get(arg, {'url': 'http://google.bg'})['url'])
    s.end_headers()

def err_responce(s):
    s.send_response(404)
    s.send_header("Content-type", "text/html")
    s.end_headers()
    s.wfile.write("<html><body><h1>Error!</h1></body></html>")
    s.wfile.write("Path:\n%s\nHeader:\n%s" % (s.path, s.headers))

def pls(s):
    _list = '#EXTM3U\n\n'

    if 'Kodi' in s.headers['User-Agent']:
      for k, v in s.server.d['dat'].iteritems():
          _radio = 'False'
          if u'Радио' in v['group']:
              _radio = 'True'

          _list += '#EXTINF:-1 radio="%s" group-title="%s" tvg-id="%s",%s\n' % (_radio, v['group'], v['id'], v['title'],)
          _list += 'http://%s/id/%s\n' % ( s.headers['Host'], v['id'])

    s.send_response(200)
    s.send_header("Content-type", "video/mpegurl")
    s.end_headers()
    s.wfile.write(_list.encode('utf-8'))

def dump_ch(s):
    _json_data = {
                    "service": "bsc_iptv",
                    "list": []
                  }

    for k, v in s.server.d['dat'].iteritems():
        l = {
            'mux_url': u'pipe://%s %s %s' % (os.path.join(s.server.d['path'], dmp), s.headers['Host'], v['id']),
            'mux_name': v['id'],
            'tag': v['group'],
            'title': v['title'],
            'ch_idx': v['ch_idx'],
        }
        _json_data['list'].append(l)

    s.send_response(200)
    s.send_header("Content-type", "text/json; charset=UTF-8")
    s.end_headers()
    s.wfile.write(json.dumps(_json_data))

map_cmd = {
    'reboot' : reboot,
    'id': get_id,
    'dumpch': dump_ch,
    'm3u8' : pls,
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

        if ddd:
            dp = ddd()
            dp.create(heading = name)

            def progress_cb (a):
                _str = name
                if a.has_key('idx') and a.has_key('max'):
                    _str += ' %s of %d' % (a['idx'], a['max'])
                    dp.update(a['pr'], _str  , a['str'])

            self._kwa['proc_cb'] = progress_cb

        b = bsc.dodat(**self._kwa)
        self._datas['dat'], self._datas['ua']= b.gen_all()

        add_dumper(self)

        self._stop = threading.Event()
        self._work = threading.Thread(target=worker, name="Httpd", kwargs={"serv": self._server, "stop":  self._stop})
        self._work.start()

        if ddd:
            time.sleep(1)
            dp.close()

    def __stop (self):
        my_log("%s", "Stop server")
        self._stop.set()
        self._server.shutdown()
        self._work.join()

    def restart(self):
        self.__stop ()
        self.start()

    def __del__(self):
        my_log("%s", "Del server")
        self.__stop()
