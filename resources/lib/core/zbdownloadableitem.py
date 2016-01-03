# coding=utf-8

##################################
# ZattooBox Downloadable item
# 
# (c) 2014-2016 Pascal Nançoz; Guido Domenici
##################################

from resources.lib.core.zbplayableitem import ZBPlayableItem
import xbmcgui
import xbmc
import urllib

class ZBDownloadableItem(ZBPlayableItem):
	Title2 = None
	ContextMenuArgs = None

	def __init__(self, host, args, title, image, title2, contextMenuArgs):
		super(ZBDownloadableItem, self).__init__(host, args, title, image, title2)
		self.ContextMenuArgs = contextMenuArgs

	def get_listItem(self):
		li = super(ZBDownloadableItem, self).get_listItem()
		# Now add context menu entries
		downloadMenuText = self.Host.ZBProxy.get_string(30103) # "Download"
		downloadMenuUrl = self.get_context_menu_url()
		xbmc.log ('downloadMenuUrl is:')
		xbmc.log (downloadMenuUrl)
		li.addContextMenuItems(
			[(downloadMenuText, "RunPlugin(" + downloadMenuUrl + ")")])
		return li
		
	def get_context_menu_url(self):
		return 'ext=%s&%s' % (type(self.Host).__name__, urllib.urlencode(self.ContextMenuArgs))
	