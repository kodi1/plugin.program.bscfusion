#!/usr/bin/python
# -*- coding: utf8 -*-

import os, sys
from time import sleep

try:
    import requests
except:
    p = os.path.join(os.getcwd(), '..', 'script.module.requests', 'lib')
    sys.path.insert(0, p)
    import requests
    pass

try:
    import simplejson as json
except:
    p = os.path.join(os.getcwd(), '..', 'script.module.simplejson', 'lib')
    sys.path.insert(0, p)
    import simplejson as json
    pass

__delay = 1
create_mux = 'api/mpegts/network/mux_create'
create_net = 'api/mpegts/network/create'
load_node = 'api/idnode/load'
save_node = 'api/idnode/save'
load_mux = 'api/mpegts/mux/grid'
get_service = 'api/mpegts/service/grid'
get_tags = 'api/channeltag/grid'
map_all = 'api/service/mapper/start'

_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Connection': 'keep-alive'
}

net_create_data = {
    'class': 'iptv_network',
    'conf': ''
}

load_data = {
    'class': 'mpegts_network',
    'enum': '1',
    'query': '',
}

grid_list = {
    'sort': 'name',
    'dir': 'ASC',
    'start': 0,
    'limit': 999999999
}

def which(ff):
    for p in os.environ["PATH"].split(os.pathsep):
        pp = os.path.join(p, ff)
        if os.path.exists(pp):
            return pp
    return None


def have_net(e, net):
    for x in e.get('entries', []):
        key = x.get('key', None)
        if key is not None and net == x.get('val', None):
            return key

    return None

def disable_auto_check_service(hts_conn):
    r = hts_conn.post('%s/%s' % (url, get_service), headers=_headers, data=grid_list)
    if r.status_code == requests.codes.ok:
        for x in r.json().get('entries', []):
            _d = {
                  'enabled': True,
                  'auto': 1,
                  'channel': [],
                  'priority': 0,
                  'dvb_ignore_eit': False,
                  'charset': 'AUTO',
                  'prefcapid': 0,
                  'prefcapid_lock': 0,
                  'force_caid': '0x0',
                  'uuid': x['uuid']
                }

            r = hts_conn.post('%s/%s' % (url, save_node), headers=_headers, data={'node': json.dumps(_d)})
            if r.status_code != requests.codes.ok:
                print 'Error: %s -> %d' % (r.url, r.status_code)
                sys.exit('Error auto disabele')
    else:
        print 'Error: %s -> %d' % (r.url, r.status_code)
        sys.exit('Error list auto disabele')

def add_mux(hts_conn, ch):
    _n = {
            'enabled': True,
            'epg': 1,
            'scan_state': 0,
            'pmt_06_ac3': 0,
            'iptv_url': ch['mux_url'],
            'iptv_interface':'',
            'iptv_atsc': False,
            'iptv_muxname' : ch['mux_name'],
            'iptv_sname': ch['mux_name'],
            'charset': 'AUTO',
            'priority': 0,
            'spriority': 0,
            'iptv_respawn': True,
            'iptv_env': ''
        }
    _mux = {
            'uuid': uuid,
            'conf': json.dumps(_n)
        }
    r = hts_conn.post('%s/%s' % (url, create_mux), headers=_headers, data=_mux)
    if r.status_code != requests.codes.ok:
        print '%s\nError:\n%s' % (ch['mux_name'], r.content)
        sys.exit('Error list chanels')
    #else:
        #print 'Add: %s' % ch['mux_name']

def wait_mux(hts_conn):
    sleep(__delay)
    r = hts_conn.post('%s/%s' % (url, get_service), headers=_headers, data=grid_list)
    if r.status_code == requests.codes.ok:
        return len(r.json().get('entries', []))
    else:
        print 'Error: %s -> %d' % (r.url, r.status_code)
        sys.exit('Error list chanels')

