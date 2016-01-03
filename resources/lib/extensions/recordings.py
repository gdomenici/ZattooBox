# coding=utf-8

##################################
# ZattooBox extension
# Recordings
# (c) 2014-2015 Pascal Nançoz
##################################

from resources.lib.core.zbextension import ZBExtension
from resources.lib.core.zbfolderitem import ZBFolderItem
from resources.lib.core.zbdownloadableitem import ZBDownloadableItem
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
			thread.start_new_thread(self.downloadPlaylist, ( url, args['title'] ))
			
	'''
		Async functions
	'''
	def downloadPlaylist(self, url, title):
		playlist = self.ZapiSession.request_url(url, None)
		playlistStream = StringIO.StringIO(playlist)
		line = playlistStream.readline()
		highestBitrate = 0
		streams = {}
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
					break
				variantUrl = urlparse.urljoin(url, variantUrl)
				streams[bitrate] = { 'variantUrl': variantUrl, 'extXStream': line }
				if bitrate > highestBitrate:
					highestBitrate = bitrate
			line = playlistStream.readline()
		# Now operate only on the highest bitrate stream
		# Create a new master playlist
		masterPlaylistFilename = self.get_valid_filename(title) + '.m3u8'
		masterPlaylistFilename = os.path.join(self.ZBProxy.StoragePath, masterPlaylistFilename)
		with open(masterPlaylistFilename, 'w') as playlistOutputStream:
			playlistOutputStream.write('#EXTM3U\n')
			playlistOutputStream.write(streams[highestBitrate]['extXStream']) # this one already has \n at the end
			rewrittenVariantUrl = `highestBitrate` + '.m3u8'
			playlistOutputStream.write(rewrittenVariantUrl + '\n')
		# Start downloading highest variant and its segments
		self.downloadVariantPlaylist(streams[highestBitrate]['variantUrl'], highestBitrate)
		
	def downloadVariantPlaylist(self, url, bitrate):
		playlist = self.ZapiSession.request_url(url, None)
		playlistInputStream = StringIO.StringIO(playlist)
		variantPlaylistDumpFile = os.path.join(self.ZBProxy.StoragePath, `bitrate` + ".m3u8")
		line = playlistInputStream.readline()
		segments = []
		with open(variantPlaylistDumpFile, 'w') as playlistOutputStream:
			while line != '':
				# non-segment lines are rewritten verbatim
				playlistOutputStream.write(line)
				if line.startswith('#EXTINF:'):
					# read next line, containing URL
					segmentUrl = playlistInputStream.readline()
					if segmentUrl == '': # shouldn't happen but you never know
						break
					segmentUrl = urlparse.urljoin(url, segmentUrl)
					#segmentData = self.ZapiSession.request_url(segmentUrl, None)
					segmentCounter = len(segments)
					segmentFilename = `segmentCounter` + '.ts'
					# rewrite segment URL as local filename URL
					playlistOutputStream.write(segmentFilename + '\n')
					segmentFullPath = os.path.join(self.ZBProxy.StoragePath, segmentFilename)
					segments.append( { 'segmentUrl': segmentUrl, 'segmentFullPath': segmentFullPath } )
				line = playlistInputStream.readline()
		xbmc.log('There are this many segments to download:')
		xbmc.log(str(len(segments)))
		'''
		# Next: download all segments
		for oneSegment in segments:
			# oneSegment is a dictionary looking like this: { 'segmentUrl': segmentUrl, 'segmentFullPath': segmentFullPath }
			segmentData = self.ZapiSession.request_url_noExceptionCatch(oneSegment['segmentUrl'], None)
			# Note the 'wb' coz it's binary
			with open(oneSegment['segmentFullPath'], 'wb') as segmentOutputStream:
				segmentOutputStream.write(segmentData)
			#time.sleep(.1)
		'''
			
	def get_valid_filename(self, title):
		 validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)
		 filename = ''.join(c for c in title if c in validFilenameChars)
		 return filename
