# coding=utf-8

##################################
# ZattooBox extension
# RecordingDownloadProgress
# (c) 2014-2016 Pascal Nançoz; Guido Domenici
##################################

import json

class RecordingDownloadProgress:
	Title = None
	DownloadedSegments = None
	TotalSegments = None
	LastStatus = None
	ErrorMessage = None
	
	def __init__(self, title, totalSegments):
		self.Title = title
		self.DownloadedSegments = 0
		self.TotalSegments = totalSegments
		self.LastStatus = 'OK'

	def deserialize(self, fromFilename):
		with open(fromFilename, 'r') as f:
			self.__dict__ = json.loads(f.read())
		
	def getProgressPercentage(self):
		return (self.DownloadedSegments / self.TotalSegments) * 100

	def serialize(self, toFilePath):
		with open(toFilePath, 'w') as f:
			f.write(json.dumps(self.__dict__))
