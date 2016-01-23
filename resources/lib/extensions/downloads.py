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
import xbmcgui
import threading
import time
import urllib

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
		xbmc.log('Entering build_downloadsList')
		downloads = []
		subdirs = [oneDir for oneDir in os.listdir(self.ContentDownloadFolder) if os.path.isdir(os.path.join(self.ContentDownloadFolder, oneDir))]
		downloadsInProgress = False
		for oneSubdir in subdirs:
			# Only focus on those dirs where the "download progress" file exists
			downloadProgressFilename = os.path.join(self.ContentDownloadFolder, oneSubdir, 'downloadProgress.dat')
			if not os.path.exists(downloadProgressFilename):
				continue
			downloadProgress = RecordingDownloadProgress(None, 0)
			downloadProgress.deserialize(downloadProgressFilename)
			contentSaveFilename = os.path.join(self.ContentDownloadFolder, oneSubdir, 'content.ts')
			downloadPercent = downloadProgress.getProgressPercentage()
			errorMessage = downloadProgress.ErrorMessage
			label = downloadProgress.Title
			if downloadPercent < 100:
				label += ' [COLOR yellow][{0}% downloaded][/COLOR]'.format(downloadPercent)
				if downloadProgress.LastStatus == 'OK':
					downloadsInProgress = True
			if errorMessage is not None:
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
		if downloadsInProgress:
			# Refresh every few seconds
			myWin = xbmcgui.Window(xbmcgui.getCurrentWindowId())
			myWin.setProperty('downloadsWindow', 'True')
			guiUpdateThread = threading.Thread(
				name = 'guiUpdateThread',
				target = self.refreshGuiItems,
				args = (downloads, ) )
			guiUpdateThread.daemon = True
			guiUpdateThread.run()

	def watch(self, args):
		contentSaveFilename = args['path']
		if os.path.exists(contentSaveFilename):
			self.ZBProxy.play_stream(contentSaveFilename)

	def refreshGuiItems(self, downloads):
		xbmc.log('in refreshGuiItems')
		time.sleep (4)
		xbmc.executebuiltin('Container.Refresh')
		return
