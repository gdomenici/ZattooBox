# coding=utf-8

##################################
# ZattooBox extension
# RecordingDownloadProgress
# (c) 2014-2016 Pascal Nançoz; Guido Domenici
##################################


class RecordingDownloadProgress:
	Title = None
	DownloadedSegments = None
	TotalSegments = None
	LastStatus = None
	ErrorMessage = None
	
	def __init__ (self, title, totalSegments):
		self.Title = title
		self.DownloadedSegments = 0
		self.TotalSegments = totalSegments
		self.lastStatus = 'OK'
	
	def getProgressPercentage():
		return (self.DownloadedSegments / self.TotalSegments) * 100

