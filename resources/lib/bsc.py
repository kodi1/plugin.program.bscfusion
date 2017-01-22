# -*- coding: utf8 -*-

import os, time
import base64
import requests
import aes as EN
import StringIO
import gzip
import xmltv
import urllib
import simplejson as json

class dodat():
  def __init__(self,
                base,
                login,
                path,
                dump_name='',
                timeout=0.5,
                ver = '0.0.0',
                xxx = False,
                os_id = 'pcweb',
                agent_id = 'pcweb',
                app_ver = '0.01',
                gen_epg = False,
                proc_cb = None,
                dbg=False
                ):

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
                'user' : [None,''],
                'device_id' : [None, os_id],
                'device_name' : [None, os_id],
                'os_version' : [None, os_id],
                'os_type' : [None, os_id],
                'app_version' : [None, app_ver],
                'pass' : [None,''],
                }
    self.__path = path
    self.__p_data['user'][1] = login['usr']
    self.__log_in['pw'] = login['pass']
    self.__DEBUG_EN = dbg
    self.__t = timeout
    self.__BLOCK_SIZE = 16
    self.__URL_LIST = base + '/tv/%s/live' % os_id
    self.__URL_EPG  = base + '/epg/short'
    self.__js = None
    self.__app_version = ver
    self.__x = xxx
    self.__gen_epg = gen_epg
    self.__cb = proc_cb
    self.__gen_jd = False

    self.__s = requests.Session()

    if agent_id != 'pcweb':
      self.__URL_LOGIN = base + '/?auth'
    else:
      self.__URL_LOGIN = base + '/auth'

    if agent_id != 'pcweb':
      self.__UA['User-Agent'] = agent_id

    if not os.path.exists(self.__path):
      os.makedirs(self.__path)

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

  def __log_out(self):
    r = self.__s.post(self.__URL_LOGIN, timeout=self.__t,
          headers=self.__UA, files={'logout': [None,'1']})

    self.__log_dat(r.request.headers)
    self.__log_dat(r.request.body)

    if r.status_code == requests.codes.ok and r.json()['Logged'] == 'false':
      self.__log_dat('Logout ok')
      if self.__cb:
        self.__cb({'pr': 100, 'str': 'Logout ok'})
    else:
      self.__log_dat('Logout Fail')
      raise Exception("LogoutFail")

  def __goforit(self):
    if self.__cb:
      self.__cb({'pr': 10, 'str': 'Session'})
    r = self.__s.post(self.__URL_LOGIN, timeout=self.__t,
                headers=self.__UA)

    if r.status_code == requests.codes.ok:
      if self.__cb:
        self.__cb({'pr': 20, 'str': 'Session start'})
      self.__log_in['key'] = r.headers['challenge']
      self.__log_in['session'] = r.headers['ssbulsatapi']

      self.__s.headers.update({'SSBULSATAPI': self.__log_in['session']})

      _text = self.__log_in['pw'] + (self.__BLOCK_SIZE - len(self.__log_in['pw']) % self.__BLOCK_SIZE) * '\0'

      enc = EN.AESModeOfOperationECB(self.__log_in['key'])
      self.__p_data['pass'][1] = base64.b64encode(enc.encrypt(_text))

      self.__log_dat(self.__log_in)
      self.__log_dat(self.__p_data)

      if self.__cb:
        self.__cb({'pr': 30, 'str': 'Login start'})

      r = self.__s.post(self.__URL_LOGIN, timeout=self.__t,
                  headers=self.__UA, files=self.__p_data)

      self.__log_dat(r.request.headers)
      self.__log_dat(r.request.body)

      if r.status_code == requests.codes.ok:
        data = r.json()
        if data['Logged'] == 'true':
          self.__log_dat('Login ok')

          if self.__cb:
            self.__cb({'pr': 50, 'str': 'Login ok'})

          self.__s.headers.update({'Access-Control-Request-Method': 'POST'})
          self.__s.headers.update({'Access-Control-Request-Headers': 'ssbulsatapi'})

          r = self.__s.options(self.__URL_LIST, timeout=self.__t,
                          headers=self.__UA)

          self.__log_dat(r.request.headers)
          self.__log_dat(r.headers)
          self.__log_dat(str(r.status_code))

          if self.__cb:
            self.__cb({'pr': 70, 'str': 'Fetch data'})

          r = self.__s.post(self.__URL_LIST, timeout=self.__t,
                      headers=self.__UA)

          self.__log_dat(r.request.headers)
          self.__log_dat(r.headers)

          if r.status_code == requests.codes.ok:
            self.__char_set = r.headers['content-type'].split('charset=')[1]
            self.__log_dat('get data ok')
            self.__tv_list = r.json()
            self.__js = {}
            self.__log_dat(self.__js)

            if self.__DEBUG_EN is True:
              with open(os.path.join(self.__path, 'ch_dump'), 'wb') as df:
                df.write(json.dumps(self.__tv_list))

            if self.__cb:
              self.__cb({'pr': 90, 'str': 'Fetch data done'})

            if self.__gen_epg or self.__gen_jd:
              for i, ch in enumerate(self.__tv_list):
                if self.__cb:
                  self.__cb(
                              {
                                'pr': int((i * 100) / len(self.__tv_list)),
                                'str': 'Fetch: %s' % ch['epg_name'].encode('utf-8'),
                                'idx': i,
                                'max': len(self.__tv_list)
                              }
                            )
                if ch.has_key('program'):
                  r = self.__s.post(self.__URL_EPG, timeout=self.__t,
                              headers=self.__UA,
                              data={
                                #'epg': 'nownext',
                                'epg': '1week',
                                #'epg': '1day',
                                'channel': ch['epg_name']
                                }
                            )
                  if r.status_code == requests.codes.ok:
                    ch['program'] = r.json().items()[0][1]['programme']

          from HTMLParser import HTMLParser as h
          self.__js = json.loads(h().unescape(json.dumps(self.__js).decode(self.__char_set)))

          self.__log_out()
          if r.status_code != requests.codes.ok:
            self.__log_dat('Error status code: %d' % (r.status_code, ))
            raise Exception("FetchFail")

        else:
          raise Exception("LoginFail")

  def gen_all(self):
    self.__goforit()
    self.__log_dat('Len: %d' % len(self.__tv_list))

    map_e = {}
    dat = {}
    jdump = {}
    xml = None

    if self.__gen_epg:
      w = xmltv.Writer(encoding=self.__char_set.upper(),
                        date=str(time.time()),
                        source_info_url="",
                        source_info_name="",
                        generator_info_name="",
                        generator_info_url="")

    for i, ch in enumerate(self.__tv_list):
      if self.__cb:
        self.__cb(
                    {
                      'pr': int((i * 100) / len(self.__tv_list)),
                      'str': 'Sync: %s' % ch['epg_name'].encode('utf-8'),
                      'idx': i,
                      'max': len(dat)
                    }
                  )
      dat[ch['epg_name']] = {
          'group': ch['genre'],
          'title': ch['title'],
          'url': ch['sources'],
          'id': ch['epg_name'],
          'ch_idx': ch['channel'],
        }

      if self.__gen_jd:
        jdump[ch['epg_name']]=ch['epg_name']

      if self.__gen_epg:
        w.addChannel(
                    {'display-name': [(ch['title'], u'bg')],
                    'id': ch['epg_name'],
                    'url': ['https://test.iptv.bulsat.com']}
                    )
        if ch.has_key('program'):
          for p in ch['program']:
            w.addProgramme(
                          {'start': p['start'],
                          'stop': p['stop'],
                          'title': [(p['title'], u'')],
                          'desc': [(p['desc'], u'')],
                          'category': [(ch['genre'], u'')],
                          'channel': ch['epg_name']}
                        )

    return dat, self.__UA['User-Agent']
