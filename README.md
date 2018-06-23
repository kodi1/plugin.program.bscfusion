plugin.program.bscfusion
======================
It is not official addon from provider.  
It was made just for fun.  
You were warned.  

Plugin can be installed via repo:
https://github.com/kodi1/kodi1.github.io/releases/download/v0.0.1/repo.bg.plugins.zip

How it works:

1.) Install kodi (Tested to be working with kodi 17.6 (current stable)).  
2.) Install tvheadend server (hts) (Tested to be working with version 4.2.4 (current stable)).  
3.) Configure tvheadend server so it is ready for the integration:  
 - By default, connecting to tvheadend web API will not prompt for credentials.  
 - Enable the epggrabber module XMLTV: Configuration / Channel/EPG / EPG Grabber Modules -> and enable External: XMLTV.
 - Locate the xmltv.sock file that got created, for example on Gentoo Linux this falls under: /etc/tvheadend/epggrab/xmltv.sock, adjust filesystem ACLs if needed so you can write to it.
 - Obtain the external EPG, on Linux run: wget -O epg.xml.gz http://epg.kodibg.org/dl.php
 - Upload the EPG into tvheadend via the xmltv socket interface, on Linux run (with root user or another one that has write access to the socket):
   ```zcat epg.xml.gz | nc -q 1 -U /etc/tvheadend/epggrab/xmltv.sock``` OR  
   run ```./epg_fetch_upload.sh``` script.  
   (prerequisite is to have netcat/ncat installed, or use alternative tool that allows you to write to unix sockets)  
 
4.) At this point you are ready to install this plugin in your kodi from the repository provided above. There are instructions on how to do this in the forum, but it boils down to: dowloading the .zip file to the kodi device and going to Addons / My Addons / Install from file. Once installed it will show up under Addons / Services, then you can configure it with all necessary settings, including your Bulsatcom IPTV credentials.  
5.) To see if the plugin works, manually load http://<KODI_IP/FQDN>:8888/dumpch, ie http://127.0.0.1:8888/dumpch. This needs to generate a json list of all the available channels under your subscription. If this works, you are ready to proceed with the tvheadend mapping and integration. If it does not work, you should fix this before proceeding(see bottom).  
6.) Run ```./map_to_hts.py [hts hostname/ip] [kodi hostname/ip]```  
 * kodi and tvheadend can be on different devices and IP addresses, but running them on 'localhost' may be the most standard use case.
 * This script requires python version 2.7 to be installed. It does not have to be the default python interpreter on the system, but needs to be available. If you have problems, just remove the new version 3.x and try running the script again or type: python2.7 map_to_hts.py [parameters*].
 * It may take a while for the muxes creation and services mapping to happen, be patient. This version of the script, runs 5 muxes at the same time for 15 seconds and then spawns another 5. On decent hardware and connection, this should be totally fine.

7.) Run ```./update_channels.py [hts hostname/ip]```  
 * This assigns tags to the channels, links them to the previously installed EPG and puts icons where a mapping between the external EPG and Bulsatcom exists.
 * Same as previous script, requires python version 2.7 to be available on the system.  

8.) Install tvheadend PVR client addon and configure it for the tvheadend IP/FQDN and port.  
9.) Go to TV section and enjoy watching your subscription on this amazing setup!  

You can also watch on your iPhone/iPad using TvhClient, requires both kodi and tvheadend to be up and running.  

If something goes wrong, consult kodi log under ~/.kodi/temp/. It can show you where an obvious problem is.  
Second, use the forums, perhaps others already experience it and figured out a way to resolve it. If you cannot find your problem, ask in the forum.  
Last, create a bug report in github.  

Happy watching!
