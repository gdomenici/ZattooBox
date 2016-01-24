# coding=utf-8

##################################
# ZattooBox extension
# RecordingDownloader
# (c) 2014-2016 Pascal Nançoz; Guido Domenici
##################################

from recordingdownloadprogress import RecordingDownloadProgress
import os
import threading
import urlparse
import xbmc
import StringIO
import string
import time
import json

class RecordingDownloader:
	Url = None
	Title = None
	Recordings = None
	RootFolderForDownloads = None
	ContentDownloadFolder = None
	
	def __init__ (self, url, title, recordings):
		self.Url = url
		self.Title = title
		self.Recordings = recordings
		self.RootFolderForDownloads = os.path.join(self.Recordings.ZapiSession.CACHE_FOLDER, 'Downloads')
		
	def startDownload(self):
		self.createMasterPlaylistFolder()
		# First read and parse the master playlist, in order to extract info about the
		# highest bitrate
		highestVariantStream = self.readMasterPlaylist()
		# Start reading and parsing the highest variant playlist. The highestVariantStream
		# dict looks like this:
		# { 'variantUrl': variantUrl, 'extXStream': line, 'bitrate': bitrate }
		segments = self.readVariantPlaylist(highestVariantStream['variantUrl'], highestVariantStream['bitrate'])
		# segments is an array of dict that looks like this:
		# { 'segmentUrl': segmentUrl }
		
		# Serialize segments
		segmentsSerializeFilename = os.path.join(self.ContentDownloadFolder, 'segments.dat')
		with open(segmentsSerializeFilename, 'w') as f:
			f.write(json.dumps(segments))

		# Start downloading the actual streams, asynchronously.
		newThread = threading.Thread(
			name = 'pippo',
			target = self.downloadSegments,
			args = (segments ,) )
		newThread.run()

	def resumeDownload(self):
		# Deserialize segments
		segmentsSerializeFilename = os.path.join(self.ContentDownloadFolder, 'segments.dat')
		with open(segmentsSerializeFilename, 'r') as f:
			segments = json.loads(f.read())
		newThread = threading.Thread(
			name = 'pluto',
			target = self.downloadSegments,
			args = (segments , True) ) # True == resume
		newThread.run()
		
	def readMasterPlaylist(self):
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
		return variantStreams[highestBitrate]
		
	def readVariantPlaylist(self, variantUrl, bitrate):
		"""
		Returns an array of a dict that looks like this:
		{ 'segmentUrl': segmentUrl }
		"""
		playlist = self.Recordings.ZapiSession.request_url(variantUrl, None)
		playlistInputStream = StringIO.StringIO(playlist)
		line = playlistInputStream.readline()
		segments = []
		while line != '':
			# non-segment lines are rewritten verbatim
			if line.startswith('#EXTINF:'):
				# read next line, containing URL
				segmentUrl = playlistInputStream.readline()
				if segmentUrl == '': # shouldn't happen but you never know
					break
				segmentUrl = urlparse.urljoin(variantUrl, segmentUrl)
				segments.append( { 'segmentUrl': segmentUrl } )
			line = playlistInputStream.readline()
		return segments

	def downloadSegments (self, segments, resume = False):
		segmentCount = len(segments)
		xbmc.log('There are this many segments to download:')
		xbmc.log(str(segmentCount))
		# Next: download all segments
		downloadProgressSerializeFilename = os.path.join(self.ContentDownloadFolder, 'downloadProgress.dat')
		startIndex = 0
		if resume:
			downloadProgress = RecordingDownloadProgress(None, 0)
			downloadProgress.deserialize(downloadProgressSerializeFilename)
			startIndex = downloadProgress.DownloadedSegments
		else:
			downloadProgress = RecordingDownloadProgress(self.Title, segmentCount)
			downloadProgress.serialize(downloadProgressSerializeFilename)
		contentSaveFilename = os.path.join(self.ContentDownloadFolder, 'content.ts')
		if os.path.exists(contentSaveFilename):
			os.remove(contentSaveFilename)
		segmentCounter = 0
		for oneSegment in segments:
			if resume:
				# Skip enough segments until we reach the resume point
				if segmentCounter < startIndex:
					segmentCounter += 1
					continue
			try:
				# oneSegment is a dictionary looking like this: { 'segmentUrl': segmentUrl }
				segmentData = self.Recordings.ZapiSession.request_url(oneSegment['segmentUrl'], None, False) # False = don't swallow exception
				# Note the 'wb' coz it's binary
				with open(contentSaveFilename, 'ab') as segmentOutputStream:
					segmentOutputStream.write(segmentData)
				segmentCounter += 1
				downloadProgress.DownloadedSegments = segmentCounter
				downloadProgress.LastUpdated = time.time()
				downloadProgress.serialize(downloadProgressSerializeFilename)
			except Exception as ex:
				downloadProgress.LastStatus = 'error'
				downloadProgress.ErrorMessage = `ex`
				downloadProgress.serialize(downloadProgressSerializeFilename)
				return
			if xbmc.abortRequested:
				xbmc.log('KODI exiting during download - stop downloading')
				return
			
	def get_valid_filename(self):
		 validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)
		 filename = ''.join(c for c in self.Title if c in validFilenameChars)
		 return filename

	def createMasterPlaylistFolder(self):
		self.ContentDownloadFolder = self.get_valid_filename()
		self.ContentDownloadFolder = os.path.join(self.RootFolderForDownloads, self.ContentDownloadFolder)
		if not os.path.exists(self.ContentDownloadFolder):
			os.makedirs(self.ContentDownloadFolder)
