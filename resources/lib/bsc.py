# -*- coding: utf8 -*-

import os, time
import requests
import io
import gzip
import xmltv
import urllib.request, urllib.parse, urllib.error
import simplejson as json
#https://github.com/ricmoo/pyaes
import pyaes
from hashlib import md5
from base64 import b64decode
from base64 import b64encode

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
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
                'Accept':'*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'DNT': '1'
                }

    self.__log_in = {}
    self.__path = path
    self.__p_data = {'user': [None, login['usr']]}
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

    retry = requests.packages.urllib3.util.Retry(
                                                  total=5,
                                                  read=5,
                                                  connect=5,
                                                  backoff_factor=1,
                                                  status_forcelist=[ 502, 503, 504 ],
                                                  method_whitelist=['GET', 'POST', 'OPTIONS']
                                                  )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)

    self.__s = requests.Session()
    self.__s.mount('http://', adapter)
    self.__s.mount('https://', adapter)

    if agent_id != 'pcweb':
      self.__URL_LOGIN = base + '/?auth'
      self.__UA['User-Agent'] = agent_id
    else:
      self.__URL_LOGIN = base + '/auth'

    if not os.path.exists(self.__path):
      os.makedirs(self.__path)

    #android_tv diry hack
    if os_id == 'androidtv':
      self.__UA['User-Agent'] = 'okhttp/2.3.0'
      self.__do_login = self.__login_android_tv
      self.__log_out = self.__logout_android_tv
      self.__p_data.update(
                            {
                              'device_id' : [None, '9774d56d682e549c'],
                              'device_name' : [None, 'unknown sdk_google_atv_x86'],
                              'os_version' : [None, '6.0'],
                              'os_type' : [None, 'androidtv'],
                              'app_version' : [None, '2.3.0'],
                              'device_type' : [None,'android-tv'],
                            }
                          )
    else:
      self.__do_login = self.__login_other
      self.__log_out = self.__logout_other
      self.__p_data.update(
                              {
                                'device_id' : [None, os_id],
                                'device_name' : [None, os_id],
                                'os_version' : [None, os_id],
                                'os_type' : [None, os_id],
                                'app_version' : [None, app_ver],
                              }
                            )


  def __login_android_tv(self):
    self.__log_dat('hashpass androidtv')
    d = lambda x: x + '\0' * ((((len(x) // 16) + 1) * 16) - len(x))
    enc = pyaes.Encrypter(pyaes.AESModeOfOperationECB(md5(b'ARTS*#234S').hexdigest().encode('utf-8')), padding=pyaes.PADDING_NONE)
    dat = enc.feed(d(self.__p_data['user'][1] + ':bulcrypt:' + self.__log_in['pw']))
    dat += enc.feed()
    self.__p_data['pass'] = [None, b64encode(dat)]
    self.__log_dat(['hashpass:', self.__p_data['pass']])
    self.__s.headers.update({'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})

    r = self.__s.post(self.__URL_LOGIN, timeout=self.__t,
            headers=self.__UA, params=self.__p_data)

    self.__log_dat(r.request.headers)
    return r

  def __login_other(self):
    self.__log_dat('hashpass other')
    enc = pyaes.Encrypter(pyaes.AESModeOfOperationECB(self.__log_in['key']))
    dat = enc.feed(self.__log_in['pw'])
    dat += enc.feed()
    self.__p_data['pass'] = [None, b64encode(dat)]

    r = self.__s.post(self.__URL_LOGIN, timeout=self.__t,
            headers=self.__UA, files=self.__p_data)

    self.__log_dat(r.request.headers)
    self.__log_dat(r.request.body)
    return r

  def __logout_android_tv(self):
    del self.__s.headers['Content-Type']
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

  def __logout_other(self):
    r = self.__s.post(self.__URL_LOGIN, timeout=self.__t,
          headers=self.__UA, files={'logout': [None,'1']})

    self.__log_dat(r.request.headers)
    self.__log_dat(r.request.body)
    self.__log_dat(r.json())

    if r.status_code == requests.codes.ok and r.json()['Logged'] == 'false':
      self.__log_dat('Logout ok')
      if self.__cb:
        self.__cb({'pr': 100, 'str': 'Logout ok'})
    else:
      self.__log_dat('Logout Fail')
      raise Exception("LogoutFail")

  def __log_dat(self, d):
    if self.__DEBUG_EN is not True:
      return
    print('--------- BEGIN ---------')
    if type(d) is str:
      print(d)
    elif type(d) is dict or type(d).__name__ == 'CaseInsensitiveDict':
      for k, v in d.items():
        print(k + ' : ' + str(v))
    elif type(d) is list:
      for l in d:
        print(l)
    else:
      print('Todo add type %s' % type(d))
    print('--------- END -----------')

  def __goforit(self):
    if self.__cb:
      self.__cb({'pr': 10, 'str': 'Session'})

    #_head={}
    #_head.update(self.__UA)
    #_head.update(
                  #{
                    #'Access-Control-Request-Method': 'POST',
                    #'Access-Control-Request-Headers': 'ssbulsatapi',
                  #}
                #)
    ##r = self.__s.options(self.__URL_LOGIN, timeout=self.__t,
                ##headers=_head)
    r = self.__s.post(self.__URL_LOGIN, timeout=self.__t,
                headers=self.__UA)

    if r.status_code == requests.codes.ok:
      if self.__cb:
        self.__cb({'pr': 20, 'str': 'Session start'})
      self.__log_in['key'] = r.headers['challenge']
      self.__log_in['session'] = r.headers['ssbulsatapi']

      self.__log_dat(self.__log_in)
      self.__log_dat(self.__p_data)

      if self.__cb:
        self.__cb({'pr': 30, 'str': 'Login start'})

      r = self.__do_login()

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
                df.write(json.dumps(self.__tv_list).encode('utf-8'))

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
                if 'program' in ch:
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
                    ch['program'] = list(r.json().items())[0][1]['programme']

          import html as h
          self.__js = json.loads(h.unescape(json.dumps(self.__js)))

        else:
          self.__log_dat(data)
          raise Exception("LoginFail")

  def log_out(self):
    self.__log_out()

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
                    {'display-name': [(ch['title'], 'bg')],
                    'id': ch['epg_name'],
                    'url': ['https://test.iptv.bulsat.com']}
                    )
        if 'program' in ch:
          for p in ch['program']:
            w.addProgramme(
                          {'start': p['start'],
                          'stop': p['stop'],
                          'title': [(p['title'], '')],
                          'desc': [(p['desc'], '')],
                          'category': [(ch['genre'], '')],
                          'channel': ch['epg_name']}
                        )
    if self.__gen_jd:
      with open(os.path.join(self.__path, 'dat'), 'wb') as f:
        f.write(json.dumps(self.__tv_list, indent=2).encode('utf-8'))

    return dat, self.__UA['User-Agent']
