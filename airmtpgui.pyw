#!/usr/bin/env python

#
#############################################################################
#
# airnef.py - Wireless file transfer for PTP/MTP-equipped cameras (GUI app)
# Copyright (C) 2015, testcams.com
#
# This module is licensed under GPL v3: http://www.gnu.org/licenses/gpl-3.0.html
#
# Camera bitmap courtesy of rg1024 at https://openclipart.org/detail/20364/cartoon-camera
# Computer bitmap courtesy of lnasto at https://openclipart.org/detail/171010/computer-client
# Icon courtesy of Paomedia at https://www.iconfinder.com/icons/285680/camera_icon,
#     licensed under Creative Commons (Attribution 3.0 Unported)
#
# note001 - The Tkinter implementation on OSX has a behavior/bug where it doesn't vertically
# center the image specified for a button if the button also has text. (it horizontally centers
# but not vertically). This makes the button look ugly for ipady because all the padding
# goes to the bottom instead of being evenly distributed. I work arond this by massaging
# the padding when we're running on iOSX
#
#############################################################################
#

from __future__ import print_function
from __future__ import division
#
# six.py's remapping works as intended under Python 2.x but PyInstaller doesn't know how
# handle its remapping yet, so when running on Python 2.x I  always use the standard
# Python 2.x imports, just in case I'm performing a PyInstaller build, which I happen
# to doing under Python 2.x.
#
import six
if six.PY2:
	from Tkinter import *
	from ScrolledText import *
	from tkFont import *
	import ttk
	import tkFileDialog
	import tkMessageBox
else:	
	from six.moves.tkinter import *
	from six.moves.tkinter_font import *
	from six.moves.tkinter_scrolledtext import *
	from six.moves import tkinter_ttk as ttk
	from six.moves import tkinter_tkfiledialog as tkFileDialog
	from six.moves import tkinter_messagebox as tkMessageBox
import time
import subprocess
import os
import errno
import platform
import json
import datetime
import signal
import sys

#
# constants
#
AIRNEF_APP_VERSION	= "1.1"
buttonBgColor = "#E8E8E8"
mainBgColor = "#E0E0E0"
toolbarColor = "#B0B0B0"
LoggingLevelChoices = ['normal', 'verbose', 'debug']
RealtimeTransferUserReadableChoices = [ 'none - exit after normal download', 'normal download then realtime', 'only realtime download' ]
RealtimeTransferUserReadableChoicesToAirnefCmdOtion = { # converts a RealtimeTransferUserReadableChoices choice to the equivalent airnefcmd command line option
	'none - exit after normal download' : '--realtimedownload disabled',
	'normal download then realtime' : '--realtimedownload afternormal',
	'only realtime download' : '--realtimedownload only'
}
IfExistsUserReadableChoices = ['generate unique filename', 'overwrite file', 'skip file', 'prompt for each file', 'exit']
IfExistsUserReadableChoicesToAirnefCmdOption = { # converts a IfExistsUserReadableChoices choice to the equivalent airnefcmd command line option
	'generate unique filename' : '--ifexists uniquename',
	'overwrite file' : '--ifexists overwrite',
	'skip file' : '--ifexists skip',
	'prompt for each file' : '--ifexists prompt',
	'exit' : '--ifexists exit'
}
ActionsUserReadableChoices = ['full-sized images/movies', 'small thumbnails', 'large thumbnails']
ActionsUserReadableChoicesToAirnefCmdOption = { # converts a ActionsUserReadableChoices choice to the equivalent airnefcmd command line option
	'full-sized images/movies' : '--action getfiles',
	'small thumbnails' : '--action getsmallthumbs',
	'large thumbnails' : '--action getlargethumbs',
}
CardSlotUserReadableChoices = ['first card found', 'card in slot #1', 'card in slot #2', 'both cards (not recommended)']
CardSlotUserReadableChoicesToAirnefCmdOption = { # converts a CardSlotUserReadableChoices choice to the equivalent airnefcmd command line option
	'first card found' : '--slot firstfound',
	'card in slot #1' : '--slot first',
	'card in slot #2' : '--slot second',
	'both cards (not recommended)' : '--slot both'
}
TransferOrderReadableChoices = [ 'oldest images/movies first', 'newest images/movies first']
TransferOrderReadableChoicesToAirnefCmdOption = { #converts a TransferOrderReadableChoices choice to the equivalent airnefcmd command line option
	'oldest images/movies first' : '--transferorder oldestfirst',
	'newest images/movies first' : '--transferorder newestfirst'
}
DownloadDateChoices = [ 'All Dates', 'today', 'yesterday', 'past week', 'past month', 'past year', 'custom date range']
	
#
# structures
#
class GlobalVarsStruct:
	def __init__(self):
		self.isWin32 = None			# True if we're running on a Windows platform
		self.isOSX = None			# True if we're runnong on an OSX platform
		self.isFrozen = None		# True if we're running in a pyintaller frozen environment (ie, built as an executable)
		self.appDir = None			# directory where script is located. this path is used to store all metadata files, in case script is run in different working directory
		self.appDataDir = None		# directory where we keep app metadata
		self.appResourceDir = None	# directory where we keep app resources (read-only files needed by app, self.appDir + "resouce")
		self.app = None				# reference to main Application class

#
# global variables
#
root = None		# Tk root
g = GlobalVarsStruct()


#
#############################################################################
#
# OSX workarounds for running in "frozen" app
#
# We use py2app to generate the OSX executable bundle. Unfortunately there are some limitations
# and odd behavior when running under this environment:
#
# * py2app only supports one python-generated executable per application gundle
# * py2app only supports GUI apps, and the environment created doesn't natively support launching airnefcmd
# * Our GUI app always launches as minimized. Every workaround to fix this causes even worse side-effects,
# such modal windows no longer functioning correctly. Update: Finally resolved this - it's something
# with py2app's argv_emulation logic. I disabled it since we don't use it and it resolved the issue.
#
# The workaround for not being able to encode airnefcmd as a native OSX app nor the ability
# to launch it in a terminal window is pretty bad. I use the OSX "open" command to launch
# our python airnefcmd script - unfortunately Terminal doesn't propagate the --args to the python
# app, so to work around that I have to write the arguments to a file. The second gotcha is that
# open's -W wait parameter doesn't work when executed through the Terminal app, which breaks the logic
# of this module waiting for airnefcmd.py to complete before presenting the output log to the user. The
# work-around for this ugly - I use the creation of files as a signaling mechanism between this module
# and airnefcmd - to keep this ugliness out of airnefcmd itself I created a new wrapper module named
# airnefcmd_OSX_Frozen_Wrapper.py - that module handles reading the cmd-line args we encode in a file
# and also the lame file-communication mechanism. To detect the termination of the wrapper/airnefcmd
# outside of the normal completion/ctrl-c the wrapper writes its process ID to the notify-start file
# and we monitor that ID to detect if the process is killed - this is necessary because the process
# created by Popen on open(Terminal) completes immediately, so we can't wait on that process ID.
#
# A more elegant IPC mechanism like a shared mem seg or pipes would be better for communication but
# I'm hoping this entire method can eventually be removed once I find a better way to launch a Terminal.
#	
def osxFrozenWorkaround_deleteWrapperCommunicationFile(filename):
	# deletes a file we're using to communicate with airnefcmd_OSX_Frozen_Wrapper.py
	if os.path.exists(filename):
		os.remove(filename)

def osxFrozenWorkaround_waitWrapperCommunicationFileExist(filename, maxWaitTimeSecs=sys.maxsize, processIdCheckTermination=None):
	# waits for airnefcmd_OSX_Frozen_Wrapper.py to create a file to signal the start or completion of airnefcmd.py
	timeStart = time.time()
	while not os.path.exists(filename):
		if time.time() - timeStart >= maxWaitTimeSecs:
			return True
		if processIdCheckTermination:
			try:
				groupId = os.getpgid(processIdCheckTermination)
			except OSError as e:
				if e.errno == errno.ESRCH:
					if not os.path.exists(filename): # exclude race condition between us checking file vs process ID (only for print purposes - doesn't really matter otherwise)
						print("airnefcmd wrapper termination detected")
					return False
		time.sleep(0.5)
	return False