def add_tag(hts_conn, tag):
    r = hts_conn.post('%s/api/channeltag/list' % url, headers=_headers)
    if r.status_code != requests.codes.ok:
        print 'Error: %s -> %d' % (r.url, r.status_code)
        sys.exit('Error list chanels')

    for k in r.json().get('entries', []):
        if tag == k.get('val'):
            return k.get('key')

    _n = {
            'enabled': True,
            'index': 0,
            'name': tag,
            'internal': False,
            'private': False,
            'icon': '',
            'titled_icon': False,
            'comment': tag
        }
    r = hts_conn.post('%s/api/channeltag/create' % url, headers=_headers, data={'conf' : json.dumps(_n)})
    if r.status_code != requests.codes.ok:
        print 'Error: %s -> %d' % (r.url, r.status_code)
        sys.exit('Error list chanels')

    r = hts_conn.post('%s/api/channeltag/list' % url, headers=_headers)
    if r.status_code != requests.codes.ok:
        print 'Error: %s -> %d' % (r.url, r.status_code)
        sys.exit('Error list url')

    for k in r.json().get('entries', []):
        if tag == k.get('val'):
            #print 'Tag created %s:\n%s' % (k.get('val'), k.get('key'))
            return k.get('key')

    sys.exit('Error tag')

def epg_chanels_edit(hts_conn, bch):
    r = hts_conn.get('http://epg.kodibg.org/dlmap.php')
    if r.status_code != requests.codes.ok:
        sys.exit('Error map')

    map_epg = r.json()

    r = hts_conn.post('%s/api/epggrab/channel/list' % url, headers=_headers)
    if r.status_code != requests.codes.ok:
        print 'Error: %s -> %d' % (r.url, r.status_code)
        sys.exit('Error list epg/xml')

    epg_list = r.json().get('entries', [])

    r = hts_conn.post('%s/api/channeltag/list' % url, headers=_headers)
    if r.status_code != requests.codes.ok:
        print 'Error: %s -> %d' % (r.url, r.status_code)
        sys.exit('Error list tag')

    tag_list = r.json().get('entries', [])

    r = hts_conn.post('%s/api/channel/list' % url, headers=_headers)
    if r.status_code != requests.codes.ok:
        print 'Error: %s -> %d' % (r.url, r.status_code)
        sys.exit('Error list epg/chanels')

    all_ch = r.json().get('entries', [])
    n = len(all_ch)
    for ch in all_ch:
        for x in bch:
            if ch.get('val') == x.get('mux_name'):
                r = hts_conn.post('%s/%s' % (url, load_node), headers=_headers, data={'uuid': ch['key'],'meta': 1})
                if r.status_code != requests.codes.ok:
                    print 'Error: %s -> %d' % (r.url, r.status_code)
                    sys.exit('Error list epg/chanels')

                for t in tag_list:
                    if t['val'] == x['tag']:
                        break

                ee = []
                for e in epg_list:
                    if e['key'].split('|')[1] == map_epg.get(x['mux_name'], {'id': x['mux_name']})['id']:
                        ee = [e['key']]
                    #if e['text'].split(':')[0] == map_epg.get(x['mux_name'], {'id': x['mux_name']})['id']:
                        #ee = [e['uuid']]
                        break

                update = {'uuid': r.json()['entries'][0]['uuid']}

                p = r.json()['entries'][0]['params']
                for i in [0, 1, 5, 6, 7, 8, 9, 10]:
                #for i in [0, 1, 5, 6, 7, 8, 9, 10, 12]:
                    #print i, x.get('title')
                    update[p[i]['id']] = p[i]['value']

                update['name'] = x['title']
                update['epggrab'] = ee
                update['tags'].append(t['key'])
                update['number'] = x['ch_idx']
                #print json.dumps(update, indent=4 * ' ')

                r = hts_conn.post('%s/%s' % (url, save_node), headers=_headers, data={"node": '%s' % json.dumps(update)})
                if r.status_code != requests.codes.ok:
                    print 'Error: %s -> %d' % (r.url, r.status_code)
                    sys.exit('Error list chanels')
                n -= 1

                e = None
                if len(ee):
                    e = ee[0].split('|')[1]

                print ("Name: %s Epg: %s Cat: %s - %d" % (x.get('title'), e, t['val'], n)).encode('utf8')
                sleep(0.5)
                break

