import xbmc
import xbmcaddon
import threading
import xbmcgui

if __name__ == '__main__':
	monitor = xbmc.Monitor()

	while not monitor.abortRequested():
		# Note that waitForAbort wants seconds
		if monitor.waitForAbort(30):
			# Abort was requested while waiting. We should exit
			break
		'''
		myWin = xbmcgui.Window(10025)
		pippo = myWin.getProperty('pippo')
		xbmc.log('pippo is ' + pippo if pippo is not None else 'not defined')
		'''