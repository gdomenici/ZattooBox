import sys, urlparse
import time
import xbmc
import xbmcaddon

from resources.lib.core.zapisession import ZapiSession
from resources.lib.core.zbplaylistproxy import ZBPlaylistProxy
from resources.lib.extensions.pvrsync import PvrSync
 
def downloadChannelList():
	if zapiSession.init_session(kodi_addon.getSetting('username'), kodi_addon.getSetting('password'), False):
		pvrSync = PvrSync(zapiSession, zbPlaylistProxy, kodi_addon.getSetting('m3uPath'))
		pvrSync.create_pvr_playlist()
	else:
		xbmcgui.Dialog().ok(kodi_addon.getAddonInfo('name'), kodi_addon.getLocalizedString(30902))
 

if __name__ == '__main__':
	
	#Main
	kodi_addon = xbmcaddon.Addon()

	zbPlaylistProxy = ZBPlaylistProxy(
		kodi_addon,
		sys.argv[0])
	zapiSession = ZapiSession(zbPlaylistProxy.StoragePath)
	
	monitor = xbmc.Monitor()

	# Do the initial one on startup
	downloadChannelList()
	
	while not monitor.abortRequested():
	#if True:
		# Sleep/wait for abort for the time that's in settings
		# Note that the setting is in minutes, but waitForAbort wants seconds
		m3uGenerateFrequency = int(kodi_addon.getSetting('m3uGenerateFrequency'))
		if monitor.waitForAbort(m3uGenerateFrequency * 60):
			# Abort was requested while waiting. We should exit
			break
		downloadChannelList()
