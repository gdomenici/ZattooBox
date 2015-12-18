# coding=utf-8

##################################
# ZattooBox extension
# PvrSync
# (c) 2014-2015 Pascal Nançoz; Guido Domenici
##################################

from livetv import LiveTV
import os

class PvrSync(LiveTV):
	M3UPath = None
	
	def __init__(self, zapiSession, zbProxy, m3uPath):
		super(PvrSync, self).__init__(zapiSession, zbProxy)
		self.M3UPath = m3uPath

	def create_pvr_playlist(self):
		args = {'mode': 'root', 'cat': 'fav'}
		self.build_channelsList(args)
		with open(self.M3UPath, 'w') as f:
			f.write ('#EXTM3U\n')
			for oneItem in self.ZBProxy.DirectoryItems:
				if oneItem.IsFolder:
					continue
				listEntry = '#EXTINF:-1 tvg-id="{0}" tvg-logo="{1}" group-title=German-TV-Channels",[COLOR deepskyblue]\n'.format(
					oneItem.Args['cid'], oneItem.Image)
				f.write(listEntry)
				
				params = {'cid': oneItem.Args['id'], 'stream_type': 'hls'}
				resultData = self.ZapiSession.exec_zapiCall('/zapi/watch', params)
				if resultData is not None:
					url = resultData['stream']['watch_urls'][0]['url']
					f.write(url + '\n')