if __name__ == '__main__':
    in_list = []
    if len(sys.argv) != 3:
        sys.exit('\nWrong parameters\nusage: %s [hts hostname/ip] [kodi hostname/ip]\n' % (sys.argv[0]))

    if which('ffmpeg') is None:
        sys.exit('\nffmpeg not found')

    hts_conn = requests.Session()

    r = hts_conn.get('http://%s:8888/dumpch' % sys.argv[2])
    if r.status_code != requests.codes.ok:
        sys.exit('Error Connection')

    lst_all = r.json().get('list', [])
    for ch in lst_all:
        if ch not in in_list:
            in_list.append(ch)
        else:
            print 'Skip duplicate entry: %s' % str(ch)

    net_name = r.json().get('service', 'Unamed')
    _headers['Host'] = '%s:9981' % sys.argv[1]
    url = 'http://%s' % _headers['Host']
    _headers['Referer'] = '%s/extjs.html?' % url

    #epg_chanels_edit(hts_conn, in_list)
    #disable_auto_check_service(hts_conn)
    #sys.exit()

    r = hts_conn.get('%s/extjs.html?' % url, headers=_headers)
    if r.status_code == requests.codes.ok:
        r = hts_conn.post('%s/%s' % (url, load_node), headers=_headers, data=load_data)
        if r.status_code == requests.codes.ok:
            uuid = have_net(r.json(), net_name)
            if uuid is None:
                print 'Create network %s' % net_name
                _c = {
                      'networkname': net_name,
                      'autodiscovery': False,
                      'skipinitscan': True,
                      'id_chnum': False,
                      'ignore_chnum': False,
                      'max_streams': 0,
                      'max_bandwidth': 0,
                      'max_timeout': 15,
                      'nid': 0,
                      'idlescan': False,
                      'charset': 'AUTO',
                      'localtime': False,
                      'priority': 1,
                      'spriority': 1
                      }

                _d = {'class': 'iptv_network', 'conf': json.dumps(_c)}

                r = hts_conn.post('%s/%s' % (url, create_net), headers=_headers, data=_d)
                if r.status_code == requests.codes.ok:
                    r = hts_conn.post('%s/%s' % (url, load_node), headers=_headers, data=load_data)
                    if r.status_code == requests.codes.ok:
                        uuid = have_net(r.json(), net_name)
                        print 'Net created %s uuid %s' % (net_name, uuid)
                    else:
                        print 'Error: %s -> %d' % (r.url, r.status_code)
                        sys.exit('Error list chanels')
                else:
                    print 'Error: %s -> %d' % (r.url, r.status_code)
                    sys.exit('Error list chanels')

            print 'Net %s uuid %s' % (net_name, uuid)
            r = hts_conn.post('%s/%s' % (url, load_mux), headers=_headers, data=grid_list)
            if r.status_code == requests.codes.ok:
                for x in r.json().get('entries', []):
                    for y in in_list:
                        if x['name'] == y['mux_name']:
                            print 'Skip: %s at %s' % (y['mux_name'], y['mux_url'])
                            in_list.remove(y)
            else:
                sys.exit('Error list chanels')

            num = len(in_list)
            #for ch in in_list[30:35]:
            for ch in in_list:
                active = wait_mux(hts_conn)
                add_mux(hts_conn, ch)
                for t in range(0, 30 + __delay, __delay):
                    _a = wait_mux(hts_conn)
                    if _a != active:
                        active = _a
                        break
                num -= 1
                print ('Active %s - %d left' % (ch['mux_name'], num)).encode('utf8')
                add_tag(hts_conn, ch.get('tag', 'empty'))

            disable_auto_check_service(hts_conn)

            r = hts_conn.post('%s/%s' % (url, map_all), headers=_headers)
            if r.status_code != requests.codes.ok:
              print 'Error: %s -> %d' % (r.url, r.status_code)
              sys.exit('Error map all')

            sleep(2)
            epg_chanels_edit(hts_conn, lst_all)
        else:
            print 'Error: %s -> %d' % (r.url, r.status_code)
            sys.exit('Error list chanels')
    else:
        print 'Login Error:\n%s' % r.content
        sys.exit('Error list chanels')