def osxFrozenWorkaround_readWrapperCommunicationFile(filename):
	fo = open(filename, "r")
	data = fo.read()
	fo.close()
	return data

#
# launches airnefcmd via airnefcmd_OSX_Frozen_Wrapper and waits for the completion
#	
def osxFrozenWorkaround_LaunchAirnefcmdWrapper(argStr):

	FILENAME_CMD_OPTS		= os.path.join(g.appDataDir, "airnefcmd-osxfrozen-cmdopts")		# file we encode options for the wrapper to read
	FILENAME_NOTIFY_START	= os.path.join(g.appDataDir, "airnefcmd-osxfrozen-notifystart") # file created by wrapper to signal it's started running
	FILENAME_NOTIFY_DONE	= os.path.join(g.appDataDir, "airnefcmd-osxfrozen-notifydone")	# file created by wrapper to signal when airnefcmd is done

	#
	# write options to temporary file
	# 
	fo = open(FILENAME_CMD_OPTS, 'w')
	argList = createArgListFromArgStr(argStr)
	for arg in argList:
		fo.write(arg + "\n")
	fo.close()

	#
	# launch the OSX frozen wrapper for a airnefcmd.py. delete
	# any leftover notify-start/notify-done files, which shouldn't exist
	# but just in case the wrapper didn't execute properly last time
	#
	osxFrozenWorkaround_deleteWrapperCommunicationFile(FILENAME_NOTIFY_START)
	osxFrozenWorkaround_deleteWrapperCommunicationFile(FILENAME_NOTIFY_DONE)
	process = subprocess.Popen(['open', '-a', 'Terminal.app', os.path.join(g.appDir, 'airnefcmd_OSX_Frozen_Wrapper.py')])

	#
	# make sure the wraper launched by checking the notify-start file was created by the wrapper.
	# this is to make sure we don't sit forever on systems where for some reasons the workaround
	# via the wrapper is not functioning properly
	#
	if osxFrozenWorkaround_waitWrapperCommunicationFileExist(FILENAME_NOTIFY_START, 5):
		tkMessageBox.showwarning("airnefcmd launch error", "Launch of airnefcmd was unsuccessful")
		return 1
	processIdWrapper = int(osxFrozenWorkaround_readWrapperCommunicationFile(FILENAME_NOTIFY_START))

	#
	# wait for completion of airnefcd, which is signified by the wrapper creating the notify-done file.
	# the file created by the wrapper actually contains the exit code from airnefcmd but since we're
	# not presently using that code I don't bother to read and return it
	#
	osxFrozenWorkaround_waitWrapperCommunicationFileExist(FILENAME_NOTIFY_DONE, processIdCheckTermination=processIdWrapper)

	return 0 

	
#
# creates a list of arguments from an argument string, honoring quoted args as a single argument
#	
def createArgListFromArgStr(argStr):
	return [x.strip('"') for x in re.split('( |".*?")', argStr) if x.strip()]


#
# spanws airnefcmd with specified arguments. returns errno
# that airnefcmd exited with
#
def launchAirnefcmd(argStr):

	#
	# launch airnefcmd and wait for its comletion
	#
	print("Launching airnefcmd with args: ", argStr)
	try:
	
		root.withdraw() # make our main GUI window invisible while running airnefcmd

		process = None
		argList = createArgListFromArgStr(argStr)
		if g.isFrozen:
			if g.isOSX:
				_errno = osxFrozenWorkaround_LaunchAirnefcmdWrapper(argStr)
			elif g.isWin32:
				process = subprocess.Popen([os.path.join(g.appDir, 'airnefcmd.exe')] + argList)
			else: # linux
				process = subprocess.Popen(['xterm', '+hold', '-e', os.path.join(g.appDir, 'airnefcmd')] + argList)
		else:
			process = subprocess.Popen(['python', os.path.join(g.appDir, 'airnefcmd.py')] + argList)

		if process:
			_errno = process.wait()
			
	except KeyboardInterrupt as e:
		print("SIGINT received while waiting for airnefcmd to complete")
		if process:
			#
			# both airnef and airnefcmd rceive the SIGINT. make sure airnefcmd
			# has completed processing its SIGTERM by waiting for it to exit
			#
			if process.poll() == None:
				print("waiting for airnefcmd to finish handling its SIGINT")
				process.wait()
		_errno = errno.EINTR
	finally:
		root.deiconify() # bring our main GUI window back
		
	#
	# display airnefcmd output
	#
	displayAirnefcmdOutput()
	return _errno
			
			
#
# displays a top-level window the last output from airnefcmd
#			
def displayAirnefcmdOutput():

	#
	# load report
	#
	mostRecentAirnefReportFilename = os.path.join(g.appDataDir, "airnefcmd-log-last.txt")
	if not os.path.exists(mostRecentAirnefReportFilename):
		tkMessageBox.showwarning("airnef Transfer Report", "No airnefcmd operations have been performed yet")
		return
	fileReport = None
	try:
		fileReport = open(mostRecentAirnefReportFilename, "r")
		reportContents = fileReport.read()
	except IOError as e:
		tkMessageBox.showerror("airnef Transfer Report", "Error reading airnefcmd report file \"{:s}\". {:s}".format(mostRecentAirnefReportFilename, str(e)))
		return
	finally:
		if fileReport:
			fileReport.close()

	#
	# detect an unclean shutdown of airnefcmd by checking if the logfile is either
	# empty (no data flushed before termation) or is missing the final "session over"
	# message (last set of message(s) not flushed).
	#
	if reportContents:
		# file not empty
		posSessionOverMessage = reportContents.find(">>>> airnefcmd session over")
	else:
		posSessionOverMessage = -1	
	if posSessionOverMessage == -1:
		g.app.showQuickTip('airnefcmd_unclean_shutdown', 1,
			"It appears airnefcmd was uncleanly terminated. In the future please press <ctrl-c> if "\
			"you'd like to terminate airnefcmd instead of closing its terminal window. This will "\
			"allow airnefcmd to perform any necessary cleanup prior to exiting.")
		if not reportContents:
			# log file is empty so no point in presenting window with contents
			return
	reportContents = reportContents[:posSessionOverMessage] # trim off ">>>> airnefcmd session over ...." message

	if g.isOSX and g.isFrozen:
		g.app.showQuickTip('osx_terminal_auto_close', 4,
			"airnef performs its job by launching airnefcmd in a terminal window. By default OSX "\
			"keeps that terminal window open even after airnefcmd has completed, requiring you to "\
			"to close it manually. You can configure OSX to close the terminal window automatically. "\
			"Go to the Terminal application and select 'Preferences' in the Terminal menu. " \
			"Click 'Profiles' at the top and then the \"Shell\" tab in the upper part of the window. "\
			"Set \"When the shell exits\" option to 'Close if the shell exited cleanly' or 'Close "\
			"the window'")
	
	#
	# create top-level window
	#
	topLevelFrame = Toplevel(root)
	topLevelFrame.geometry('900x420')
	topLevelFrame.title("airnef Transfer Report")
	setFrameIcon(topLevelFrame)
	
	#
	# fill window with text control to hold report and some buttons
	#
	scrolledText = ScrolledText(topLevelFrame, bg='yellow', width=80)
	# text widgets can't be set read-only without disabling them, so achieve the same by disabling all keypresses except ctrl-c (to allow copy)
	scrolledText.bind("<Control-c>", lambda e : "")	# on ctrl-c, invoke function that returns empty string, allowing the default ahndler to process the ctrl-c copy operations
	scrolledText.bind('<Key>', lambda e: "break")		# on all other keys, invoke function that returns "break", preventing the keypress from being handled
	
	buttonFrame = Frame(topLevelFrame)	
	button = Button(buttonFrame, text="Ok", command=lambda : topLevelFrame.destroy())
	button.grid(column=0, row=0, padx=10, pady=5, ipadx=40, ipady=5)
	button.focus_set()
	button = Button(buttonFrame, text="Copy to Clipboard", command=lambda : [root.clipboard_clear(), root.clipboard_append(reportContents)])
	button.grid(column=2, row=0, padx=80, pady=5, ipady=5, ipadx=8)
	buttonFrame.pack(side=BOTTOM)
	scrolledText.pack(side=TOP, fill=BOTH, expand=1) # packed last to give other controls real estate in frame

	# insert report into text control and move cursor to the end
	scrolledText.insert(END, reportContents)
	scrolledText.see(END)
	
	
	#
	# present top-level window as modal and wait for it to be dismissed
	#
	topLevelFrame.transient(root)
	topLevelFrame.grab_set()
	bringAppToFront()
	root.wait_window(topLevelFrame)

	
