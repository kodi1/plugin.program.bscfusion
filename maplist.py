import os, sys, json, re

class tst():
  def __init__ (self):
    self.match = 0
    self.__chmap = {}
    with open ('bgtv.json', 'r') as t:
      self._bgtv = json.load(t)
    with open('list', 'r') as t:
      self._list = t.readlines()

  def update_map_bgtv(self, e):
    for k, v in list(self._bgtv.items()):
      if v['id'] == e['id']:
        e.update({'uri': v['uri']})
        self.match += 1
        self.__chmap.update({k : e})

  def mkchmap(self):
    for l in self._list:
      m = re.match(r'^.*tags="(.*?)".*?"(.*?)".*?"(.*?)".*,(.*?)$', l)
      if m:
          e = {
                'name': m.group(4).decode('utf-8'),
                'id': m.group(2),
                'tag': m.group(1).decode('utf-8'),
                'logo': m.group(3),
                }
          self.update_map_bgtv(e)

  def chmaplist(self):
    for l in self._list:
      m = re.match(r'^.*tags="(.*?)".*?"(.*?)".*?"(.*?)".*,(.*?)$', l)
      if m:
        print('-->\n"id": "%s",\n"logo": "%s",\n"name": "%s",\n"tag": "%s",\n<--' % (
                                                      m.group(2),
                                                      m.group(3),
                                                      m.group(4).decode('utf-8'),
                                                      m.group(1).decode('utf-8'),
                                                    ))

  def dump_data(self):
    s = json.dumps(self.__chmap, indent=2, sort_keys=True, ensure_ascii=False)
    print(s)
    with open('_chmap.json', 'w') as f:
      f.write(s)

  def show(self):
    print(self.__chmap)
    print(x.match)

if '__main__' == __name__:
  x = tst()
  x.mkchmap()
  x.dump_data()
  x.chmaplist()
  x.show()
