# coding=utf-8

##################################
# ZattooBox Playlist proxy
#
# (c) 2014-2015 Pascal Nançoz; Guido Domenici
##################################

import xbmc, xbmcplugin, xbmcgui
from zbaddonproxy import ZBAddonProxy

# This is used for synchronization with the PVR plugin
# Note that we inherit from ZBAddonProxy
class ZBPlaylistProxy(ZBAddonProxy):
	Addon = None
	URLBase = None
	SourcePath = None
	StoragePath = None
	DirectoryItems = None

	def __init__(self, addon, urlBase):
		self.Addon = addon
		self.URLBase = urlBase
		self.SourcePath = xbmc.translatePath(addon.getAddonInfo('path')).decode('utf-8')		
		self.StoragePath = xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')
		self.DirectoryItems = None

	def get_string(self, code):
		return self.Addon.getLocalizedString(code)

	# Writes the playlist to the specified m3u file
	def add_directoryItems(self, items):
		'''
		with open(self.M3UPath, 'w') as f:
			f.write ('#EXTM3U\n')
			for item in items:
				if item.IsFolder:
					continue
				listEntry = '#EXTINF:-1 tvg-id="{0}" tvg-logo="{1}" group-title=German-TV-Channels",[COLOR deepskyblue]\n'.format(
					item.Args['cid'], item.Image)
				f.write(listEntry)
				f.write(item.get_url() + '\n')
		'''
		self.DirectoryItems = items
