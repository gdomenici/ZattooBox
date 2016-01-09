# coding=utf-8

##################################
# ZattooBox extension
# Recordings
# (c) 2014-2015 Pascal Nançoz
##################################

from resources.lib.core.zbextension import ZBExtension
from resources.lib.core.zbfolderitem import ZBFolderItem
from resources.lib.core.zbdownloadableitem import ZBDownloadableItem
from resources.lib.extensions.recordingdownload.recordingdownloader import RecordingDownloader
import os
import thread
import urlparse
import xbmc
import StringIO
import time
import string

class Recordings(ZBExtension):

	def init(self):
		return

	def get_items(self):
		content = [
			ZBFolderItem(
				host=self,
				args={'mode': 'root'},
				title=self.ZBProxy.get_string(30102),
				image=os.path.join(self.ExtensionsPath, 'recordings/video.png')
			)
		]
		return content

	def activate_item(self, args):
		if args['mode'] == 'root':
			self.build_recordingsList()
		elif args['mode'] == 'watch':
			self.watch(args)
		elif args['mode'] == 'download':
			self.download(args)

	#---

	def build_recordingsList(self):
		resultData = self.ZapiSession.exec_zapiCall('/zapi/playlist', None)
		if resultData is None:
			return

		recordings = []
		for record in resultData['recordings']:
			recordings.append(ZBDownloadableItem(
				host=self,
				args={'mode': 'watch', 'id': record['id']},
				title=record['title'],
				image=record['image_url'],
				title2=record['episode_title'],
				contextMenuArgs={'mode': 'download', 'id': record['id'], 'title': record['title']}
				)
			)
		self.ZBProxy.add_directoryItems(recordings)

	def watch(self, args):
		params = {'recording_id': args['id'], 'stream_type': 'hls'}
		resultData = self.ZapiSession.exec_zapiCall('/zapi/watch', params)
		if resultData is not None:
			url = resultData['stream']['url']
			self.ZBProxy.play_stream(url)

	def download(self, args):
		params = {'recording_id': args['id'], 'stream_type': 'hls'}
		resultData = self.ZapiSession.exec_zapiCall('/zapi/watch', params)
		if resultData is not None:
			url = resultData['stream']['url']
			title = args['title']
			downloader = RecordingDownloader(url, title, self)
			try:
				downloader.startDownload() # part of this is asynchronous
				# "Recording download started. Check your Downloads folder for progress."
				self.ZBProxy.show_message(self.ZBProxy.get_string(30903))
			except Exception as ex:
				xbmc.log('******** ERROR:')
				xbmc.log(`ex`)
				# "An error has occurred. Check the log file for details."
				self.ZBProxy.show_message(self.ZBProxy.get_string(30904))
