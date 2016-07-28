#!/usr/bin/env python

#
#############################################################################
#
# applog - Application logging
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
# logging flags
#

# logging level flags
APPLOGF_LEVEL_ERROR				= (0x00000001<<0)
APPLOGF_LEVEL_INFORMATIONAL		= (0x00000001<<1)
APPLOGF_LEVEL_WARNING			= (0x00000001<<2)
APPLOGF_LEVEL_VERBOSE			= (0x00000001<<3)
APPLOGF_LEVEL_DEBUG				= (0x00000001<<4)
APPLOGF_LEVEL_MASK				= 0x000000FF
APPLOGF_DONT_WRITE_TO_CONSOLE	= (0x00000001<<8)

#
# global variables
# 
gFileSessionLog = None
gFileLifetimeLog = None
gLoggingFlags = 0

#
# initialize this module, which includes opening log file(s) for writing
#
def applog_init(loggingFlags=APPLOGF_LEVEL_INFORMATIONAL | APPLOGF_LEVEL_ERROR, sessionLogFilename=None, lifetimeLogFilename=None):
	global gFileSessionLog, gFileLifetimeLog, gLoggingFlags
	gLoggingFlags = loggingFlags
	if sessionLogFilename:
		try:
				gFileSessionLog = open(sessionLogFilename, "w")
		except IOError as e:
			print("Unable to open/create logfile \"{:s}\". {:s}".format(sessionLogFilename, str(e)))
			return e.errno
	if lifetimeLogFilename:
		try:
				gFileLifetimeLog = open(lifetimeLogFilename, "a")
		except IOError as e:
			print("Unable to open/create logfile \"{:s}\". {:s}".format(lifetimeLogFilename, str(e)))
			return e.errno
	return 0
	
#
# set new logging flags
#	
def applog_set_loggingFlags(newLoggingFlags):
	global gLoggingFlags
	gLoggingFlags = newLoggingFlags	
	
#
# shutdown this module
#	
def applog_shutdown():
	try:
		if gFileSessionLog:
			gFileSessionLog.close()
		if gFileLifetimeLog:
			gFileSessionLog.close()
	except IOError as e:
		print("Unable to close logfile. {:s}".format(str(e)))
 
 #
 # Log message with specified level
 #
def applog(str, flags=APPLOGF_LEVEL_INFORMATIONAL):
	if gLoggingFlags & (flags & APPLOGF_LEVEL_MASK):
		if not (flags & APPLOGF_DONT_WRITE_TO_CONSOLE):
			if flags & APPLOGF_LEVEL_ERROR:
				print(str, file=sys.stderr)
			else:
				print(str)
		# redirect output to log file(s)		
		if gFileSessionLog:
			print(str, file=gFileSessionLog)
		if gFileLifetimeLog:
			print(str, file=gFileLifetimeLog)
 
 
 #
 # Logging wrapper functions for each level
 #
def applog_i(s): 
	applog(s, APPLOGF_LEVEL_INFORMATIONAL)
def applog_v(s): 
	applog(s, APPLOGF_LEVEL_VERBOSE)
def applog_w(s): 
	applog(s, APPLOGF_LEVEL_WARNING)
def applog_e(s): 
	applog(s, APPLOGF_LEVEL_ERROR)
def applog_d(s):	
	applog(s, APPLOGF_LEVEL_DEBUG)
	
#
# Logging check-enabled functions, used to avoid
# performance penalty of generating log message
# if logging level is not enabled
#
def isDebugLog():
	return (gLoggingFlags & APPLOGF_LEVEL_DEBUG)
def isVerboseLog():
	return (gLoggingFlags & APPLOGF_LEVEL_VERBOSE)

#
# console writing function wrappers
#	
def consoleWriteLine(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()
def consoleClearLine():
	sys.stdout.write("\r" + " "*78 + "\r")
	sys.stdout.flush()