#
# brings our app window(s) to the front of the OS's window z-order
#	
def bringAppToFront():	
	# fix for bringing our app to front on OS X
	root.lift()
	root.call('wm', 'attributes', '.', '-topmost', True)
	root.after_idle(root.call, 'wm', 'attributes', '.', '-topmost', False)			

#
# sets the icon for the given window/frame
# 	
def setFrameIcon(frame):
	if g.isWin32:
		frame.wm_iconbitmap(bitmap = os.path.join(g.appResourceDir, 'airnef.ico'))
	else:
		frame.wm_iconbitmap(bitmap = '@' + os.path.join(g.appResourceDir, 'airnef.xbm'))
	
	
	

#
# main application Tkinter class
#	
class Application(Frame):

	#
	# root -> Application(Frame)	-> Menu
	#								-> ToolBar
	#								-> ContentFrame
	#
	# instance variables
	#	
	# self.toolbarFrame
	# self.wizard_BackNavigationToolbarButton
	# self.toolbar_IpAdressEntry
	# self.toolbar_RealtimeDownloadComboBox
	# self.toolbar_LoggingLevelComboBox
    #
	# self.contentFrame
	# self.contentAreaLabel
	# self.fontWizardQuestion14
	# self.resource_PhotoDict
	# self.wizard_SkipFilesInDownloadHistoryCheckboxIntVar
	# self.wizard_common_OutputDirComboBox
	# self.wizard_common_IfFileExistsComboBox
	# self.wizard_2_0_ActionComboBox
	# self.wizard_2_0_CardSlotComboBox
	# self.wizard_2_0_TransferOrderComboBox
	# self.wizard_2_0_DateSelectionComboBox
	# self.wizard_2_0_CustomDateRangeStartEntry
	# self.wizard_2_0_CustomDateRangeEndEntry
	# self.wizard_2_0_FileExt_NEF_IntVar
	# self.wizard_2_0_FileExt_JPG_IntVar
	# self.wizard_2_0_FileExt_MOV_IntVar
	# self.wizard_2_0_FileExt_CR2_IntVar	
	# self.wizard_2_0_FileExt_ARW_IntVar	
	# self.wizard_2_0_FileExtMoreEntry
	# self.wizard_2_0_AdditionalArgsEntry
	

	def __init__(self, master):
	
		Frame.__init__(self, master, bg=mainBgColor)

		root.title("airnef - Wirelessly download images and movies from your Nikon Camera")
		setFrameIcon(root)
		
		# resources
		self.fontWizardQuestion14 = Font(family="Helvetica", size=14, weight=BOLD, slant=ITALIC)
		self.resource_PhotoDict = {}
		
		# load config from previous session(s). this contains previous user choices, which
		# will be the defaults for each repesective wizard/form element.
		self.loadAppConfig()

		# top-level menu
		self.createTopLevelMenu()
		
		# toolbar
		self.toolbarFrame = Frame(self, bg=toolbarColor)
		
		# toolbar - Last Transfer Report button
		button = Button(self.toolbarFrame, text="Last Transfer Report", command=lambda : self.toolbarClick('transfer_report'))
		button.pack(side=LEFT, padx=10, pady=5, ipadx=10)
		
		# toolbar - IP address label and entry field
		optionsFrame = Frame(self.toolbarFrame, bg=toolbarColor)
		label = Label(optionsFrame, text="Camera IP Address:", bg=toolbarColor)
		label.grid(column=0, row=0, sticky=E)
		entry = Entry(optionsFrame, bg=mainBgColor, width=16)
		if 'ip_address' in self.appConfigDict:
			entry.insert(0, self.appConfigDict['ip_address'])
		else:
			entry.insert(0, "192.168.1.1")
		entry.grid(column=1, row=0, sticky=W, padx=2)
		self.toolbar_IpAdressEntry = entry
		
		# toolbar - Real-time download label and combo box		
		label = Label(optionsFrame, text="Realtime download:", anchor=E, bg=toolbarColor)
		label.grid(column=2, row=0, sticky=W, ipadx=2)
		comboBox = ttk.Combobox(optionsFrame, values=RealtimeTransferUserReadableChoices, state='readonly', width=30)
		if 'realtime_download_choice' in self.appConfigDict:
			comboBox.current(comboBox['values'].index (self.appConfigDict['realtime_download_choice']))
		else:
			comboBox.current(0)
		comboBox.grid(column=3, row=0, sticky=W)
		self.toolbar_RealtimeDownloadComboBox = comboBox

		# toolbar - Logging level label and combo box		
		label = Label(optionsFrame, text="Logging:", bg=toolbarColor)
		label.grid(column=4, row=0, sticky=E, padx=2)
		comboBox = ttk.Combobox(optionsFrame, values=LoggingLevelChoices, state='readonly', width=8)
		if 'logging_level_choice' in self.appConfigDict:
			comboBox.current(comboBox['values'].index (self.appConfigDict['logging_level_choice']))
		else:
			comboBox.current(0)
		comboBox.grid(column=5, row=0, sticky=W, padx=10)
		self.toolbar_LoggingLevelComboBox = comboBox
		
		optionsFrame.pack(side=LEFT, padx=0, pady=5)
			
		self.wizard_BackNavigationToolbarButton = None
		self.toolbarFrame.pack(side=TOP, fill=X)
		
		# label between toolbar and main window area
		self.contentAreaLabel = Label(self, text="", font=self.fontWizardQuestion14, bg=mainBgColor)
		self.contentAreaLabel.pack(side=TOP, fill=X, pady=10)
		
		# main window area
		self.contentFrame = Frame(self, bg=mainBgColor)
		
		# first scene
		self.setContent_Wizard_0()
		self.pack(fill=BOTH, expand=1)
						
		bringAppToFront()
				
	def loadAppConfig(self):
		appConfigFilename = os.path.join(g.appDataDir, "airnef-gui1-config")
		self.appConfigDict = None
		try:
			if os.path.exists(appConfigFilename):
				f = open(appConfigFilename, "r")
				self.appConfigDict  = json.loads(f.read())
				f.close()
		except IOError as e:
			tkMessageBox.showwarning("Loading App Config", "Could not read app config data. {:s}. Defaults will be used.".format(str(e)))
		except ValueError as e:
			tkMessageBox.showwarning("Loading App Config", "Could not decode app config data. {:s}. Defaults will be used.")
		if not self.appConfigDict:
			self.appConfigDict = {}
		
	def saveAppConfig(self):
		appConfigFilename = os.path.join(g.appDataDir, "airnef-gui1-config")
		try:
			f = open(appConfigFilename, "w")
			f.write(json.dumps(self.appConfigDict))
			f.close()
		except IOError as e:
			tkMessageBox.showwarning("Saving App Config", "Could not write app config data. {:s}.".format(str(e)))
		except ValueError as e:
			tkMessageBox.showwarning("Saving App Config", "Could not encode  app config data. {:s}.")
				
	def showQuickTip(self, tipReference, numOccurrencesBeforePresentingTip, tipStr):
	
		#
		# this routine is used to present the user a tip/warning about using the app.
		# it is called from various places within the module based on where the app
		# determines the tip would be useful to know. 'tipReference' is only tag used
		# to track this particular tip. 'tipStr' is the contents of the tip itself.
		# 'numOccurrencesBeforePresentingTip' establishes how many times the tip
		# should be evaluated before presenting it to the user; for example, if the tip
		# is to inform the user about a faster way to accomplish an action, we might
		# wait until the 5th time the user performs the action before presenting the
		# tip. That way the user gets to use the program/action for a bit before being
		# bombarded with a bunch of tips. once the occurence threshold has been reached
		# the tip will be presented to the user and the record of the presentation will
		# be saved in appConfigDict so that the tip is never presented again
		#
	
		if 'quick_tips' in self.appConfigDict:
			# quick_tips dictionary exists - retrieve it
			quickTipsDict = self.appConfigDict['quick_tips']
		else:
			# this is the first quick tip check we're performing - create dictionary
			quickTipsDict = {}
		if tipReference in quickTipsDict:
			# we've previously evaluated this tip before
			if quickTipsDict[tipReference] >= numOccurrencesBeforePresentingTip:
				#  tip previously reached its occurence threshold and has already been presented to user
				return
			quickTipsDict[tipReference] = quickTipsDict[tipReference] + 1 # increase evaluation count for this tip
		else:
			# this is the first time we're evaluating this tip for presentation
			quickTipsDict[tipReference] = 1

		# we've updated the quick-tips dictionary - save it
		self.appConfigDict['quick_tips'] = quickTipsDict
		self.saveAppConfig()
		
		# present the tip to the user if we've reached its threshold
		if quickTipsDict[tipReference] >= numOccurrencesBeforePresentingTip:
			tkMessageBox.showinfo("airnef Quick Tip", tipStr)		
					
	def createTopLevelMenu(self):
	
		menubar = Menu(root)

		# file menu
		filemenu = Menu(menubar, tearoff=0)
		filemenu.add_command(label="Exit", command=root.quit)
		menubar.add_cascade(label="File", menu=filemenu)

		# help menu
		helpmenu = Menu(menubar, tearoff=0)
		helpmenu.add_command(label="About", command=lambda : tkMessageBox.showinfo("airnef", \
			"airnef - Version {:s}\n\nRunning under Python Version {:d}.{:d}.{:d}\n\nApplication is licensed under GPL v3\n\n"\
			"To report issues or for support please send an email to airnef@hotmail.com - the email must "\
			"include airnef-support in the title to be routed past my email spam filter.\n\n"\
			"Special thanks to Joe FitzPatrick for his work on reverse engineering Nikon's Wifi interface\n\n"\
			"Camera bitmap courtesy of rg1024 at https://openclipart.org/detail/20364/cartoon-camera\n\n"\
			"Computer bitmap courtesy of lnasto at https://openclipart.org/detail/171010/computer-client\n\n"\
			"Icon courtesy of Paomedia at https://www.iconfinder.com/icons/285680/camera_icon, licensed under Creative Commons (Attribution 3.0 Unported)"\
			.format(AIRNEF_APP_VERSION, sys.version_info.major, sys.version_info.minor, sys.version_info.micro)))
		menubar.add_cascade(label="Help", menu=helpmenu)

		root.config(menu=menubar)
		
	def clearContent(self):
		for widget in self.contentFrame.winfo_children():
			widget.destroy()
			
	def getResource_Image(self, filename):
	
		#
		# gets photo resource. returns the resource if it's previously been loaded,
		# otherwise we load it. we keep the reference in a dictionary, as required
		# because tKinter doesn't keep a reference itself and so without our
		# reference the image would be garbage collected
		#
	
		if filename in self.resource_PhotoDict:
			return self.resource_PhotoDict[filename]
		
		photo = PhotoImage(file = os.path.join(g.appResourceDir, filename))
		self.resource_PhotoDict[filename] = photo
		return photo

	def packContentFrame(self):
		self.contentFrame.pack(side=LEFT, fill=BOTH, expand=1)
		
	#########################################################################
	
	def setContent_Wizard_0(self):
	
		#
		# application's base wizard - user chooses whether to select images on camera or computer
		#
		self.clearContent()
		self.wizard_1_DisableBackNavigationButton()
		
		self.contentAreaLabel['text'] = "How would you like to choose which images to download?"
		
		leftFrame = Frame(self.contentFrame, bg=mainBgColor)	   
		button = Button(leftFrame, image=self.getResource_Image("camera_button_200x134.gif"), compound=TOP, text="Select in Camera", bg=buttonBgColor, command=lambda : self.wizard_0_ButtonClick('select_in_camera'))
		button.pack(side=LEFT, expand=1, ipadx=40, ipady=40 if not g.isOSX else 10, pady=30) # note001
		leftFrame.pack(side=LEFT, fill=BOTH, expand=1)

		rightFrame = Frame(self.contentFrame, bg=mainBgColor)
		button = Button(rightFrame, image=self.getResource_Image("computer_200x134.gif"), compound=TOP, text="Select on Computer", bg=buttonBgColor, command=lambda : self.wizard_0_ButtonClick('select_in_computer'))
		button.pack(side=RIGHT, expand=1,  ipadx=40, ipady=40 if not g.isOSX else 10, pady=30) # note001
		rightFrame.pack(side=RIGHT, fill=BOTH, expand=1)
		
		self.packContentFrame()
		
	def wizard_0_ButtonClick(self, str):
		if str == 'select_in_camera':
			self.setContent_Wizard_1_0()
		elif str == 'select_in_computer':
			self.setContent_Wizard_2_0()
		 
	def toolbarClick(self, str):
		if str == 'Wizard_1_Prev':
			self.setContent_Wizard_0()
		elif str == 'transfer_report':
			displayAirnefcmdOutput()

	def menuSelected(self, str):
		print("Menu: ", str)

	def createIfFileExistsLabelAndCombo(self, parentFrame):
		label = Label(parentFrame, text="If File(s) Exists:", bg=mainBgColor)
		comboBox = ttk.Combobox(parentFrame, values=IfExistsUserReadableChoices, state='readonly')
		if 'if_file_exists_choice' in self.appConfigDict:
			comboBox.current(comboBox['values'].index (self.appConfigDict['if_file_exists_choice']))
		else:
			comboBox.current(0)
		self.wizard_common_IfFileExistsComboBox = comboBox
		return (label, comboBox)

	def createSkipFilesInDownloadHistoryCheckbox(self, parentFrame):
		self.wizard_SkipFilesInDownloadHistoryCheckboxIntVar = IntVar()
		if 'skip_files_in_download_history_choice' in self.appConfigDict:
			self.wizard_SkipFilesInDownloadHistoryCheckboxIntVar.set(self.appConfigDict['skip_files_in_download_history_choice'])
		else:		
			self.wizard_SkipFilesInDownloadHistoryCheckboxIntVar.set(True)
		checkButton = Checkbutton(parentFrame, variable = self.wizard_SkipFilesInDownloadHistoryCheckboxIntVar, onvalue = True, text="Skip images/movies you've previously downloaded")
		return checkButton

	def createDownloadDirectoryLabel_ComboBox_Button(self, parentFrame):
		label = Label(parentFrame, text="Output Directory:", bg=mainBgColor)
		comboBox = ttk.Combobox(parentFrame, state='readonly')
		if 'outputdir_history' in self.appConfigDict:
			comboBox['values'] = self.appConfigDict['outputdir_history']
		else:
			# no saved directory in app config. select a default directory			
			defaultDir = os.getcwd() # default to last resort of current working directory, which is usually our application
			userFilesPath = None
			
			if g.isWin32:
				if os.environ['HOMEDRIVE'] and os.environ['HOMEPATH']:
					# user files path available
					userFilesPath = os.path.join(os.environ['HOMEDRIVE'], os.environ['HOMEPATH'])
			else:
				if os.environ['HOME']:
					# user files path available
					userFilesPath = os.environ['HOME']
			if userFilesPath:
				userFilesPath = os.path.abspath(userFilesPath)
				userPictureFilesPath = os.path.join(userFilesPath, 'Pictures')						
				if os.path.exists(userPictureFilesPath):
					# 'Pictures' exists, use it ('Pictures' is OSX and display folder name. For Win32 'My Pictures' goes to 'Pictures' as well
					defaultDir = userPictureFilesPath
				elif os.path.exists(userFilesPath):
					# user files path exists, use it
					defaultDir = userFilesPath
				
			comboBox['values'] = [ defaultDir ]
		comboBox.current(0)
		self.wizard_common_OutputDirComboBox = comboBox
		button = Button(parentFrame, text="More choices", command=lambda : self.changeDownloadDirectory_ButtonClick())
		return (label, comboBox, button)
		
	def createStartDownloadFrameAndButton_PackOnRightInParent(self, parentFrame, theCommand, buttonPady):
		rightFrame = Frame(self.contentFrame, bg=mainBgColor)
		button = Button(rightFrame, image=self.getResource_Image("wifi_200x134.gif"), compound=TOP, text="Start Download", bg=buttonBgColor, command=theCommand)
		button.pack(side=TOP, fill=BOTH, expand=1, ipadx=40, ipady=40 if not g.isOSX else 10, padx=40, pady=buttonPady) # note001
		rightFrame.pack(side=LEFT, fill=BOTH, expand=1)
		return rightFrame
		
	def setOutputDirListInAppConfig(self):
		outputDirList = list(self.wizard_common_OutputDirComboBox['values'])
		outputDirList.insert(0, outputDirList.pop(outputDirList.index(self.wizard_common_OutputDirComboBox.get())))			
		del outputDirList[32:] # limit size of dir history to 32 elements, otherwise it can get unwieldly)
		self.appConfigDict['outputdir_history'] = outputDirList			
		
	def changeDownloadDirectory_ButtonClick(self):
		dir_opt = { 'initialdir' : self.wizard_common_OutputDirComboBox.get(),	\
					'mustexist' : True,
					'title' : 'Select folder to download images/movies into'
					
			}
		newDir = tkFileDialog.askdirectory(**dir_opt)
		if newDir: # user selected a directory
			if g.isWin32:
				# askdirectory() converts paths to unix style. while these work on Windows,
				# they're confusing to see so convert it back
				newDir = newDir.replace('/', '\\')
			comboTuple = self.wizard_common_OutputDirComboBox['values']
			if newDir not in comboTuple:
				# user selected a directory that's not already in the combo list
				comboTuple = (newDir,) + comboTuple
				self.wizard_common_OutputDirComboBox['values'] = comboTuple
				self.wizard_common_OutputDirComboBox.current(0)
			else:
				# user selected a directory that's already in the combo list. make that the current selection
				self.wizard_common_OutputDirComboBox.current(comboTuple.index(newDir))

	def genAirnefArgs_OutputDir_SkipFilesInDownloadHistory_IfExistsCmdOtion(self):
		argStr = " --outputdir \"{:s}\"".format(self.wizard_common_OutputDirComboBox.get())
		if self.wizard_SkipFilesInDownloadHistoryCheckboxIntVar.get() == False:
			argStr += " --downloadhistory ignore"
		argStr += " " + IfExistsUserReadableChoicesToAirnefCmdOption[self.wizard_common_IfFileExistsComboBox.get()]
		return argStr

	def saveAppVersionToConigDict(self):
		self.appConfigDict['app_version'] = AIRNEF_APP_VERSION
		
	#########################################################################

	def setContent_Wizard_1_0(self):
	
		self.clearContent()
		self.wizard_1_EnableBackNavigationButton()
		
		self.contentAreaLabel['text'] = ("Download images you've selected in the camera")
		
		# instructions
		leftFrame = Frame(self.contentFrame, bg=mainBgColor, padx=20)
		label = Label(leftFrame, text="1. Turn your camera on and select which images you'd like to upload. This may be under the "\
			"camera's WiFi menu as \"Select to send to smart device\" or in the playback menu, depending on the camera model.", bg=mainBgColor, wraplength=300, justify=LEFT)
		label.grid(column=0, columnspan=3, row=0, sticky=W, padx=5, pady=5)
		label = Label(leftFrame, text="2. Make sure your Camera's WiFi is on. The camera may sometimes disable it without direction from the user.", bg=mainBgColor, wraplength=300, justify=LEFT)
		label.grid(column=0, columnspan=3, row=1, sticky=W, padx=5, pady=5)
		label = Label(leftFrame, text="3. Join your Camera's WiFi network on your computer. It will have a name prefixed with \"Nikon\", such as \"Nikon_WU2_0090B6245A45\".", bg=mainBgColor, wraplength=300, justify=LEFT)
		label.grid(column=0, columnspan=3, row=2, sticky=W, padx=5, pady=5)

		# output directory
		(label, comboBox, button) = self.createDownloadDirectoryLabel_ComboBox_Button(leftFrame)
		label.grid(column=0, row=3, sticky=E, pady=5)
		comboBox.grid(column=1, row=3, sticky=W, ipadx=50)
		button.grid(column=2, row=3, sticky=W, pady=5,  padx=5)
		comboBox.focus_set()

		# if file exists combobox
		(label, comboBox) = self.createIfFileExistsLabelAndCombo(leftFrame)
		label.grid(column=0, row=4, sticky=E, pady=5)
		comboBox.grid(column=1, row=4, sticky=W, ipadx=15)
				
		# skip files in download history checkbox
		checkButton = self.createSkipFilesInDownloadHistoryCheckbox(leftFrame)
		checkButton.grid(column=0, row=5, columnspan=3, sticky=W, ipady=4, ipadx=4, pady=5)
		
		#
		# done with left frame, pack it
		#
		leftFrame.pack(side=LEFT, fill=BOTH, expand=1)

		#
		# right frame
		#		
		
		# button to start download
		self.createStartDownloadFrameAndButton_PackOnRightInParent(self.contentFrame, lambda : self.wizard_1_0_ButtonClick('start_download_selected_in_camera'), 
			30 if not g.isOSX else (60,90)) # note001

		self.packContentFrame()		
	
	def wizard_1_EnableBackNavigationButton(self):
		if not self.wizard_BackNavigationToolbarButton:
			self.wizard_BackNavigationToolbarButton = Button(self.toolbarFrame, text="Prev <", fg="red", command=lambda : self.toolbarClick('Wizard_1_Prev'))
			self.wizard_BackNavigationToolbarButton.pack(side=RIGHT, padx=5, pady=5)
			
	def wizard_1_DisableBackNavigationButton(self):
		if	self.wizard_BackNavigationToolbarButton:
			self.wizard_BackNavigationToolbarButton.destroy()
			self.wizard_BackNavigationToolbarButton = None
						
	def wizard_1_0_ButtonClick(self, str):
		if str == 'start_download_selected_in_camera':
		
			#
			# save options in app config, so that they will be defaults next time
			#

			# app version
			self.saveAppVersionToConigDict()
			# ip address
			self.appConfigDict['ip_address'] = self.toolbar_IpAdressEntry.get()
			# logging level
			self.appConfigDict['logging_level_choice'] = self.toolbar_LoggingLevelComboBox.get()
			# realtime download
			self.appConfigDict['realtime_download_choice'] = self.toolbar_RealtimeDownloadComboBox.get()
			# output dir history. in addition to saving it we move the current selection to the front of the list (we keep list MRU to be intuitive)
			self.setOutputDirListInAppConfig()
			# if file exists action
			self.appConfigDict['if_file_exists_choice'] = self.wizard_common_IfFileExistsComboBox.get()
			# skip files in download history
			self.appConfigDict['skip_files_in_download_history_choice'] = self.wizard_SkipFilesInDownloadHistoryCheckboxIntVar.get()
			
			# save the config
			self.saveAppConfig()
			
			#
			# generate command line and launch airnefcmd
			#
			argStr = self.genAirnefArgs_OutputDir_SkipFilesInDownloadHistory_IfExistsCmdOtion()
			ipAddrStr = self.toolbar_IpAdressEntry.get()
			if ipAddrStr:
				argStr += " --ipaddress " + ipAddrStr
			argStr += " " + RealtimeTransferUserReadableChoicesToAirnefCmdOtion[self.toolbar_RealtimeDownloadComboBox.get()]
			argStr += " --logginglevel " + self.toolbar_LoggingLevelComboBox.get()
			argStr += " --cameratransferlist exitifnotavail"
			launchAirnefcmd(argStr)
		
	#########################################################################
		
	def setContent_Wizard_2_0(self):

		self.clearContent()
		self.wizard_1_EnableBackNavigationButton()
		self.contentAreaLabel['text'] = ("Set criteria for which images/movies to download")

		# what to get/action
		leftFrame = Frame(self.contentFrame, bg=mainBgColor, padx=15)
		label = Label(leftFrame, text="What to Get:", bg=mainBgColor)
		label.grid(column=0, row=0, sticky=E, pady=5)
		comboBox = ttk.Combobox(leftFrame, values=ActionsUserReadableChoices, state='readonly')
		if 'action_choice' in self.appConfigDict:
			comboBox.current(comboBox['values'].index (self.appConfigDict['action_choice']))
		else:
			comboBox.current(0)
		comboBox.grid(column=1, row=0, sticky=W, ipadx=10)
		comboBox.focus_set()
		self.wizard_2_0_ActionComboBox = comboBox
		
		#
		# file extension radio group
		#
		fileExtFrame = Frame(leftFrame, bg=mainBgColor, padx=15)
		label = Label(fileExtFrame, text="File Types:  ", bg=mainBgColor)
		label.grid(column=0, row=0, sticky=E)
		self.wizard_2_0_FileExt_NEF_IntVar = IntVar()
		checkButton = Checkbutton(fileExtFrame, variable = self.wizard_2_0_FileExt_NEF_IntVar, onvalue = True, text="NEF")
		checkButton.grid(column=1, row=0, sticky=W, ipadx=0, pady=5)		
		self.wizard_2_0_FileExt_JPG_IntVar = IntVar()
		checkButton = Checkbutton(fileExtFrame, variable = self.wizard_2_0_FileExt_JPG_IntVar, onvalue = True, text="JPG")
		checkButton.grid(column=2, row=0, sticky=W, ipadx=0, pady=5)		
		self.wizard_2_0_FileExt_MOV_IntVar = IntVar()
		checkButton = Checkbutton(fileExtFrame, variable = self.wizard_2_0_FileExt_MOV_IntVar, onvalue = True, text="MOV")
		checkButton.grid(column=3, row=0, sticky=W, ipadx=0, pady=5)
		self.wizard_2_0_FileExt_CR2_IntVar = IntVar()
		checkButton = Checkbutton(fileExtFrame, variable = self.wizard_2_0_FileExt_CR2_IntVar, onvalue = True, text="CR2")
		checkButton.grid(column=4, row=0, sticky=W, ipadx=0, pady=5)
		self.wizard_2_0_FileExt_ARW_IntVar = IntVar()
		checkButton = Checkbutton(fileExtFrame, variable = self.wizard_2_0_FileExt_ARW_IntVar, onvalue = True, text="ARW")		
		checkButton.grid(column=5, row=0, sticky=W, ipadx=0, pady=5)
		
		
		if 'file_exts' in self.appConfigDict:
			fileTypeList = self.appConfigDict['file_exts']
			self.wizard_2_0_FileExt_NEF_IntVar.set('NEF' in fileTypeList)
			self.wizard_2_0_FileExt_JPG_IntVar.set('JPG' in fileTypeList)
			self.wizard_2_0_FileExt_MOV_IntVar.set('MOV' in fileTypeList)
			self.wizard_2_0_FileExt_CR2_IntVar.set('CR2' in fileTypeList)
			self.wizard_2_0_FileExt_ARW_IntVar.set('ARW' in fileTypeList)
		else:		
			self.wizard_2_0_FileExt_NEF_IntVar.set(True)
			self.wizard_2_0_FileExt_JPG_IntVar.set(True)
			self.wizard_2_0_FileExt_MOV_IntVar.set(True)
			self.wizard_2_0_FileExt_CR2_IntVar.set(True)
			self.wizard_2_0_FileExt_ARW_IntVar.set(True)

		label = Label(fileExtFrame, text="More: ", bg=mainBgColor)
		label.grid(column=6, row=0)
		entry = Entry(fileExtFrame, bg=mainBgColor, width=10)
		entry.grid(column=7, row=0)		
		if 'file_exts_more' in self.appConfigDict:
			entry.insert(0, self.appConfigDict['file_exts_more'])
		self.wizard_2_0_FileExtMoreEntry = entry			
			
		fileExtFrame.grid(column=0, columnspan=8, row=1, padx=25, sticky=W)
		
		# date choice
		dateSelectFrame = Frame(leftFrame, bg=mainBgColor, padx=0)
		label = Label(dateSelectFrame, text="Capture Date:", bg=mainBgColor)
		label.grid(column=0, row=0, sticky=E, pady=5, padx=5)
		comboBox = ttk.Combobox(dateSelectFrame, values=DownloadDateChoices, state='readonly')
		self.wizard_2_0_DateSelectionComboBox = comboBox
		if 'download_date_choice' in self.appConfigDict:
			comboBox.current(comboBox['values'].index (self.appConfigDict['download_date_choice']))
		else:
			comboBox.current(0)
		comboBox.bind("<<ComboboxSelected>>", self.wizard_2_0_DateSelectionComboBoxSelectionChanged)
		comboBox.grid(column=1, row=0, sticky=W)
				
		label = Label(dateSelectFrame, text="Start:", bg=mainBgColor)
		label.grid(column=2, row=0, sticky=E, pady=5)
		entry = Entry(dateSelectFrame, bg=mainBgColor, width=8)
		if 'custom_download_date_end' in self.appConfigDict:
			entry.insert(0, self.appConfigDict['custom_download_date_end'])
		self.wizard_2_0_CustomDateRangeStartEntry = entry
		entry.grid(column=3, row=0, sticky=W, padx=5)
		label = Label(dateSelectFrame, text="End:", bg=mainBgColor)
		label.grid(column=4, row=0, sticky=E, pady=5)
		entry = Entry(dateSelectFrame, bg=mainBgColor, width=8)
		if 'custom_download_date_end' in self.appConfigDict:
			entry.insert(0, self.appConfigDict['custom_download_date_end'])
		self.wizard_2_0_CustomDateRangeEndEntry = entry
		entry.grid(column=5, row=0, sticky=W, padx=5)
		# trigger selection change event to set initial enable/disable state for custom date range edit fields
		self.wizard_2_0_DateSelectionComboBoxSelectionChanged(None)	
		
		dateSelectFrame.grid(column=0, columnspan=3, row=2, padx=20, sticky=W)		

		# media card choice
		label = Label(leftFrame, text="Media Card:", bg=mainBgColor)
		label.grid(column=0, row=3, sticky=E, pady=5)
		comboBox = ttk.Combobox(leftFrame, values=CardSlotUserReadableChoices, state='readonly', width=28)
		if 'card_slot_choice' in self.appConfigDict:
			comboBox.current(comboBox['values'].index (self.appConfigDict['card_slot_choice']))
		else:
			comboBox.current(0)
		comboBox.grid(column=1, row=3, sticky=W)
		self.wizard_2_0_CardSlotComboBox = comboBox
		
		# transfer order
		label = Label(leftFrame, text="Download Order:", bg=mainBgColor)
		label.grid(column=0, row=4, sticky=E, pady=5)
		comboBox = ttk.Combobox(leftFrame, values=TransferOrderReadableChoices, state='readonly')
		if 'transfer_order_choice' in self.appConfigDict:
			comboBox.current(comboBox['values'].index (self.appConfigDict['transfer_order_choice']))
		else:
			comboBox.current(0)
		comboBox.grid(column=1, row=4, sticky=W, ipadx=20)
		self.wizard_2_0_TransferOrderComboBox = comboBox
		
		# output directory
		(label, comboBox, button) = self.createDownloadDirectoryLabel_ComboBox_Button(leftFrame)
		label.grid(column=0, row=5, sticky=E, pady=5)
		comboBox.grid(column=1, row=5, sticky=W, ipadx=50, padx=0)
		button.grid(column=2, row=5, sticky=W, pady=5, padx=5)

		# if file exists combo
		(label, comboBox) = self.createIfFileExistsLabelAndCombo(leftFrame)
		label.grid(column=0, row=6, sticky=E, pady=5)
		comboBox.grid(column=1, row=6, sticky=W, ipadx=10)

		# additional options entry
		label = Label(leftFrame, text="Additional Args:", bg=mainBgColor)
		label.grid(column=0, row=7, sticky=E, pady=5)
		entry = Entry(leftFrame, bg=mainBgColor, width=50)
		if 'additional_args' in self.appConfigDict:
			entry.insert(0, self.appConfigDict['additional_args'])
		self.wizard_2_0_AdditionalArgsEntry = entry
		entry.grid(column=1, columnspan=3, row=7, sticky=W, pady=5)
	
		# skip files in download history checkbox
		checkButton = self.createSkipFilesInDownloadHistoryCheckbox(leftFrame)
		checkButton.grid(column=0, columnspan=3, row=8, sticky=W, ipady=4, ipadx=4, pady=5, padx=80)

		#
		# done with left frame, pack it
		#
		leftFrame.pack(side=LEFT, fill=BOTH, expand=1)		

		#
		# right frame
		#
		
		# button to start download
		rightFrame = self.createStartDownloadFrameAndButton_PackOnRightInParent(self.contentFrame, lambda : self.wizard_2_0_ButtonClick('start_download_selected_on_computer'), (35,10))
		
		# button to preview file list
		button = Button(rightFrame, text="Preview File List for Criteria", command=lambda : self.wizard_2_0_ButtonClick('preview_file_list'))
		button.pack(side=BOTTOM, expand=1, ipadx=5, ipady=5, padx=10, pady=(0,15))
		
		self.packContentFrame()
		
	def wizard_2_0_DateSelectionComboBoxSelectionChanged(self, event):
		# enable/disable custom date range edit fields based on combobox selection
		if (self.wizard_2_0_DateSelectionComboBox.get() == "custom date range"):
			self.wizard_2_0_CustomDateRangeStartEntry.configure(state=NORMAL)
			self.wizard_2_0_CustomDateRangeEndEntry.configure(state=NORMAL)
			if event: # don't set focus if we're being called to set initial enable/disable state by setContent_Wizard_2_0()
				self.wizard_2_0_CustomDateRangeStartEntry.focus_set()			
		else:
			self.wizard_2_0_CustomDateRangeStartEntry.configure(state=DISABLED)
			self.wizard_2_0_CustomDateRangeEndEntry.configure(state=DISABLED)
			
	@classmethod 		
	def validateCustomDateEntry(cls, userDateTimeStr):
		if userDateTimeStr.find(":") != -1:
			# user specified date and time
			strptimeTranslationStr = "%m/%d/%y %H:%M:%S"
		else:
			# user only specified time
			strptimeTranslationStr = "%m/%d/%y"
		try:
			strptimeResult = time.strptime(userDateTimeStr, strptimeTranslationStr)
		except ValueError as e:
			return True
		return False		
			
	def wizard_2_0_ButtonClick(self, str):
	
		if str == 'start_download_selected_on_computer' or str == 'preview_file_list':
		
			#
			# build file extension list and make sure it has at least
			# one entry
			#
			fileExtList = []
			if self.wizard_2_0_FileExt_NEF_IntVar.get() == True:
				fileExtList.append('NEF')
			if self.wizard_2_0_FileExt_JPG_IntVar.get() == True:
				fileExtList.append('JPG')
			if self.wizard_2_0_FileExt_MOV_IntVar.get() == True:
				fileExtList.append('MOV')
			if self.wizard_2_0_FileExt_CR2_IntVar.get() == True:
				fileExtList.append('CR2')
			if self.wizard_2_0_FileExt_ARW_IntVar.get() == True:
				fileExtList.append('ARW')
			fileExtMore = self.wizard_2_0_FileExtMoreEntry.get()				
			if (not fileExtList) and (not fileExtMore):
				tkMessageBox.showwarning("Selection Issue", "At least one file type must be checked/entered, otherwise there wont be anything to download :)")
				return;
				
			#
			# if custom date range entered, validate
			#
			if self.wizard_2_0_DateSelectionComboBox.get() == 'custom date range':
				dateStr = self.wizard_2_0_CustomDateRangeStartEntry.get()
				if dateStr:
					if (Application.validateCustomDateEntry(dateStr)):			
						tkMessageBox.showwarning("Invalid Start Date", "Start date specified \"{:s}\" is formatted incorrectly or has an invalid date/time. It must be formatted as mm/dd/yy or mm/dd/yy hh:mm:ss (including leading zeros) and be a valid date/time.".\
							format(dateStr))
						return
				dateStr = self.wizard_2_0_CustomDateRangeEndEntry.get()
				if dateStr:
					if (Application.validateCustomDateEntry(dateStr)):			
						tkMessageBox.showwarning("Invalid End Date", "End date specified \"{:s}\" is formatted incorrectly or has an invalid date/time. It must be formatted as mm/dd/yy or mm/dd/yy hh:mm:ss (including leading zeros) and be a valid date/time.".\
							format(dateStr))
						return
				
			#
			# save options in app config, so that they will be defaults next time
			#

			# app version
			self.saveAppVersionToConigDict()
			# ip address
			self.appConfigDict['ip_address'] = self.toolbar_IpAdressEntry.get()			
			# logging level
			self.appConfigDict['logging_level_choice'] = self.toolbar_LoggingLevelComboBox.get()
			# realtime download
			self.appConfigDict['realtime_download_choice'] = self.toolbar_RealtimeDownloadComboBox.get()
			# action
			self.appConfigDict['action_choice'] = self.wizard_2_0_ActionComboBox.get()
			# file ext list from check boxes
			self.appConfigDict['file_exts'] = fileExtList
			# file ext list from entry field
			self.appConfigDict['file_exts_more'] = fileExtMore
			# if file exists action
			self.appConfigDict['if_file_exists_choice'] = self.wizard_common_IfFileExistsComboBox.get()
			# date choice
			self.appConfigDict['download_date_choice'] = self.wizard_2_0_DateSelectionComboBox.get()
			self.appConfigDict['custom_download_date_end'] = self.wizard_2_0_CustomDateRangeStartEntry.get()
			self.appConfigDict['custom_download_date_end'] = self.wizard_2_0_CustomDateRangeEndEntry.get()
			
			# media card slot
			self.appConfigDict['card_slot_choice'] = self.wizard_2_0_CardSlotComboBox.get()
			# skip files in download history
			self.appConfigDict['skip_files_in_download_history_choice'] = self.wizard_SkipFilesInDownloadHistoryCheckboxIntVar.get()
			# transfer order
			self.appConfigDict['transfer_order_choice'] = self.wizard_2_0_TransferOrderComboBox.get()			
			# output dir history. in addition to saving it we move the current selection to the front of the list (we keep list MRU to be intuitive)
			self.setOutputDirListInAppConfig()
			# additional args
			self.appConfigDict['additional_args'] = self.wizard_2_0_AdditionalArgsEntry.get()
			
			# save the config					
			self.saveAppConfig()
				
			#
			# generate command line and launch airnefcmd
			#
			if str == 'start_download_selected_on_computer':
				argStr = ActionsUserReadableChoicesToAirnefCmdOption[self.wizard_2_0_ActionComboBox.get()]
			else:
				# 'preview_file_list'
				argStr = '--action listfiles'
			ipAddrStr = self.toolbar_IpAdressEntry.get()
			if ipAddrStr:
				argStr += " --ipaddress " + ipAddrStr
			argStr += " " + RealtimeTransferUserReadableChoicesToAirnefCmdOtion[self.toolbar_RealtimeDownloadComboBox.get()]				
			argStr += " --logginglevel " + self.toolbar_LoggingLevelComboBox.get()
			argStr += " --extlist " + " ".join(fileExtList)
			if fileExtMore:
				argStr += " " + fileExtMore
			argStr += self.genAirnefArgs_OutputDir_SkipFilesInDownloadHistory_IfExistsCmdOtion()
			argStr += " " + CardSlotUserReadableChoicesToAirnefCmdOption[self.wizard_2_0_CardSlotComboBox.get()]
			argStr += " " + TransferOrderReadableChoicesToAirnefCmdOption[self.wizard_2_0_TransferOrderComboBox.get()]

			# date
			dateChoiceStr = self.wizard_2_0_DateSelectionComboBox.get()
			if dateChoiceStr == 'All Dates':
				# all dates is airnefcmd's default, so no option needed
				pass
			elif dateChoiceStr == 'custom date range':
				startDateStr = self.wizard_2_0_CustomDateRangeStartEntry.get()
				if startDateStr:
					argStr += " --startdate \"{:s}\"".format(startDateStr)
				endDateStr = self.wizard_2_0_CustomDateRangeEndEntry.get()
				if endDateStr:
					argStr += " --enddate \"{:s}\"".format(endDateStr)
			else:
				dateTimeTodayMidnight = datetime.datetime.combine(datetime.datetime.now(), datetime.time.min)
				dateTimeForUserSpecifiedInterval = None
				if dateChoiceStr == 'today':
					dateTimeForUserSpecifiedInterval = dateTimeTodayMidnight
				elif dateChoiceStr == 'yesterday':
					dateTimeForUserSpecifiedInterval = dateTimeTodayMidnight - datetime.timedelta(days=1)
				elif dateChoiceStr == 'past week':
					dateTimeForUserSpecifiedInterval = dateTimeTodayMidnight - datetime.timedelta(weeks=1)
				elif dateChoiceStr == 'past month':
					dateTimeForUserSpecifiedInterval = dateTimeTodayMidnight - datetime.timedelta(days=31)
				elif dateChoiceStr == 'past year':				
					dateTimeForUserSpecifiedInterval = dateTimeTodayMidnight - datetime.timedelta(days=365)
				if dateTimeForUserSpecifiedInterval != None:
					argStr += " --startdate {:02d}/{:02d}/{:02d}".format(dateTimeForUserSpecifiedInterval.month, dateTimeForUserSpecifiedInterval.day, dateTimeForUserSpecifiedInterval.year-2000)
							
			argStr += " --cameratransferlist ignore"
			if self.wizard_2_0_AdditionalArgsEntry.get():
				argStr += " " + self.wizard_2_0_AdditionalArgsEntry.get()
			launchAirnefcmd(argStr)


