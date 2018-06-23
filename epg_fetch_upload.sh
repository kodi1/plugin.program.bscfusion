#!/bin/bash
wget -O epg.xml.gz http://epg.kodibg.org/dl.php
cat epg.xml.gz | nc -q 1 -U /etc/tvheadend/epggrab/xmltv.sock
