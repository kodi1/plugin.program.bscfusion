#!/usr/bin/python
# -*- coding: utf8 -*-

import os, sys, time

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

__ua_os = {
  '0' : {'ua' : 'pcweb', 'osid' : 'pcweb'},
  '1' : {'ua' : 'Mozilla/5.0 (SMART-TV; Linux; Tizen 2.3) AppleWebkit/538.1 (KHTML, like Gecko) SamsungBrowser/1.0 TV Safari/538.1', 'osid' : 'samsungtv'},
  '2' : {'ua' : 'HLS Client/2.0 (compatible; LG NetCast.TV-2012)', 'osid' : 'lgtv'},
  '3' : {'ua' : 'Mozilla/5.0 (FreeBSD; Viera; rv:34.0) Gecko/20100101 Firefox/34.0', 'osid' : 'panasonictv'},
  '4' : {'ua' : 'Bulsatcom for android', 'osid' : 'androidtv'},
}


def progress_cb (a):
  print('Cb: %s -> %s' % (a['str'], a['pr']))

def cmd_get_dbg():
  return input("q - quit\nr - restart\n")

def cmd_get():
  if refreshtime:
    time.sleep(600)
    diff = (time.time() - last_runtime[0]) / 60.0
    print('Time check %f' % diff)
    if diff > float(refreshtime):
      last_runtime[0] = time.time()
      return "r"
  else:
   return input("q - quit\nr - restart\n")

def main():
    last_runtime[0] = time.time()
    server.my_serv.start()
    try:
        while True:
            c = cmd_get()
            if c:
              print(c)
            if c == "q":
                break;
            if c == "r":
                server.my_serv.restart()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt")
        pass

def __log(fmt, data):
    print(fmt % data)

usr, psw = os.getenv('BSCLOGIN', 'user:pass').split(':')
refreshtime = os.getenv('BSCREFRESH', False)

last_runtime = [0.0]

if __name__ == "__main__":
    if len(sys.argv) != 2:
        for p in sys.argv:
            print(p)
        print('0 - pcweb, 1 - samsungtv')
        sys.exit('wrong parameters')

    import server
    server.log_cb = __log
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
        'gen_epg': False,
      }
    server.my_serv = server.serv(kwargs)

    main()
    del server.my_serv
