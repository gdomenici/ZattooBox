# coding=utf-8

##################################
# ZattooBox extension
# RecordingDownloader
# (c) 2014-2016 Pascal Nançoz; Guido Domenici
##################################

from recordingdownloadprogress import RecordingDownloadProgress
import os
import thread
import urlparse
import xbmc
import StringIO
import string

class RecordingDownloader:
	Url = None
	Title = None
	Recordings = None
	DownloadRootFolder = None
	MasterPlaylistFolder = None
	
	def __init__ (self, url, title, recordings):
		self.Url = url
		self.Title = title
		self.Recordings = recordings
		self.DownloadRootFolder = os.path.join(self.Recordings.ZapiSession.CACHE_FOLDER, 'Downloads')
		
	def startDownload(self):
		self.createMasterPlaylistFolder()
		highestVariantStream = self.downloadPlaylist()
		# Start downloading highest variant. The highestVariantStream dict looks like this:
		# { 'variantUrl': variantUrl, 'extXStream': line, 'bitrate': bitrate }
		segments = self.downloadVariantPlaylist(highestVariantStream['variantUrl'], highestVariantStream['bitrate'])
		# Starts downloading the actual streams, asynchronously.
		# segments is an array of dict that looks like this:
		# { 'segmentUrl': segmentUrl, 'segmentFullPath': segmentFullPath }
		thread.start_new_thread(self.downloadSegments, (segments, ) )

	def downloadPlaylist(self):
		"""
		Returns a dict corresponding to the highest variant bitrate. The dict looks like this:
		{ 'variantUrl': variantUrl, 'extXStream': line, 'bitrate': bitrate }
		"""
		playlist = self.Recordings.ZapiSession.request_url(self.Url, None)
		playlistStream = StringIO.StringIO(playlist)
		line = playlistStream.readline()
		highestBitrate = 0
		variantStreams = {}
		while line != '':
			if line.startswith('#EXT-X-STREAM-INF:'):
				lineParts = line.split(':')[1].split(',')
				# lineParts looks like [ 'PROGRAM-ID=1', 'BANDWIDTH=2999000' ]
				bitrate = None
				for oneLinePart in lineParts:
					lineAttrs = oneLinePart.split('=')
					if lineAttrs[0] == 'BANDWIDTH':
						bitrate = int(lineAttrs[1])
				if bitrate is None:
					raise Exception('Cannot find BANDWIDTH attribute in master playlist')
				variantUrl = playlistStream.readline()
				if variantUrl == '': # shouldn't happen but you never know
					raise Exception('Malformed playlist: missing variant URL after EXT-X-STREAM-INF tag')
				variantUrl = urlparse.urljoin(self.Url, variantUrl)
				variantStreams[bitrate] = { 'variantUrl': variantUrl, 'extXStream': line, 'bitrate': bitrate }
				if bitrate > highestBitrate:
					highestBitrate = bitrate
			line = playlistStream.readline()
		# Now operate only on the highest bitrate stream
		# Create a new master playlist, outputting only the highest variant
		masterPlaylistFilename = os.path.join(self.MasterPlaylistFolder, 'index.m3u8')
		with open(masterPlaylistFilename, 'w') as playlistOutputStream:
			playlistOutputStream.write('#EXTM3U\n')
			playlistOutputStream.write(variantStreams[highestBitrate]['extXStream']) # this one already has \n at the end
			rewrittenVariantUrl = `highestBitrate` + '.m3u8'
			playlistOutputStream.write(rewrittenVariantUrl + '\n')
		return variantStreams[highestBitrate]
		
	def downloadVariantPlaylist(self, variantUrl, bitrate):
		"""
		Returns an array of a dict that looks like this:
		{ 'segmentUrl': segmentUrl, 'segmentFullPath': segmentFullPath }
		"""
		playlist = self.Recordings.ZapiSession.request_url(variantUrl, None)
		playlistInputStream = StringIO.StringIO(playlist)
		variantPlaylistFilename = os.path.join(self.MasterPlaylistFolder, `bitrate` + ".m3u8")
		line = playlistInputStream.readline()
		segments = []
		with open(variantPlaylistFilename, 'w') as playlistOutputStream:
			while line != '':
				# non-segment lines are rewritten verbatim
				playlistOutputStream.write(line)
				if line.startswith('#EXTINF:'):
					# read next line, containing URL
					segmentUrl = playlistInputStream.readline()
					if segmentUrl == '': # shouldn't happen but you never know
						break
					segmentUrl = urlparse.urljoin(variantUrl, segmentUrl)
					segmentCounter = len(segments)
					segmentFilename = `segmentCounter` + '.ts'
					# rewrite segment URL as local filename URL
					playlistOutputStream.write(segmentFilename + '\n')
					segmentFullPath = os.path.join(self.MasterPlaylistFolder, segmentFilename)
					segments.append( { 'segmentUrl': segmentUrl, 'segmentFullPath': segmentFullPath } )
				line = playlistInputStream.readline()
		return segments

	def downloadSegments (self, segments):
		segmentCount = len(segments)
		xbmc.log('There are this many segments to download:')
		xbmc.log(str(segmentCount))
		# Next: download all segments
		downloadProgress = RecordingDownloadProgress(self.Title, segmentCount)
		downloadProgressSerializeFilename = os.path.join(self.MasterPlaylistFolder, 'downloadProgress.dat')
		downloadProgress.serialize(downloadProgressSerializeFilename)
		contentSaveFilename = os.path.join(self.MasterPlaylistFolder, 'content.ts')
		if os.path.exists(contentSaveFilename):
			os.remove(contentSaveFilename)
		segmentCounter = 0
		for oneSegment in segments:
			try:
				# oneSegment is a dictionary looking like this: { 'segmentUrl': segmentUrl, 'segmentFullPath': segmentFullPath }
				segmentData = self.Recordings.ZapiSession.request_url_noExceptionCatch(oneSegment['segmentUrl'], None)
				# Note the 'wb' coz it's binary
				#with open(oneSegment['segmentFullPath'], 'wb') as segmentOutputStream:
				#	segmentOutputStream.write(segmentData)
				with open(contentSaveFilename, 'ab') as segmentOutputStream:
					segmentOutputStream.write(segmentData)
				segmentCounter += 1
				downloadProgress.DownloadedSegments = segmentCounter
				downloadProgress.serialize(downloadProgressSerializeFilename)
			except Exception as ex:
				downloadProgress.LastStatus = 'error'
				downloadProgress.Error = `ex`
				downloadProgress.serialize(downloadProgressSerializeFilename)
				return
			
	def get_valid_filename(self):
		 validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)
		 filename = ''.join(c for c in self.Title if c in validFilenameChars)
		 return filename

	def createMasterPlaylistFolder(self):
		self.MasterPlaylistFolder = self.get_valid_filename()
		self.MasterPlaylistFolder = os.path.join(self.DownloadRootFolder, self.MasterPlaylistFolder)
		if not os.path.exists(self.MasterPlaylistFolder):
			os.makedirs(self.MasterPlaylistFolder)
