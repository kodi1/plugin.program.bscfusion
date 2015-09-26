# -*- coding: utf8 -*-

import os, json, time
import base64
from requests import Session, codes
import io
from time import localtime, strftime
import aes as EN
from hashlib import md5

def gen_logo(stri, f_name, pr):
  img = stri.decode('base64')
  if os.path.exists(f_name):
    with open(f_name, "r+b") as f:
      if md5(img).hexdigest() != md5(f.read()).hexdigest():
        f.seek(0)
        f.write(img)
  else:
    with open(f_name, "wb") as f:
      f.write(img)
  return {'pr': pr, 'str': 'Logo: %s' % os.path.splitext(os.path.basename(f_name))[0]}

class dodat():
  def __init__(self,
                base,
                login,
                cachepath,
                cachetime=1,
                dbg=False,
                dump_name='',
                timeout=0.5,
                ver = '0.0.0',
                xxx = False,
                proc_cb = None):
    self.__UA = {
                'Host': 'api.iptv.bulsat.com',
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0',
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://test.iptv.bulsat.com/iptv.php',
                'Origin': 'https://test.iptv.bulsat.com',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                }

    self.__log_in = {}
    self.__p_data = {
                'user' : ['',''],
                'device_id' : ['','pcweb'],
                'device_name' : ['','pcweb'],
                'os_version' : ['','pcweb'],
                'os_type' : ['','pcweb'],
                'app_version' : ['','0.01'],
                'pass' : ['',''],
                }
    self.__cachepath = cachepath
    self.__refresh = int(cachetime) * 60
    self.__p_data['user'][1] = login['usr']
    self.__log_in['pw'] = login['pass']
    self.__DEBUG_EN = dbg
    self.__t = timeout
    self.__BLOCK_SIZE = 16
    self.__URL_LOGIN = base + '/?auth'
    self.__URL_LIST = base + '/tv/full/live'
    self.__URL_EPG  = base + '/epg/short'
    self.__js = None
    self.__lgos = ['logo', 'logo_epg', 'logo_favorite', 'logo_mobile', 'logo_mobile_selected', 'logo_selected']
    self.__app_version = ver
    self.__x = xxx
    self.__cb = proc_cb

  def __create_logo_dir(self):
    for l in self.__lgos:
      d = os.path.join(os.path.dirname(self.__cachepath), l)
      if not os.path.exists(d):
        os.makedirs(d)

  def __mk_logos(self):
    c1 = float(1.0 / (len(self.__js['tvlists']['tv']) * len(self.__lgos)))
    pr = float(0.0)
    try:
      import multiprocessing as mp
      from multiprocessing.pool import ThreadPool

      p = ThreadPool(processes = mp.cpu_count())

      for ch in self.__js['tvlists']['tv']:
        for l in self.__lgos:
          pr += c1
          f_name = os.path.join(os.path.dirname(self.__cachepath), l, ('%s.png' % ch['epg_name']))
          p.apply_async(func = gen_logo, args = (ch[l], f_name, pr), callback = self.__cb)
          ch[l] = f_name

      p.close()
      p.join()
    except:
      for ch in self.__js['tvlists']['tv']:
        for l in self.__lgos:
          pr += c1
          f_name = os.path.join(os.path.dirname(self.__cachepath), l, ('%s.png' % ch['epg_name']))
          self.__cb(gen_logo(ch[l], f_name, pr))
          ch[l] = f_name
      pass

  def __log_dat(self, d):
    if self.__DEBUG_EN is not True:
      return
    print '--------- BEGIN ---------'
    if type(d) is str:
      print d
    elif type(d) is dict or type(d).__name__ == 'CaseInsensitiveDict':
      for k, v in d.iteritems():
        print k + ' : ' + str(v)
    elif type(d) is list:
      for l in d:
        print l
    else:
      print 'Todo add type %s' % type(d)
    print '--------- END -----------'

  def __store_data(self):
      with io.open(self.__cachepath, 'w+', encoding=self.__char_set) as f:
        f.write(unicode(json.dumps(self.__js,
                        sort_keys = True,
                        indent = 1,
                        ensure_ascii=False)))

  def __restore_data(self):
    with open(self.__cachepath, 'r') as f:
      self.__js = json.load(f)

  def __goforit(self):
    if self.__cb:
      self.__cb({'pr': 0.10, 'str': 'Session'})
    s = Session()
    r = s.post(self.__URL_LOGIN, timeout=self.__t,
                headers=self.__UA)

    if r.status_code == codes.ok:
      if self.__cb:
        self.__cb({'pr': 0.20, 'str': 'Session start'})
      self.__log_in['key'] = r.headers['challenge']
      self.__log_in['session'] = r.headers['ssbulsatapi']

      s.headers.update({'SSBULSATAPI': self.__log_in['session']})

      _text = self.__log_in['pw'] + (self.__BLOCK_SIZE - len(self.__log_in['pw']) % self.__BLOCK_SIZE) * '\0'

      enc = EN.AESModeOfOperationECB(self.__log_in['key'])
      self.__p_data['pass'][1] = base64.b64encode(enc.encrypt(_text))

      self.__log_dat(self.__log_in)
      self.__log_dat(self.__p_data)

      if self.__cb:
        self.__cb({'pr': 0.30, 'str': 'Login start'})

      r = s.post(self.__URL_LOGIN, timeout=self.__t,
                  headers=self.__UA, files=self.__p_data)

      self.__log_dat(r.request.headers)
      self.__log_dat(r.request.body)

      if r.status_code == codes.ok:
        data = r.json()
        if data['Logged'] == 'true':
          self.__log_dat('Login ok')

          if self.__cb:
            self.__cb({'pr': 0.50, 'str': 'Login ok'})

          s.headers.update({'Access-Control-Request-Method': 'POST'})
          s.headers.update({'Access-Control-Request-Headers': 'ssbulsatapi'})

          r = s.options(self.__URL_LIST, timeout=self.__t,
                          headers=self.__UA)

          self.__log_dat(r.request.headers)
          self.__log_dat(r.headers)
          self.__log_dat(str(r.status_code))

          if self.__cb:
            self.__cb({'pr': 0.70, 'str': 'Fetch data'})

          r = s.post(self.__URL_LIST, timeout=self.__t,
                      headers=self.__UA)

          self.__log_dat(r.request.headers)
          self.__log_dat(r.headers)
          if r.status_code == codes.ok:
            self.__char_set = r.headers['content-type'].split('charset=')[1]
            self.__log_dat('get data ok')
            self.__js = {'tvlists': {'tv' : r.json()}}
            self.__log_dat(self.__js)

            if self.__cb:
              self.__cb({'pr': 1.0, 'str': 'Fetch data done'})

            for i, ch in enumerate(self.__js['tvlists']['tv']):
              if self.__cb:
                self.__cb({'pr': (float(i) / len(self.__js['tvlists']['tv'])), 'str': ('Epg sync %s' % ch['epg_name']).encode('utf-8')})
              if ch.has_key('program'):
                r = s.post(self.__URL_EPG, timeout=self.__t,
                            headers=self.__UA,
                            data={
                              'epg': 'nownext',
                              'channel': ch['epg_name']
                              }
                          )
                if r.status_code == codes.ok:
                  ch['program'] = r.json()[ch['epg_name']]['programme']

        else:
          raise Exception("LoginFail")

  def __data_fetch(self):
    if os.path.exists(self.__cachepath):
      self.__restore_data()
      if time.time() - self.__js['ts'] < self.__refresh:
        self.__log_dat('Use cache file')
      else:
        self.__log_dat('Use site')
        self.__js = None

    if self.__js is None:
      self.__goforit()
      self.__log_dat('Len: %d' % len(self.__js['tvlists']['tv']))
      self.__create_logo_dir()
      self.__mk_logos()
      self.__js['ts'] = divmod(time.time(), self.__refresh)[0] * self.__refresh
      self.__js['app_version'] = self.__app_version
      self.__log_dat('Base time: %s' % time.ctime(self.__js['ts']))
      self.__store_data()

  def get_genres(self):
    self.__data_fetch()
    seen = set()
    dat = [x['genre'] for x in self.__js['tvlists']['tv'] if not (x['genre'] in seen or seen.add(x['genre'])) and (x['pg'] == 'free' or self.__x)]

    for i, g in enumerate(dat):
      if self.__cb:
        self.__cb({'pr': (float(i) / len(dat)), 'str': g.encode('utf-8')})

      yield g

  def get_all_by_genre(self, g):
    self.__data_fetch()
    dat = [x for x in self.__js['tvlists']['tv'] if x['genre'] == g and (x['pg'] == 'free' or self.__x)]

    for i, ch in enumerate(dat):
      if self.__cb:
        self.__cb({'pr': (float(i) / len(dat)), 'str': ch['epg_name'].encode('utf-8')})

      yield ch
