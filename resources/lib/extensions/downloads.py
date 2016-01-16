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
	ContentDownloadFolder = None

	def init(self):
		self.ContentDownloadFolder = os.path.join(self.ZapiSession.CACHE_FOLDER, 'Downloads')
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
		subdirs = [oneDir for oneDir in os.listdir(self.ContentDownloadFolder) if os.path.isdir(os.path.join(self.ContentDownloadFolder, oneDir))]
		for oneSubdir in subdirs:
			# Only focus on those dirs where the "download progress" file exists
			downloadProgressFilename = os.path.join(self.ContentDownloadFolder, oneSubdir, 'downloadProgress.dat')
			if not os.path.exists(downloadProgressFilename):
				continue
			downloadProgress = RecordingDownloadProgress(None, 0)
			downloadProgress.deserialize(downloadProgressFilename)
			contentSaveFilename = os.path.join(self.ContentDownloadFolder, oneSubdir, 'content.ts')
			# Read the 'download progress' filename, to see if we're fully or partially downloaded
			downloadProgressSerializeFilename = os.path.join(self.ContentDownloadFolder, oneSubdir, 'downloadProgress.dat')
			downloadPercent = 0
			errorMessage = None
			if os.path.exists(downloadProgressSerializeFilename):
				downloadProgress = RecordingDownloadProgress(None, 0)
				downloadProgress.deserialize(downloadProgressSerializeFilename)
				if downloadProgress.LastStatus == 'OK':
					downloadPercent = int((float(downloadProgress.DownloadedSegments) / float(downloadProgress.TotalSegments)) * 100)
				else:
					errorMessage = downloadProgress.ErrorMessage
			else:
				# If for some mysterious reason we can't find the download progress file, assume it's 100%
				downloadPercent = 100
			label = downloadProgress.Title
			if errorMessage is None:
				if downloadPercent < 100:
					label += ' [COLOR yellow][{0}% downloaded][/COLOR]'.format(downloadPercent) 
			else:
				label += ' [COLOR red][ERRORS - see log][/COLOR]'
				xbmc.log('ERRORS downloading:')
				xbmc.log(errorMessage)
			downloads.append(ZBPlayableItem(
				host=self,
				args={'mode': 'watch', 'path': contentSaveFilename},
				title=label,
				image=None,
				title2=''
				)
			)
		self.ZBProxy.add_directoryItems(downloads)

	def watch(self, args):
		contentSaveFilename = args['path']
		if os.path.exists(contentSaveFilename):
			self.ZBProxy.play_stream(contentSaveFilename)
