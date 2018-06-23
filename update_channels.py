#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
 
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

load_node = 'api/idnode/load'
save_node = 'api/idnode/save'
epggrab_ch_list = 'api/epggrab/channel/list'
channel_list = 'api/channel/list'

_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Connection': 'keep-alive'
}

def update_channels_epg_icon(hts_conn):
	url = 'http://'+sys.argv[1]+':9981'
	ee = []
	epg_icon = ''
	r = hts_conn.get('http://epg.kodibg.org/dlmap.php')
	if r.status_code != requests.codes.ok:
	    sys.exit('Error downloading EPG->BSC map file.')

	map_epg = r.json()
# Loads the map file from local json file
#	with open("/tmp/epg_map.json", "r") as epg_json:
#		map_epg = json.load(epg_json)
#	print json.dumps(map_epg)

#	need to add EPG first, as this will not work properly if EPG is empty!!!
	r = hts_conn.post('%s/%s' % (url, epggrab_ch_list), headers=_headers)
	if r.status_code != requests.codes.ok:
		print 'Error: %s -> %d' % (r.url, r.status_code)
		sys.exit('Error list epggrab channel list.')

	epg_list = r.json().get('entries', [])
	#print json.dumps(epg_list[0])
	r = hts_conn.post('%s/%s' % (url, channel_list), headers=_headers)
	if r.status_code != requests.codes.ok:
		print 'Error: %s -> %d' % (r.url, r.status_code)
		sys.exit('Error list channels')

	all_ch = r.json().get('entries', [])
	for ch in all_ch:
		r = hts_conn.post('%s/%s' % (url, load_node), headers=_headers, data={'uuid': ch['key'],'meta': 1})
		if r.status_code != requests.codes.ok:
			print 'Error: %s -> %d' % (r.url, r.status_code)
			sys.exit('Error loading channel')

		channel_name = r.json()['entries'][0]['text']
		#print ("current channel name: " + channel_name),
		#find channel name in the map and obtain the EPG name for it
		for epg in map_epg:
			#if channel_name == epg:
                        if channel_name.lower() == epg.lower():
			#it exists in the mapping file and matches current channel... get uuid from the existing EPG
			#print ("map_epg.get(ch['text'] is: " + map_epg.get(r.json()['entries'][0]['text'])['id'])
			#matched_name = map_epg.get(r.json()['entries'][0]['text'])['id']
				for e in epg_list:
					current_epg_name = e['text'].split(':')[0]
					#print ("current: " + current_epg_name)
					#print ("e uuid : " + e['uuid'])
					#if current_epg_name == map_epg[epg]['id']:
                                        if current_epg_name.lower() == map_epg[epg]['id'].lower() or current_epg_name.lower() == epg.lower():
						ee = [e['uuid']]
						epg_icon = 'http://logos.kodibg.org/'+current_epg_name.lower()+'.png'
						print ("EPG and icon for "+channel_name+" will be updated")
						break
				break

		update = {'uuid': r.json()['entries'][0]['uuid']}
		update['epggrab'] = ee
		update['icon'] = epg_icon
		#print json.dumps(update, indent=4 * ' ')

		r = hts_conn.post('%s/%s' % (url, save_node), headers=_headers, data={"node": '%s' % json.dumps(update)})
		if r.status_code != requests.codes.ok:
			print 'Error: %s -> %d' % (r.url, r.status_code)
			sys.exit('Error saving channel')

		ee = None
		epg_icon = None

def main(args):
    return 0

if __name__ == '__main__':
	if len(sys.argv) != 2:
		sys.exit('\nWrong parameters\nusage: %s [hts hostname/ip]\n' % (sys.argv[0]))
        print ("Did you add your EPG first? If not, do so first! Otherwise this will not work.")
        raw_input ("Visit http://epg.kodibg.org/ to understand more.")
	hts_conn = requests.Session()
	update_channels_epg_icon(hts_conn)
	sys.exit(main(sys.argv))
