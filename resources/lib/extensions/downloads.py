# coding=utf-8

##################################
# ZattooBox extension
# Downloads
# (c) 2014-2016 Pascal Nançoz; Guido Domenici
##################################

from resources.lib.core.zbextension import ZBExtension
from resources.lib.core.zbfolderitem import ZBFolderItem
from resources.lib.core.zbplayableitem import ZBPlayableItem
from resources.lib.extensions.recordingdownload.recordingdownloadprogress import RecordingDownloadProgress
import os
import xbmc

class Downloads(ZBExtension):
	DownloadRootFolder = None

	def init(self):
		self.DownloadRootFolder = os.path.join(self.ZapiSession.CACHE_FOLDER, 'Downloads')
		return

	def get_items(self):
		content = [
			ZBFolderItem(
				host=self,
				args={'mode': 'root'},
				title=self.ZBProxy.get_string(30104), # Downloads
				image=os.path.join(self.ExtensionsPath, 'downloads/downloadedvideo.png')
			)
		]
		return content

	def activate_item(self, args):
		if args['mode'] == 'root':
			self.build_downloadsList()
		elif args['mode'] == 'watch':
			self.watch(args)

	def build_downloadsList(self):
		downloads = []
		subdirs = [oneDir for oneDir in os.listdir(self.DownloadRootFolder) if os.path.isdir(os.path.join(self.DownloadRootFolder, oneDir))]
		for oneSubdir in subdirs:
			# Only focus on those dirs where the "download progress" file exists
			downloadProgressFilename = os.path.join(self.DownloadRootFolder, oneSubdir, 'downloadProgress.dat')
			if not os.path.exists(downloadProgressFilename):
				continue
			downloadProgress = RecordingDownloadProgress(None, 0)
			downloadProgress.deserialize(downloadProgressFilename)
			rootPlaylistFilename = os.path.join(self.DownloadRootFolder, oneSubdir, 'content.ts')
			downloads.append(ZBPlayableItem(
				host=self,
				args={'mode': 'watch', 'path': rootPlaylistFilename},
				title=downloadProgress.Title,
				image=None,
				title2=''
				)
			)
		self.ZBProxy.add_directoryItems(downloads)

	def watch(self, args):
		rootPlaylistFilename = args['path']
		if os.path.exists(rootPlaylistFilename):
			self.ZBProxy.play_stream(rootPlaylistFilename)