#
# verifies user is running version a modern-enough version of python for this app
#					
def verifyPythonVersion():
	if sys.version_info.major == 2:
		if sys.version_info.minor < 7:
			print("Warning: You are running a Python 2.x version older than app was tested with.")
			print("Version running is {:d}.{:d}.{:d}, app was tested on 2.7.x".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
	elif sys.version_info.major == 3:
		if sys.version_info.minor < 4:
			print("Warning: You are running a Python 3.x version older than app was tested with.")
			print("Version running is {:d}.{:d}.{:d}, app was tested on 3.4.x".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
		
#
# sets app-level globals related to the platform we're running under and
# creates path to app directories, creating them if necessary
#			
def establishAppEnvironment():

	g.isWin32 = (platform.system() == 'Windows')
	g.isOSX = (platform.system() == 'Darwin')
	g.isFrozen = (getattr(sys, 'frozen', False))

	#
	# determine the directory our script resides in, in case the
	# user is executing from a different working directory.
	#
	g.appDir = os.path.dirname(os.path.realpath(sys.argv[0]))
	g.appResourceDir = os.path.join(g.appDir, "appresource")
	
	#
	# determine directory for our APPDATA, which contains log
	# and configuration files. For Win32 if we're frozen this
	# goes in the dedicated OS area for application data files
	#
	g.appDataDir = None
	if g.isFrozen and g.isWin32:
		if os.getenv('LOCALAPPDATA'):
			g.appDataDir = os.path.join(os.getenv('LOCALAPPDATA'), "airnef\\appdata") # typically C:\Users\<username>\AppData\Local\airnef\appdata
	elif g.isOSX: # for OSX we always try to store our app data under Application Support
		userHomeDir = os.getenv('HOME')
		if userHomeDir:
			applicationSupportDir = os.path.join(userHomeDir, 'Library/Application Support')
			if os.path.exists(applicationSupportDir): # probably not necessary to check existence since every system should have this directory
				g.appDataDir = os.path.join(applicationSupportDir, 'airnef/appdata')
	if not g.appDataDir:
		# none of runtime-specific cases above selected an app data directory - use directory based off our app directory
		g.appDataDir = os.path.join(g.appDir, "appdata")
	# create our app-specific subdirectories if necessary	
	if not os.path.exists(g.appDataDir):
		os.makedirs(g.appDataDir)
		
	
#
# main app routine
#			
def main():

	global root
	
	
	#
	# verify we're running under a tested version of python
	#
	verifyPythonVersion()
		
	#
	# establish our app environment, including our app-specific subdirectories
	#
	establishAppEnvironment()

	root = Tk()
	if not os.path.exists(g.appResourceDir):
		tkMessageBox.showwarning("Setup Error", "The appresource subdirectory is missing. This directory and its files (icons/bitmaps/etc..) are needed for proper functioning of airnef :(")
		return	
#	root.resizable(0,0) I'm tempted to disable resizing (for aesthetics) but going to kee it enabled in case some platforms don't size the main window properly
	app = Application(master=root)
	g.app = app
	app.mainloop()
	try: # root.destroy() throws exception if user exited app via native OS menu. Can't find a way to detect if it's been destroyed
		root.destroy()	  
	except:
		pass
	
#
# program entry point
#	
if __name__ == "__main__":
	main()

	

#
#############################################################################
#
# Here is a collection of OSX workarounds that didn't work out. I'm leaving them
# in for future reference/efforts
#

'''

#
# this is an altnerative to the "open" method of launching a Terminal window with airnefcmd that
# doesn't require writing the args to a file. Unfortunately once airnefcmd exits the terminal windows created
# by AppleScript stays open, requiring the user to manually close it, which made this workaround unsuitable
#
	script = "tell app \"Terminal\"\n\tactivate\n\tdo script \"python " + os.path.join(g.appDir, 'airnefcmd.py') + ' ' + argStr.replace('"', "'")  +  "\"\n end tell"
	subprocess.call(['osascript', '-e', script])

'''

