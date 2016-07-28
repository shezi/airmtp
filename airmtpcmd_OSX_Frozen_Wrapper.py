#!/usr/bin/env python

#
#############################################################################
#
# airnefcmd_OSX_Frozen_Wrapper.py - Wrapper around airnefcmd.py for use
# by the frozon airnef.py under OSX. This is a hack to work around the
# inability of a Python app running in an OSX bundle to launch a terminal
# app with parameters.
#
# Copyright (C) 2015, testcams.com
#
# This module is licensed under GPL v3: http://www.gnu.org/licenses/gpl-3.0.html
#
#############################################################################
#

from __future__ import print_function
from __future__ import division
import sys
#
# print Python version immediately to troubleshoot any version conflicts
# within the frozen environment that may cause imports to fail
#
print("airnefcmd OSX wrapper, running under Python Version {:d}.{:d}.{:d}".\
	format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
import strutil
import time
import os
import errno
import airnefcmd
import platform

class GlobalVarsStruct:
	def __init__(self):
		self.isWin32 = None			# True if we're running on a Windows platform
		self.isOSX = None			# True if we're runnong on an OSX platform
		self.appDir = None			# directory where script is located. this path is used to store all metadata files, in case script is run in different working directory
		self.appDataDir = None		# directory where we keep app metadata
		self.appResourceDir = None	# directory where we keep app resources (read-only files needed by app, self.appDir + "resouce")

#
# global variables
#
g = GlobalVarsStruct()


#
# creates IPC file for communication with Airnef
#
def createHackFileForAirnefCommunication(filename, data=None):
	fo = open(filename, "w")
	if data:
		fo.write(data)
	fo.close()


#
# deletes file, ignorning any errors
#
def deleteFileIgnoreErrors(filename):
    try:
        os.remove(filename)
    except:
        pass


#
# sets app-level globals related to the platform we're running under and
# creates path to app directories, creating them if necessary
#			
def establishAppEnvironment():

	g.isOSX = (platform.system() == 'Darwin')

	if not g.isOSX:
		raise AssertionError("Not running under OSX")

	#
	# determine the directory our script resides in, in case the
	# user is executing from a different working directory.
	#
	g.appDir = os.path.dirname(os.path.realpath(sys.argv[0]))
	g.appResourceDir = os.path.join(g.appDir, "appresource")
	
	#
	# note we always run in a frozen scenario since we're only
	# executed by airnef.pyw in a frozen environment. our environment
	# is not actually marked as frozen though since we're not the
	# module name associated with the app (airnef.pyw is)
	#
	g.appDataDir = None
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
		raise AssertionError("APPDATA path at {:s} doesn't exist".format(g.appDataDir))


#
# program entry point
#	
if __name__ == "__main__":
	
	establishAppEnvironment()	

	FILENAME_CMD_OPTS		= os.path.join(g.appDataDir, "airnefcmd-osxfrozen-cmdopts")
	FILENAME_NOTIFY_START	= os.path.join(g.appDataDir, "airnefcmd-osxfrozen-notifystart")
	FILENAME_NOTIFY_DONE	= os.path.join(g.appDataDir, "airnefcmd-osxfrozen-notifydone")

	fo = open(FILENAME_CMD_OPTS, 'r')
	cmdArgs = fo.read().split('\n')
	fo.close()
	if cmdArgs[len(cmdArgs)-1] == '':
		cmdArgs.pop()
	sys.argv = [os.path.join(g.appDir, './airnefcmd.py')] + cmdArgs

	createHackFileForAirnefCommunication(FILENAME_NOTIFY_START, str(os.getpid()))
	_errno = 0
	try:
		_errno = airnefcmd.main()
	except:
		print("exception")
	print("airnefcmd.main() returned/exited")

	createHackFileForAirnefCommunication(FILENAME_NOTIFY_DONE, data=str(_errno))
