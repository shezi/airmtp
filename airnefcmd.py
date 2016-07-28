#!/usr/bin/env python

#
#############################################################################
#
# airnefcmd.py - Wireless file transfer for PTP/MTP-equipped cameras (command-line app)
# Copyright (C) 2015, testcams.com
#
# This module is licensed under GPL v3: http://www.gnu.org/licenses/gpl-3.0.html
#
#############################################################################
#

from __future__ import print_function
from __future__ import division
import six
from six.moves import xrange
from six.moves import cPickle as pickle
import argparse
import mtpwifi
from mtpdef import *
import strutil
import struct
import time
import datetime
import sys
import os
import errno
import math
import traceback
import platform
import socket
import hashlib
from dlinkedlist import *
from collections import namedtuple
from applog import *
import rename
import ssdp
import subprocess

#
# constants
#

AIRNEFCMD_APP_VERSION	= "1.1"

DEFAULT_MAX_KB_PER_GET_OBJECT_REQUEST				= 1024 		# 1MB - empirically tweaked to get max download performance from Nikon bodies (too large an xfer and Nikon bodies start intermittently dropping connections)
DEFAULT_MAX_KB_TO_BUFFER_FOR_GET_OBJECT_REQUESTS 	= 32768		# 32MB - max bytes we buffer before flushing what we have to disk

# values for g.fileTransferOrder
FILE_TRANSFER_ORDER_USER_CONFIGURED		= 0
FILE_TRANSFER_ORDER_OLDEST_FIRST		= 1
FILE_TRANSFER_ORDER_NEWEST_FIRST		= 2
# values for g.cameraMake
CAMERA_MAKE_UNDETERMINED				= 0
CAMERA_MAKE_NIKON						= 1
CAMERA_MAKE_CANON						= 2
CAMERA_MAKE_SONY						= 3
# values for g.realtimeDownloadMethod
REALTIME_DOWNLOAD_METHOD_NIKON_EVENTS	= 0
REALTIME_DOWNLOAD_METHOD_MTPOBJ_POLLING	= 1
REALTIME_DOWNLOAD_METHOD_SONY_EXIT		= 2
REALTIME_DOWNLOAD_METHOD_MAX			= REALTIME_DOWNLOAD_METHOD_SONY_EXIT
# values for g.args['sonyuniquecmdsenable'] (bitmask)
SONY_UNQIUECMD_ENABLE_SENDING_MSG					= 0x00000001
SONY_UNQIUECMD_ENABLE_UNKNOWN_CMD_1					= 0x00000002
SONY_UNQIUECMD_ENABLE_SAVING_PROCESS_CANCELLED_MSG	= 0x00000004


#
# custom errno from app
#
ERRNO_CAMERA_COMMUNICATION_FAILURE		= 4000	# general communication error with camera
ERRNO_CAMERA_UNEXPECTED_RESP_CODE		= 4001	# an MTP request was successfully delivered but the camera responsed with response code that indicated failure
ERRNO_CAMERA_PROTOCOL_ERROR				= 4002	# unexpected protocol event during PTP-IP exchange
ERRNO_SONY_REALTIME_ENTER_RETRY_LOOP	= 4003  # not an error or exit - for Sony realtime operaiton we simply return to the session retry loop after a transfer operation
ERRNO_COULDNT_CONNECT_TO_CAMERA			= 4004	# initial connection to camera was unsuccessful
# place all errors for which app should bypass retry invocations here, between ERRNO_FIRST_CUSTOM_DONT_RETRY and ERRNO_LAST_CUSTOM_DONT_RETRY
ERRNO_FIRST_CUSTOM_DONT_RETRY			= 5000	# first custom errno that we trigger for which app should bypass any retry invocations
ERRNO_BAD_CMD_LINE_ARG					= 5000	# bad command line argument specified
ERRNO_FILE_EXISTS_USER_SPECIFIED_EXIT	= 5001	# a file exists that we were to write to and user configured app to exit when this occurs
ERRNO_DIFFERENT_CAMREA_DURING_RETRY		= 5002	# during a retry  invocation a different camera was discvered vs the original camera we found
ERRNO_NO_CAMERA_TRANSFER_LIST			= 5003  # no camera transfer list available and user configured app to exit if the list is not available
ERRNO_NO_CARD_MEDIA_AVIALABLE			= 5004  # second slot specified but camera only has 1 slot
ERRNO_MTP_OBJ_CACHE_VALIDATE_FAILED		= 5005	# we're performing a (debug) validation of object cache and found a mismatch
ERRNO_DOWNLOAD_FILE_OP_FAILED			= 5006	# create/append/write/close operation failed on file being downloaded
ERRNO_RENAME_ENGINE_PARSING_ERROR		= 5007  # error parsing --dirnamespec or --filenamespec
ERRNO_REAL_TIME_CAPTURE_NOT_SUPPORTED	= 5008	# realtime capture not supported on the camera we're connected to
ERRNO_TRANSFER_LIST_NOT_SUPPORTED		= 5009	# camera doesn't support MTP transfer lists, which is used to download user-selected images in the camera
ERRNO_FILENAMESPEC_RESULT_EMPTY_STR		= 5010	# the result of the user-specified --filenamespec resulted in an empty string
ERRNO_FILENAMESPEC_HAS_PATH_CHARACTERS  = 5011  # the result of the user-specified --filenamespec had a path or path characters in it
ERRNO_DOWNLOADEXEC_LAUNCH_ERROR			= 5012	# unable to launch app/script specified by --downloadexec
ERRNO_DOWNLOADEXEC_NON_ZERO_EXIT_CODE	= 5013	# a launched '--downloadexec' app returned a non-zero result and user config was to exit on this case
ERRNO_LAST_CUSTOM_DONT_RETRY			= 5099	# last custom errno that we trigger for which app should bypass any retry invocations

#
# structures
#
class DownloadStatsStruct:

	def __init__(self):
		self.countFilesSkippedDueToDownloadHistory = 0
		self.countFilesSkippedDueToFileExistingLocally = 0
		self.countFilesDownloaded = 0
		self.totalBytesDownloaded = 0
		self.totalDownloadTimeSecs = 0
		
	def reportDownloadStats(self, fDontPrintStatsIfNoFilesDownloaded=False):
		if g.dlstats.totalDownloadTimeSecs > 0: # avoid divide-by-zero in case no files downloaded
			averageDownloadRateMbSec = g.dlstats.totalBytesDownloaded / g.dlstats.totalDownloadTimeSecs / 1048576
		else:
			averageDownloadRateMbSec = 0
		if fDontPrintStatsIfNoFilesDownloaded and g.dlstats.countFilesDownloaded==0:
			return
		applog_i("\n{:d} files downloaded in {:.2f} seconds (Average Rate = {:.2f} MB/s)".format(g.dlstats.countFilesDownloaded, g.dlstats.totalDownloadTimeSecs, averageDownloadRateMbSec))
		if g.dlstats.countFilesSkippedDueToDownloadHistory:
			applog_i("{:d} previously-downloaded files skipped".format(g.dlstats.countFilesSkippedDueToDownloadHistory))
		if g.dlstats.countFilesSkippedDueToFileExistingLocally:
			applog_i("{:d} files skipped because they already existed in output directory".format(g.dlstats.countFilesSkippedDueToFileExistingLocally))
		
#
# stats structure used by the createMtpObjectXX methods
# 
class CreateMtpObjectStatsStruct:
	def __init__(self):
		self.recursionNesting = 0
		self.countObjectsProcessed = 0
		self.countMtpObjectsAlreadyExisting = 0
		self.countCacheHits = 0


class GlobalVarsStruct:
	def __init__(self):
	
		self.isWin32 = None								# True if we're running on a Windows platform
		self.isOSX = None								# True if we're runnong on an OSX platform
		self.isFrozen = None							# True if we're running in a pyintaller frozen environment (ie, built as an executable)		
		self.args = None								# dictionary of command-line arguments (generated by argparse)
		self.appDir = None								# directory where script is located. this path is used to store all metadata files, in case script is run in different working directory
		self.appDataDir = None							# directory where we keep app metadata
		self.appStartTimeEpoch = None					# time that application started
		self.openSessionTimeEpoch = None				# time when session started with camera
		self.sessionId = None							# MTP session ID
		
		self.objfilter_dateStartEpoch = None			# user-specified starting date filter. any file earlier than this will be filtered.
		self.objfilter_dateEndEpoch = None				# user-specified ending date filter. any file later than this will be filtered.
		self.maxGetObjTransferSize = None				# max size of MTP_OP_GetPartialObject requests
		self.maxGetObjBufferSize = None					# max amount of download file data we buffer before flushing
		
		self.fileTransferOrder = None					# FILE_TRANSFER_ORDER_* constant
	
		self.socketPrimary = None
		self.socketEvents = None
		
		self.cameraMake = CAMERA_MAKE_UNDETERMINED 
		self.realtimeDownloadMethod = None
		
		self.countCardsUsed = None						# number of media cards that airnefcmd will be using/accessing this session
		self.storageId = None
		self.mtpStorageIds = None						# list of storage IDs returned from MTP_OP_GetStorageIDs / parseMptStorageIds()
		self.mtpDeviceInfo = None
		self.mtpStorageInfoList = None
		self.cameraLocalMetadataPathAndRootName = None	# path+root name for all metadata files we associate with a specific model+serial number
		
		self.lastFullMtpHandleListProcessedByBuildMtpObjects = None
		
		self.fAllObjsAreFromCameraTransferList = False	# True if buildMtpObjects() found and retrieved a transfer list from the camera (ie, user picked photos to download on camera)
		self.fRetrievedMtpObjects = False				# True if buildMtpObjects() has successfully completed this session
		self.fRealTimeDownloadPhaseStarted = False		# True if we've completed a "normal" mode transfer (or bypassed it by user config) and have started realtime image download
		
		self.downloadHistoryDict = None					# download history
		self.downloadMtpFileObjects_LastMtpObjectDownload = None # MTP object last downloaded (either last completed or last we were working on)
		
		self.countFilesDownloadedPersistentAcrossStatsReset = 0	# count of files downloaded this session, survives reset of DownloadStatsStruct
			
		# download stats
		self.dlstats = DownloadStatsStruct()

		# exit cleanup tracking vars
		self.filesToDeleteOnAppExit = []
	
#
# global vars
#
g  = GlobalVarsStruct()

#
# global constant data
#
CmdLineActionToMtpTransferOpDict = {				
	'getfiles' 			: MTP_OP_GetObject,			\
	'getsmallthumbs' 	: MTP_OP_GetThumb,			\
	'getlargethumbs'	: MTP_OP_GetLargeThumb		\
}

#
# used to maintain information about current file being downloaded
# across any retry/resumption attempts
# 
class PartialDownloadData():
	def __init__(self):
		self.bytesWritten = 0
		self.downloadTimeSecs = 0
		self.localFilenameWithoutPath = None
	def getBytesWritten(self):
		return self.bytesWritten
	def addBytesWritten(self, moreBytesWritten):
		self.bytesWritten += moreBytesWritten
	def getDownloadTimeSecs(self):
		return self.downloadTimeSecs
	def addDownloadTimeSecs(self, moreTimeSecs):
		self.downloadTimeSecs += moreTimeSecs
	def getLocalFilenameWithoutPath(self):
		return self.localFilenameWithoutPath
	def setLocalFilenameWithoutPath(self, localFilenameWithoutPath):
		self.localFilenameWithoutPath = localFilenameWithoutPath

#
# Main class to manage both individual MTP objects, including  files, directories, etc.., plus collections of these objects
#
class MtpObject(LinkedListObj):

	#
	# class variables
	#
	__MtpObjects_LL_CaptureDateSorted = LinkedList()	# link list of all MtpObject instances, sorted by capture date ([0] = oldest, [n-1]=newest)	
	__MtpObjects_ObjectHandleDict = {}					# dictionary of all objects, keyed by object handle 
	_CountMtpObjectDirectories = 0						# number MtpObjects that represent directories

	#
	# instance variables (documentation only since variables don't need to be declared in Python)
	# self.mtpObjectHandle:			Handle by which camera references this object
	# self.mtpObjectInfo: 			Structure containing information from MTP_OP_GetObjectInfo
	# self.captureDateEpoch:		self.mtpObjectInfo.captureDateStr converted to epoch time
	# self.bInTransferList:			TRUE if user selected this image for transfer in the camera
	# self.bDownloadedThisSession	TRUE if object has been downloaded successfully this session [for possible future retry logic, if implemented]
	#

	def __init__(self, mtpObjectHandle, mtpObjectInfo):
	
		# init some instance vars
		self.bInCameraTransferList = False
		self.bDownloadedThisSession = False
		self.partialDownloadData = None

		# save handle and object info to instance vars
		self.mtpObjectHandle = mtpObjectHandle
		self.mtpObjectInfo = mtpObjectInfo

		if isDebugLog():
			applog_d("Creating MtpObject with the following mtpObjectInfo:\n" + str(self))
		
		# calculate instance vars that are based on mtpObjectInfo data
		self.captureDateEpoch = 0
		if self.mtpObjectInfo.captureDateStr: # there is a non-empty capture date string
			self.captureDateEpoch = mtpTimeStrToEpoch(self.mtpObjectInfo.captureDateStr)
		else:
			#
			# Sony uses a date stamp for the filename of folders. Extract that as the date if this is a folder object. this is
			# important because we rely on folder timestamps for the MTP object cache logic
			#
			if self.mtpObjectInfo.associationType == MTP_OBJASSOC_GenericFolder:
				if len(self.mtpObjectInfo.filename)==10 and self.mtpObjectInfo.filename[4]=='-' and self.mtpObjectInfo.filename[7]=='-':
					# capture date is in in YYYY-MM-DD (Sony uses this for folders)
					self.captureDateEpoch = time.mktime( time.strptime(self.mtpObjectInfo.filename, "%Y-%m-%d"))			
			
		# make sure this object hasn't already been inserted
		if MtpObject.objInList(self):
			raise AssertionError("MtpObject: Attempting to insert mtpObjectHandle that's already in dictionary. newObj:\n{:s}, existingObj:\n{:s}".format(
				str(self), str(MtpObject.__MtpObjects_ObjectHandleDict[self.mtpObjectHandle])))

		# insert into capture-date sorted linked list
		LinkedListObj.__init__(self, self.captureDateEpoch, MtpObject.__MtpObjects_LL_CaptureDateSorted)
			
		# insert into object handle dictionary, which is used for quick lookups by object handle
		MtpObject.__MtpObjects_ObjectHandleDict[self.mtpObjectHandle] = self
		
		# update counts based on this object type
		if self.mtpObjectInfo.associationType == MTP_OBJASSOC_GenericFolder:
			MtpObject._CountMtpObjectDirectories += 1
					
	def setAsDownloadedThisSession(self):
		self.bDownloadedThisSession = True
		
	def wasDownloadedThisSession(self):
		return self.bDownloadedThisSession
		
	def isPartialDownload(self):
		return self.partialDownloadData != None
		
	def partialDownloadObj(self):
		if self.partialDownloadData:
			return self.partialDownloadData
		self.partialDownloadData = PartialDownloadData()
		return self.partialDownloadData
		
	def releasePartialDownloadObj(self):
		if self.partialDownloadData:
			self.partialDownloadData = None
			
	def getImmediateDirectory(self): # gets immediate camera directory that this object is in. ex: "100NC1J4"
		objHandleDirectory = self.mtpObjectInfo.parentObject
		if not objHandleDirectory:
			# no parent to this object
			return ""
		if objHandleDirectory not in MtpObject.__MtpObjects_ObjectHandleDict:
			applog_d("getImmediateDirectory(): Unable to locate parent object for {:s}, parent=0x{:08x}".format(self.mtpObjectInfo.filename, objHandleDirectory))
			return ""			
		dirObject = MtpObject.__MtpObjects_ObjectHandleDict[objHandleDirectory]
		return dirObject.mtpObjectInfo.filename		
							
	def genFullPathStr(self): # builds full path string to this object on camera, including filename itself. Ex: "DCIM\100NC1J4\DSC_2266.NEF"
		# full path built by walking up the parent object tree for this object, prepending the directory of each parent we find
		pathStr = self.mtpObjectInfo.filename
		objHandleAncestorDirectory = self.mtpObjectInfo.parentObject
		loopIterationCounter_EndlessLoopProtectionFromCorruptList = 0
		while (objHandleAncestorDirectory != 0):
			if objHandleAncestorDirectory not in MtpObject.__MtpObjects_ObjectHandleDict:
				# couldn't find next folder up. this shouldn't happen since we always pull down full directory tree for all objects
				applog_d("genFullPathStr(): Unable to locate parent object for {:s}, parent=0x{:08x}".format(self.mtpObjectInfo.filename, objHandleDirectory))
				return pathStr
			dirObject = MtpObject.__MtpObjects_ObjectHandleDict[objHandleAncestorDirectory]
			pathStr = dirObject.mtpObjectInfo.filename + "\\" + pathStr
			objHandleAncestorDirectory = dirObject.mtpObjectInfo.parentObject
			loopIterationCounter_EndlessLoopProtectionFromCorruptList += 1
			if loopIterationCounter_EndlessLoopProtectionFromCorruptList >= 512:	
				# 512 is arbitrary. wouldn't expect cameras to have more than one or two directory levels
				raise AssertionError("Endless loop detected while building directory chain for {:s}. Local list is corrupt".format(pathStr))
			
		return pathStr
									
	@classmethod
	def getCount(cls):	# returns count of objects
		return MtpObject.__MtpObjects_LL_CaptureDateSorted.count()
		
	@classmethod
	def getOldest(cls):	# returns oldest object in age collection
		if MtpObject.__MtpObjects_LL_CaptureDateSorted.count():		# if list is not empty
			return MtpObject.__MtpObjects_LL_CaptureDateSorted.head()
		else:
			return None
							
	@classmethod
	def getNewest(cls):	# returns newest object in age collection
		if MtpObject.__MtpObjects_LL_CaptureDateSorted.count():		# if list is not empty
			return MtpObject.__MtpObjects_LL_CaptureDateSorted.tail()
		else:
			return None
		
	def getNewer(self):	# returns next newer object
		return self.llNext()
			
	def getOlder(self):	# returns next older object
		return self.llPrev()

	@classmethod
	def getByMtpObjectHandle(cls, mtpObjectHandle):
		if mtpObjectHandle in MtpObject.__MtpObjects_ObjectHandleDict:
			return MtpObject.__MtpObjects_ObjectHandleDict[mtpObjectHandle]
		else:
			return None
			
	@classmethod
	def objInList(cls, mtpObj):		
		return mtpObj.mtpObjectHandle in MtpObject.__MtpObjects_ObjectHandleDict
			
			
	def __str__(self):	# generates string description of object
		s =  "MtpObject instance = 0x{:08x}\n".format(id(self))
		s += "  mtpObjectHandle = 0x{:08x}\n".format(self.mtpObjectHandle)
		s += "  --- mptObjectInfo ---\n"		
		s += "    storageId          = " + getMtpStorageIdDesc(self.mtpObjectInfo.storageId) + "\n"
		s += "    objectFormat       = " + getMtpObjFormatDesc(self.mtpObjectInfo.objectFormat) + "\n"
		s += "    protectionStatus   = " + strutil.hexShort(self.mtpObjectInfo.protectionStatus) + "\n"
		s += "    compressedSize     = " + strutil.hexWord(self.mtpObjectInfo.objectCompressedSize) + "\n"
		s += "    thumbFormat        = " + getMtpObjFormatDesc(self.mtpObjectInfo.thumbFormat) + "\n"
		s += "    thumbCompressedSize= " + strutil.hexWord(self.mtpObjectInfo.thumbCompressedSize) + "\n"
		s += "    thumbPixDimensions = " + str(self.mtpObjectInfo.thumbPixWidth) + "x" + str(self.mtpObjectInfo.thumbPixHeight) + "\n"
		s += "    imagePixDimensions = " + str(self.mtpObjectInfo.imagePixWidth) + "x" + str(self.mtpObjectInfo.imagePixHeight) + "\n"
		s += "    imageBitDepth      = " + str(self.mtpObjectInfo.imageBitDepth) + "\n"
		s += "    parentObject       = " + strutil.hexWord(self.mtpObjectInfo.parentObject) + "\n"
		s += "    associationType    = " + getObjAssocDesc(self.mtpObjectInfo.associationType) + "\n"
		s += "    associationDesc    = " + strutil.hexWord(self.mtpObjectInfo.associationDesc) + "\n"
		s += "    sequenceNumber     = " + strutil.hexWord(self.mtpObjectInfo.sequenceNumber) + "\n"
		s += "    filename           = " + self.genFullPathStr() + "\n"
		s += "    captureDateSt      = " + self.mtpObjectInfo.captureDateStr + "\n"
		s += "    modificationDateStr= " + self.mtpObjectInfo.modificationDateStr
		return s

		
#
# resets all download statistics
#	
def resetDownloadStats():
	g.dlstats = DownloadStatsStruct()	

		
#
# verifies user is running version a modern-enough version of python for this app
#		
def verifyPythonVersion():
	if sys.version_info.major == 2:
		if sys.version_info.minor < 7:
			applog_i("Warning: You are running a Python 2.x version older than app was tested with.")
			applog_i("Version running is {:d}.{:d}.{:d}, app was tested on 2.7.x".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
	elif sys.version_info.major == 3:
		if sys.version_info.minor < 4:
			applog_i("Warning: You are running a Python 3.x version older than app was tested with.")
			applog_i("Version running is {:d}.{:d}.{:d}, app was tested on 3.4.x".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))


#
# returns the number of seconds that have elapsed since
# the specified anchor time. if the anchor time is None
# then this routine returns the current time, which
# the caller can use for a subsequent call to get elapsed
# time. time values are floats
#
def secondsElapsed(timeAnchor):
	timeCurrent = time.time()
	if timeAnchor == None:
		return timeCurrent
	return timeCurrent - timeAnchor


#
# sets app-level globals related to the platform we're running under and
# creates path to app directories, creating them if necessary
#			
def establishAppEnvironment():

	g.isWin32 = (platform.system() == 'Windows')
	g.isOSX = (platform.system() == 'Darwin') 
	g.isFrozen = (getattr(sys, 'frozen', False)) # note for OSX isFrozen is always false because py2app only marks airnef.pyw as frozen when we're a py2app

	#
	# determine the directory our script resides in, in case the
	# user is executing from a different working directory.
	#
	g.appDir = os.path.dirname(os.path.realpath(sys.argv[0]))

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
# transltes a date or date+time string from the user into an
# epoch time (ie, time in seconds).
#
def translateDateCmdLineArgToEpoch(cmdArgDesc, isInclusiveEndDate=False):
	userDateTimeStr = g.args[cmdArgDesc]
	if userDateTimeStr == None:
		# user did not specify arg
		return None
	if userDateTimeStr.find(":") != -1:
		# user specified date and time
		strptimeTranslationStr = "%m/%d/%y %H:%M:%S"
		bOnlyDateSpecified = False
	else:
		# user only specified time
		strptimeTranslationStr = "%m/%d/%y"
		bOnlyDateSpecified = True		
	try:
		strptimeResult = time.strptime(userDateTimeStr, strptimeTranslationStr)
	except ValueError as e:
		applog_e("Date specified for \"--{:s}\" is \"{:s}\", which is formatted incorrectly or has an invalid date/time. It must be formatted as mm/dd/yy or mm/dd/yy hh:mm:ss (including leading zeros) and be a valid date/time.".\
			format(cmdArgDesc, userDateTimeStr))
		sys.exit(ERRNO_BAD_CMD_LINE_ARG)
	timeEpoch = time.mktime(strptimeResult)
	if bOnlyDateSpecified and isInclusiveEndDate:
		timeEpoch += (23*60*60) + (59*60) + 59	# make end date inclusive by adding 23 hours, 59 minutes, 59 seconds to epoch time
	return timeEpoch


#
# sets/changes the capture date filter to our app's start time. this is
# done to limit further downloads to those captured after the app started,
# such as for realtime capture
#
def changeCaptureDateFilterToAppStartTime():
	#
	# I've found a bug in the D7200 and D750 - it may exist on other cameras but I
	# don't see it on a D7100 w/WU-1a nor a J5. The firmware will sometimes misreport
	# the seconds field capture time in the MTP_OP_GetObjectInfo. It's a curious bug -
	# the camera reports a seconds value that is half of the actual value. Here is an
	# actual example taken from a D7200:
	#
	# Data returned from MTP_OP_GetObjectInfo:
	#
	# 	filename           	= DSC_0093.NEF
    # 	captureDateSt       = 20150927T185813
    #	modificationDateStr = 20150927T185813
	#
	# However when the file is viewed on the camera in playback mode the correctly
	# displayed timestamp is 18:58:26, so the MTP seconds timestamp is half what it
	# should be. When the issue does occur it appears to be a capture-time bug - the
	# camera will always misreport the time on  files that had the issue even
	# if it's currently in a state where it doesn't have the issue (ie, where
	# new files deliver the correct timestamp over MTP).
	#
	# Since we use capture-date filtering for our realtime capture having the time
	# skew from this bug will cause us to think the image is older than it is, at least
	# within the first minute of our session where the skew is enough to put the image
	# before our appStartTimeEpoch. To work around this I adjust the capture-date filter
	# back by 35 seconds from realtime (a few extra seconds padding just in case) - since
	# the Nikon bug produces max skew of 30 seconds (for the case of the real timestamp
	# being 59 seconds but the camera reports it as 29, since it rounds down). This runs
	# the risk of us downloading images taken up to 35 seconds before the user launched
	# airnefcmd for realtime transfer (ie, images the user didn't want if he's running
	# airnefcmd in realtime-only mode)
	#
	g.objfilter_dateStartEpoch = g.appStartTimeEpoch - 35
	g.objfilter_dateEndEpoch = None


#
# clears the capture date filters
#	
def clearCaptureDateFilter():
	g.objfilter_dateStartEpoch = None
	g.objfilter_dateEndEpoch = None


#
# verifies that a command line integer value is within a defined range
#
def verifyIntegerArgRange(argNameStr, minAllowedValue, maxAllowedValue) :
	if g.args[argNameStr] != None:
		if g.args[argNameStr] < minAllowedValue or g.args[argNameStr] > maxAllowedValue:
			applog_e("Invalid value for --{:s}: valid range is [{:d}-{:d}]".format(argNameStr, minAllowedValue, maxAllowedValue))
			exitAfterCmdLineError(ERRNO_BAD_CMD_LINE_ARG)
	
	
#
# verifies that a command line argument is either an allowable
# string constant or a valid integer value. If validation fails
# then sys.exit() is called with ERRNO_BAD_CMD_LINE_ARG
#
def verifyIntegerArgStrOptions(argNameStr, validStrArgValues=None):
	argValueStr = g.args[argNameStr]
	if validStrArgValues and argValueStr in validStrArgValues:
		# arg is one of the valid string values
		return
	try:
		int(argValueStr)
	except:
		if validStrArgValues == None:
			applog_e("Invalid integer value specified for --" + argNameStr)
		else:
			applog_e("Unknown value name or integer value specified for --" + argNameStr)
			applog_e("Valid values are: {:s}".format(str(validStrArgValues)))
		sys.exit(ERRNO_BAD_CMD_LINE_ARG)	


#
# converts the values of a multiple-value argument ('nargs=+') to uppercase set
#		
def convertMultipleArgToUppercaseSet(argNameStr):
	if g.args[argNameStr]:
		g.args[argNameStr] = set([ x.upper() for x in g.args[argNameStr] ])
	

#
# converts the values of a multiple-value argument ('nargs=+') to lowercase set
#		
def convertMultipleArgToLowercaseSet(argNameStr):
	if g.args[argNameStr]:
		g.args[argNameStr] = set([ x.lower() for x in g.args[argNameStr] ])
	

#
# processCmdLine - Processes command line arguments
#
class ArgumentParserError(Exception): pass # from http://stackoverflow.com/questions/14728376/i-want-python-argparse-to-throw-an-exception-rather-than-usage
class ArgumentParserWithException(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


#
# called when a command-line error is detected. shuts down the applog module
# and then invokves sys.exit() with specified error code
#
def exitAfterCmdLineError(errno):
	shutdownApplog()
	sys.exit(errno)

	
#
# used for a parser.add_argument "type=conver_int_auto_radix" instead of
# of "type=int". this version converts using a radix determined from the string rather
# than  assumed base-10 for "type=int". this allows hex entries
#	
def conver_int_auto_radix(argStr):
	return int(argStr, 0)
	
	
def processCmdLine():

	#
	# note: if you add additional filter options/logic, go to realTimeCapture() to see if those options
	# need to be overriden when we enter the realtime capture phase
	#
	parser = ArgumentParserWithException(fromfile_prefix_chars='!',\
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description='Wifi image transfer utility for Nikon cameras (airnef@hotmail.com)',\
		epilog="Options can also be specified from a file. Use !<filename>. Each word in the\nfile must be on its own line.\n\nYou "\
			"can abbreviate any argument name provided you use enough characters to\nuniquely distinguish it from other argument names.\n"\
			"\n\n"\
			"Command-Line Examples:\n"\
			"  %(prog)s --extlist NEF MOV (download only raw images and MOV files)\n"\
			"  %(prog)s --downloadhistory ignore (dont skip files previously downloaded)")
	parser.add_argument('--ipaddress', type=str.lower, help='IP address of camera. Default is "%(default)s"', default='192.168.1.1', metavar="addr", required=False)			
	parser.add_argument('--action', type=str.lower, choices=['getfiles', 'getsmallthumbs', 'getlargethumbs', 'listfiles'], help='Program action. Default is "%(default)s"', default='getfiles', required=False)
	parser.add_argument('--realtimedownload', type=str.lower, choices=['disabled', 'afternormal', 'only'], help='Download images from camera in realtime as they\'re taken. \'afternormal\' means realtime capture starts after regular image download. \'only\' skips normal download and only captures realtime images. Default is "%(default)s"', default='disabled', required=False)	
	parser.add_argument('--extlist', help='Type of image/file(s) to download. Ex: \"--extlist NEF\". Multiple extensions can be specified. Use \"<NOEXT>\" to include files that don\'t have extensions. Default is to download all file types', default=None, nargs='+', metavar='extension', required=False)
	parser.add_argument('--startdate', help='Only include image/file(s) captured on or later than date. Date-only Ex: --startdate 12/05/14. Date+Time Example: --startdate \"12/05/14 15:30:00\"', metavar="date", required=False)
	parser.add_argument('--enddate', help='Only include image/file(s) captured on or earlier than date or date+time. Date without a specified time is inclusive, so for example --enddate 06/12/14 is interpreted as 06/12/14 23:59:59', metavar="date", required=False)
	parser.add_argument('--outputdir', type=str, help='Directory to store image/file(s) to.  Default is current directory. No ending backslash is necessary. If path contains any spaces enclose it in double quotes. Example: --outputdir \"c:\My Documents\"', default=None, metavar="path", required=False)
	parser.add_argument('--ifexists', type=str.lower, choices=['uniquename', 'skip', 'overwrite', 'prompt', 'exit'], help='Action to take if file with same name already exists. Default is "%(default)s"', default='uniquename', required=False)
	parser.add_argument('--downloadhistory', type=str.lower, choices=['skipfiles', 'ignore', 'clear' ], help='\'skipfiles\' means that files in history (ie, previously downloaded) will be skipped and not downloaded. Default is "%(default)s"', default='skipfiles', required=False)
	parser.add_argument('--onlyfolders', help='Only include image/file(s) existing in specified camera folders.. Ex: \"--onlyfolders 100D7200 101D7200\". Default is to include all folders', default=None, nargs='+', metavar="camera_folder", required=False)
	parser.add_argument('--excludefolders', help='Exclude image/file(s) existing in specified camera folders.. Ex: \"--excludefolders 103D7200\". Default is no exclusions.', default=None, nargs='+', metavar="camera_folder", required=False)			
	parser.add_argument('--filenamespec', type=str, help='Optionally rename files using dynamic renaming engine. See online help for documentation on \'spec\'', default=None, metavar="spec", required=False)	
	parser.add_argument('--dirnamespec', type=str, help='Optionally name directories using dynamic renaming engine. See online help for documentation on \'spec\'', default=None, metavar="spec", required=False)		
	parser.add_argument('--transferorder', type=str.lower, choices=['oldestfirst', 'newestfirst'], help='Transfer oldest or newest files first. Default is "%(default)s"', default='oldestfirst', required=False)
	parser.add_argument('--slot', type=str.lower, help='Card slot on camera to read from. Default is "%(default)s", which means first populated slot', choices=['firstfound', 'first', 'second', 'both'], default='firstfound', required=False)
	parser.add_argument('--cameratransferlist', type=str.lower, choices=['useifavail', 'exitifnotavail', 'ignore'], help='Decide how to handle images selected on camera. Default is "%(default)s"', default='useifavail', required=False)
	parser.add_argument('--downloadexec', help='Launch application for each file downloaded', default=None, nargs='+', metavar=('executable', 'arguments'), required=False)
	parser.add_argument('--downloadexec_extlist', help='Type of files(s) by extension on wich to perform --downloadexec on. Default is all file types', default=None, nargs='+', metavar='extension', required=False)
	parser.add_argument('--downloadexec_options', help='Options for launcing application. For example \'wait\' waits for launched app to exit before proceeding to next download. See online help for more options', default=[], nargs='+', metavar='option', required=False)	
	parser.add_argument('--realtimepollsecs', type=int, help='How often camera is polled for new images in realtime mode, in seconds. Default is every %(default)s seconds', default=3, metavar="seconds", required=False)
	parser.add_argument('--logginglevel', type=str.lower, choices=['normal', 'verbose', 'debug' ], help='Sets how much information is saved to the result log. Default is "%(default)s"', default='normal', required=False)
	# hidden args (because they wont be used often and will complicate users learning the command line - they are documented online)
	parser.add_argument('--connecttimeout', help=argparse.SUPPRESS, type=int, default=10, required=False)
	parser.add_argument('--socketreadwritetimeout', help=argparse.SUPPRESS, type=int, default=5, required=False)
	parser.add_argument('--retrycount', help=argparse.SUPPRESS, type=int, default=sys.maxsize, required=False)
	parser.add_argument('--retrydelaysecs', help=argparse.SUPPRESS, type=int, default=5, required=False)
	parser.add_argument('--printstackframes', help=argparse.SUPPRESS, type=str.lower, choices=['no', 'yes'], default='no', required=False)
	parser.add_argument('--mtpobjcache', type=str.lower, choices=['enabled', 'writeonly', 'readonly', 'verify', 'disabled'], help=argparse.SUPPRESS, default='enabled', required=False)	
	parser.add_argument('--mtpobjcache_maxagemins', help=argparse.SUPPRESS, type=int, default=0, required=False) # default is 0=indefinite (never invalidate based on age)
	parser.add_argument('--maxgetobjtransfersizekb', help=argparse.SUPPRESS, type=int, default=DEFAULT_MAX_KB_PER_GET_OBJECT_REQUEST, required=False)	
	parser.add_argument('--maxgetobjbuffersizekb', help=argparse.SUPPRESS, type=int, default=DEFAULT_MAX_KB_TO_BUFFER_FOR_GET_OBJECT_REQUESTS, required=False)
	parser.add_argument('--initcmdreq_guid', help=argparse.SUPPRESS, type=str.lower, default='0x7766554433221100-0x0000000000009988', required=False) # GUID order in string is high-low
	parser.add_argument('--initcmdreq_hostname', help=argparse.SUPPRESS, type=str, default='airnef', required=False)
	parser.add_argument('--initcmdreq_hostver', help=argparse.SUPPRESS, type=conver_int_auto_radix, default=0x00010000, required=False)
	parser.add_argument('--opensessionid', help=argparse.SUPPRESS, type=conver_int_auto_radix, default=None, required=False)
	parser.add_argument('--maxclockdeltabeforesync', help=argparse.SUPPRESS, type=str.lower, default='5', required=False)
	parser.add_argument('--camerasleepwhendone', help=argparse.SUPPRESS, type=str.lower, choices=['no', 'yes'], default='yes', required=False)
	parser.add_argument('--sonyuniquecmdsenable', help=argparse.SUPPRESS, type=conver_int_auto_radix, default=SONY_UNQIUECMD_ENABLE_SENDING_MSG, required=False)
	parser.add_argument('--suppressdupconnecterrmsgs', help=argparse.SUPPRESS, type=str.lower, choices=['no', 'yes'], default='yes', required=False)
	parser.add_argument('--rtd_pollingmethod', help=argparse.SUPPRESS, type=int, default=None, required=False)
	parser.add_argument('--rtd_mtppollingmethod_newobjdetection', help=argparse.SUPPRESS, type=str.lower, choices=['objlist', 'numobjs'], default='objlist', required=False)
	parser.add_argument('--rtd_maxsecsbeforeforceinitialobjlistget', help=argparse.SUPPRESS, type=int, default=5, required=False)
	parser.add_argument('--ssdp_discoveryattempts', help=argparse.SUPPRESS, type=int, default=3, required=False)
	parser.add_argument('--ssdp_discoverytimeoutsecsperattempt', help=argparse.SUPPRESS, type=int, default=2, required=False)	
	parser.add_argument('--ssdp_discoveryflags', help=argparse.SUPPRESS, type=conver_int_auto_radix, default=None, required=False)
	parser.add_argument('--ssdp_addservice', help=argparse.SUPPRESS, nargs='+', required=False, default=None)
	parser.add_argument('--ssdp_addmulticastif', help=argparse.SUPPRESS, nargs='+', required=False, default=None)
	
	
	#
	# if there is a default arguments file present, add it to the argument list so that parse_args() will process it
	#
	defaultArgFilename = os.path.join(g.appDir, "airnefcmd-defaultopts")
	if os.path.exists(defaultArgFilename):
		sys.argv.insert(1, "!" + defaultArgFilename) # insert as first arg (past script name), so that the options in the file can still be overriden by user-entered cmd line options
			
	# perform the argparse
	try:
		args = vars(parser.parse_args())
	except ArgumentParserError as e:
		applog_e("Command line error: " + str(e))
		exitAfterCmdLineError(ERRNO_BAD_CMD_LINE_ARG)	
	
	# set our global var to the processed argument list	and log them
	g.args = args

	#
	# process any args that need verification/translation/conversion
	#
	
	# convert all arguments that have multiple values to uppercase/lowercase sets
	convertMultipleArgToUppercaseSet('extlist')
	convertMultipleArgToUppercaseSet('onlyfolders')
	convertMultipleArgToUppercaseSet('excludefolders')
	convertMultipleArgToLowercaseSet('downloadexec_options')
	convertMultipleArgToUppercaseSet('downloadexec_extlist')
	
	if not g.args['outputdir']:
		if not g.args['dirnamespec']:
			# neither 'outputdir' nor 'dirnamespec' specified - use current directory
			g.args['outputdir'] = '.\\' if g.isWin32 else './'
		else:
			# 'dirnamespec' specified - use empty string for base output dir
			g.args['outputdir'] = ""
	
	
	# verify syntax of --filenamespec and --dirnamespec
	if g.args['filenamespec']:
		try:
			rename.verifyRenameFormatStringSyntax(g.args['filenamespec'])
		except rename.GenerateReplacementNameException as e:
			applog_e("Error parsing filenamespec: " + str(e))
			exitAfterCmdLineError(ERRNO_RENAME_ENGINE_PARSING_ERROR)
	if g.args['dirnamespec']:
		try:
			rename.verifyRenameFormatStringSyntax(g.args['dirnamespec'])
		except rename.GenerateReplacementNameException as e:
			applog_e("Error parsing dirnamespec: " + str(e))
			exitAfterCmdLineError(ERRNO_RENAME_ENGINE_PARSING_ERROR)
			
	# verify syntax of --downloadexec
	if g.args['downloadexec']:
		try:
			for argNumber, arg in enumerate(g.args['downloadexec']):
				rename.verifyRenameFormatStringSyntax(arg)
		except rename.GenerateReplacementNameException as e:
			applog_e("Error parsing downloadexec arg #{:d} \"{:s}\": {:s}".format(argNumber+1, arg, str(e)))
			exitAfterCmdLineError(ERRNO_RENAME_ENGINE_PARSING_ERROR)
	
	# verify --downloadexec_options
	validDownloadExecOptions = [ 'ignorelauncherror', 'wait', 'exitonfailcode', 'delay', 'notildereplacement' ]
	for arg in g.args['downloadexec_options']:
		if arg not in validDownloadExecOptions:
			applog_e("Unrecognized option \"{:s}\" for --downloadexec_options".format(arg))
			exitAfterCmdLineError(ERRNO_BAD_CMD_LINE_ARG)
	
	if g.args['action'] not in CmdLineActionToMtpTransferOpDict:
		#
		# action is not a download operation. change/disable other command
		# line arguments that aren't valid for non-download actions
		#
		g.args['realtimedownload'] = 'disabled'

	if g.args['realtimedownload'] != 'only':
		# regular image download enabled. process any start/end date filters that user specified
		g.objfilter_dateStartEpoch = translateDateCmdLineArgToEpoch('startdate')
		g.objfilter_dateEndEpoch = translateDateCmdLineArgToEpoch('enddate', isInclusiveEndDate=True)
	# else we'll set the capture date filters later for realtime operation
		
	g.fileTransferOrder = FILE_TRANSFER_ORDER_OLDEST_FIRST if g.args['transferorder']=='oldestfirst' else FILE_TRANSFER_ORDER_NEWEST_FIRST	
	g.maxGetObjTransferSize = g.args['maxgetobjtransfersizekb'] * 1024
	g.maxGetObjBufferSize = g.args['maxgetobjbuffersizekb'] * 1024		
	verifyIntegerArgStrOptions('maxclockdeltabeforesync', ['disablesync', 'alwayssync'])	
	verifyIntegerArgRange('rtd_pollingmethod', 0, REALTIME_DOWNLOAD_METHOD_MAX)
	
	# process any args that require action now
	if g.args['logginglevel'] == 'normal':
		# we've already set to this default
		pass
	elif g.args['logginglevel'] == 'verbose':
		applog_set_loggingFlags(APPLOGF_LEVEL_INFORMATIONAL | APPLOGF_LEVEL_ERROR | APPLOGF_LEVEL_WARNING | APPLOGF_LEVEL_VERBOSE)
	elif g.args['logginglevel'] == 'debug':
		applog_set_loggingFlags(APPLOGF_LEVEL_INFORMATIONAL | APPLOGF_LEVEL_ERROR | APPLOGF_LEVEL_WARNING | APPLOGF_LEVEL_VERBOSE | APPLOGF_LEVEL_DEBUG)

	# log the cmd line arguments
	applog_d("Orig cmd line: {:s}".format(str(sys.argv)))
	applog_d("Processed cmd line: {:s}".format(str(g.args)))


#
# Converts counted utf-16 MTP string to unicode string
#
def mtpCountedUtf16ToPythonUnicodeStr(data):
	# format of string: first byte has character length of string inlcuding NULL (# bytes / 2)
	if not data:
		return "", 0
	(utf16CharLenIncludingNull,) = struct.unpack('<B', data[0:1])
	if utf16CharLenIncludingNull ==  0:
		# count byte of zero indicates no string.
		return "", 1
	
	utf16ByteLenIncludingNull = utf16CharLenIncludingNull*2
	unicodeStr = six.text_type(data[1:1+utf16ByteLenIncludingNull-2], 'utf-16')
	
	# some Nikon strings have trailing NULLs for padding - remove them
	for charPos in reversed(xrange(len(unicodeStr))):
		if unicodeStr[charPos] != '\x00':
			break;
	unicodeStr = unicodeStr[0:charPos+1]	# ok if original string was null-only string
	
	return unicodeStr, 1+utf16ByteLenIncludingNull	# 1+ for first byte containing character length
	

#
# Removes specified leading characters from string
#
def removeLeadingCharsFromStr(str, charsToRemoveSet):
	for charPos in xrange(len(str)):
		if str[charPos] not in charsToRemoveSet:
			break;
	return str[charPos:]


#
# Converts a raw MTP-obtained counted array of values into a list format
# of string: first word has count of entries, followed by array of entries,
# each of which is 'elementSizeInBytes' in size. Returns (list, bytesConsumedFromData),
# where 'list' is the list of entries and 'bytesConsumedFromData' is the number of
# bytes used from 'data' to generate the list
#
def parseMtpCountedList(data, elementSizeInBytes):

	elementSizeToUnpackStr = { 1 : 'B', 2 : 'H', 4 : 'I' }

	theList = list()
	(countEntries,) = struct.unpack('<I', data[0:4])
	offset = 4
	for entryIndex in xrange(countEntries):
		(entry,) = struct.unpack('<' + elementSizeToUnpackStr[elementSizeInBytes], data[offset:offset+elementSizeInBytes])
		offset += elementSizeInBytes
		theList.append(entry)
	return theList, countEntries*elementSizeInBytes + 4		# +4 to include count field itself
def parseMtpCountedWordList(data):
	return parseMtpCountedList(data, 4)
def parseMtpCountedHalfwordList(data):
	return parseMtpCountedList(data, 2)


#
# parses the raw data from MTP_OP_GetStorageIDs into a MptStorageIds tuple
#	
def parseMptStorageIds(data):
	(storageIdsList,bytesConsumed) = parseMtpCountedWordList(data)
	return MptStorageIdsTuple(storageIdsList)


#
# parses the raw data from MTP_OP_GetStorageInfo into a MtpStorageInfo tuple
#		
def parseMtpStorageInfo(data):
	(storageType,fileSystemType,accessCapability,maxCapacityBytes,freeSpaceBytes,freeSpaceInImages,storageDescription) = struct.unpack('<HHHQQIB', data[0:27])
	(volumeLabel,byteLen) = mtpCountedUtf16ToPythonUnicodeStr(data[27:])	
	return MtpStorageInfoTuple(storageType, fileSystemType, accessCapability, maxCapacityBytes,
						freeSpaceBytes, freeSpaceInImages, storageDescription, volumeLabel)						
	

#
# parses the raw data from MTP_OP_GetDeviceInfo into a MtpDeviceInfo tuple
#			
def parseMtpDeviceInfo(data):

	(standardVersion, vendorExtensionID, vendorExtensionVersion) = struct.unpack('<HIH', data[0:8])
	
	offset = 8
	(vendorExtensionDescStr,bytesConsumed) = mtpCountedUtf16ToPythonUnicodeStr(data[offset:])
	offset += bytesConsumed
	offset += 2			# skip 'FunctionalMode' field
	
	(operationsSupportedList,bytesConsumed) = parseMtpCountedHalfwordList(data[offset:])
	offset += bytesConsumed
	
	(eventsSupportedList,bytesConsumed) = parseMtpCountedHalfwordList(data[offset:])
	offset += bytesConsumed
	
	(devicePropertiesSupportedList,bytesConsumed) = parseMtpCountedHalfwordList(data[offset:])
	offset += bytesConsumed
	
	(captureFormatsSupportedList,bytesConsumed) = parseMtpCountedHalfwordList(data[offset:])
	offset += bytesConsumed
	
	(imageFormatsSupportedList,bytesConsumed) = parseMtpCountedHalfwordList(data[offset:])
	offset += bytesConsumed

	(manufacturerStr,byteLen) = mtpCountedUtf16ToPythonUnicodeStr(data[offset:])
	offset += byteLen
	(modelStr,byteLen) = mtpCountedUtf16ToPythonUnicodeStr(data[offset:])
	offset += byteLen
	(deviceVersionStr,byteLen) = mtpCountedUtf16ToPythonUnicodeStr(data[offset:])
	offset += byteLen
	(serialNumberStr,byteLen) = mtpCountedUtf16ToPythonUnicodeStr(data[offset:])
	serialNumberStr = removeLeadingCharsFromStr(serialNumberStr, {' ', '0'}) # remove leading spaces/zeros from serial number

	return MtpDeviceInfoTuple(	standardVersion, vendorExtensionID, vendorExtensionVersion, vendorExtensionDescStr,\
						set(operationsSupportedList), set(eventsSupportedList), set(devicePropertiesSupportedList), \
						set(captureFormatsSupportedList), set(imageFormatsSupportedList), manufacturerStr, \
						modelStr, deviceVersionStr, serialNumberStr)	


#
# called within application wait loops, this method makes
# sure we keep the MTP session alive by periodically sending
# an MTP request. without such requests many cameras will
# drop the MTP session, including Nikon cameras. the first
# call to this function should be with None - the function
# will return an opaque value that is actually a timestamp
# of when we were last called. the caller should
# periodically call this function thereafter with whatever
# return value we last give it - when enough time has elapsed
# we'll send an MTP command to keep the session alive
#						
def mtpSessionKeepAlive(timeProbeLastSent):
	timeCurrent = time.time()
	if timeProbeLastSent == None:
		return timeCurrent
	if timeCurrent - timeProbeLastSent < 5:
		return timeProbeLastSent
	#
	# send an MTP command to keep session alive. I wanted to use
	# sendProbeRequest() since it's lightweight and seemingly made
	# for that purpose but Sony cameras will still time'out
	# the session if we just send those
	#
	mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetDeviceInfo)
	return timeCurrent


#
# parses the raw data from MTP_OP_GetObjectInfo into a MtpObjectInfo tuple
#									
def parseMtpObjectInfo(data):

	(storageId, objectFormat, protectionStatus) = struct.unpack('<IHH', data[0:8])
	(objectCompressedSize, thumbFormat, thumbCompressedSize) = struct.unpack('<IHI', data[8:18])
	(thumbPixWidth, thumbPixHeight, imagePixWidth, imagePixHeight) = struct.unpack('<IIII', data[18:34])			
	(imageBitDepth, parentObject, associationType) = struct.unpack('<IIH', data[34:44])
	(associationDesc, sequenceNumber) = struct.unpack('<II', data[44:52])
				
	offset = 52
	(filename, bytesConsumed) = mtpCountedUtf16ToPythonUnicodeStr(data[offset:])
	offset = offset + bytesConsumed			
	(captureDateStr, bytesConsumed) = mtpCountedUtf16ToPythonUnicodeStr(data[offset:])
	captureDateStr = captureDateStr[:15] # Canon adds a ".0"... to the capture date/time - trim that off
	offset = offset + bytesConsumed
	(modificationDateStr, bytesConsumed) =  mtpCountedUtf16ToPythonUnicodeStr(data[offset:])
	modificationDateStr = modificationDateStr[:15] # Canon adds a ".0"... to the modification date/time - trim that off

	return MtpObjectInfoTuple(	storageId, objectFormat, protectionStatus, \
						objectCompressedSize, thumbFormat, thumbCompressedSize, \
						thumbPixWidth, thumbPixHeight, imagePixWidth, imagePixHeight, \
						imageBitDepth, parentObject, associationType, \
						associationDesc, sequenceNumber, filename, \
						captureDateStr, modificationDateStr)
						

#
# closes TCP/IP connection sockets to camera's MTP interface
#
def closeSockets():	
	if g.socketPrimary:
		g.socketPrimary.close()
		g.socketPrimary = None
	if g.socketEvents:
		g.socketEvents.close()
		g.socketEvents = None
		
#
# converts a GUID string to a pair of 64-bit values (high/low).
# the following string formats are support:
#		xxxxxxxx 			presumed hex characters specifying lower 64-bit of GUID
#		xxxxxxxx-yyyyyyyy 	presumed hex characters specifying both high (xx) and low (yy) parts of 128-bit GUID
#		xx:xx:xx:xx:xx:xx	presumed MAC address consisting of hex characters (for Sony)
#
def convertGuidStrToLongs(guidHexStr):
	if guidHexStr.find(':') != -1:
		#
		# GUID specified as a MAC address (for Sony). Sony cameras can either operate
		# in a host-selective mode where they'll only accept connections from a specific MAC
		# address or in a mode where they'll accept any GUID as long as the lower 6-bytes
		# of the GUID corresponding to area Sony uses to identify the MAC address are zero.
		# the logic here is when the user wants to run in the host-selective mode - it's
		# pretty much only for debugging.
		#
		
		
		# string are implicitly big endian. build as little endian and then convert
		# to big endian if necessary when done if we're running on a big-endian platform
		#
		macAddressFieldList = guidHexStr.split(':')
		guidLow = 0x0000000000000000
		for nthField in xrange(len(macAddressFieldList)):
			guidLow |= int(macAddressFieldList[nthField], 16) << nthField*8		
		if len(macAddressFieldList) == 6:
			# Sony preprends 0xFFFF to MAC addr to form the full 64-bit lower GUID
			guidLow = (guidLow<<16) | 0xFFFF
		if sys.byteorder == 'big':
			guidLow = strutil.invertEndian(guidLow)
		guidHigh = 0x0000000000000000
	else:
		posColon = guidHexStr.find('-')
		if posColon != -1:
			# upper 64-bits of GUID specified
			guidHigh = int(guidHexStr[:posColon], 16)
			guidLow = int(guidHexStr[posColon+1:], 16)
		else:
			guidHigh = 0x0000000000000000
			guidLow = int(guidHexStr, 16)
	return (guidHigh, guidLow)


#
# retrieves the count of MTP objects for a given storage ID
#
def getNumMtpObjects(storageId):
	#
	# note that Sony cameras require the optional parameters to MTP_OP_GetNumObjects - Canon/Nikon do not
	# oddly a given Sony wont always reject the absence of the optional parameters
	#
	mtpTcpCmdResult = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetNumObjects, struct.pack('<III', storageId, 0, 0)) 
	return mtpTcpCmdResult.mtpResponseParameter


#
# retrieves list of MTP object handles for a given storage ID
#
def getMtpObjectHandles(storageId):
	#
	# note that Sony cameras require the optional parameters to MTP_OP_GetObjectHandles - Canon/Nikon do not
	# oddly a given Sony wont always reject the absence of the optional parameters
	#
	mtpTcpCmdResult = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetObjectHandles, struct.pack('<III', storageId, 0, 0))
	(objHandlesList, bytesConsumed) = parseMtpCountedWordList(mtpTcpCmdResult.dataReceived)
	return objHandlesList


#
# retrieves the MTP object info for the specified handle
# 	
def getMtpObjectInfo(objHandle, fRetryErrors = True):

	#
	# it's been observed on Nikon bodies that if we attempt to issue a MTP_OP_GetObjectInfo
	# right after the object comes into existence then the camera may return a MTP_RESP_GeneralError.
	# the errors were observed to resolve within a second of the original MTP_OP_GetObjectInfo request
	# but we retry up to 5 seconds just in case there are other factors that may delay the object from
	# becoming ready
	#
	timeStart = secondsElapsed(None)
	while True:
		try:
			mtpTcpCmdResult = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetObjectInfo, struct.pack('<I', objHandle))
			return parseMtpObjectInfo(mtpTcpCmdResult.dataReceived)
		except mtpwifi.MtpOpExecFailureException as e:
			if fRetryErrors == False or e.mtpRespCode == MTP_RESP_COMMUNICATION_ERROR:
				# instructed not to retry or this is a communication error that isn't retried
				raise
			elapsedTimeSecs = secondsElapsed(timeStart)
			applog_d("getMtpObjectInfo() failed: {:s}, elaspsedTimeSecs={:.2f}".format(getMtpRespDesc(e.mtpRespCode), elapsedTimeSecs))			
			if elapsedTimeSecs >= 5:
				raise
			time.sleep(.25) # wait 1/4 second before retrying


#
# uses SSDP discovery to get the IP address of the first camera that responds.
# Returns the IP address string if found or None if not found
#		
def ssdpDiscoverCameraIpAddress():

	#
	# generate service list
	#
	ssdpServiceNames = [ "urn:microsoft-com:service:MtpNullService:1", 		# Sony
		"urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1"	# Canon
	]
	if g.args['ssdp_addservice']:
		ssdpServiceNames = ssdpServiceNames + g.args['ssdp_addservice']
	
	consoleWriteLine("Searching for a Sony or Canon camera via SSDP ")
	try:
		ssdpMessage = ssdp.discover(ssdpServiceNames, lambda ssdpMessage : ssdp.extractIpAddressFromSSDPMessage(ssdpMessage) != None,\
			g.args['ssdp_discoveryattempts'], g.args['ssdp_discoverytimeoutsecsperattempt'], g.args['ssdp_discoveryflags'], g.args['ssdp_addmulticastif'])
		if ssdpMessage  == None:
			raise ssdp.DiscoverFailureException(\
				"No camera found via SSDP Discovery. For Sony cameras please make the camera\n"\
				"is in the 'Send to Computer' WiFi mode.")			
	except ssdp.DiscoverFailureException as e:
		raise ssdp.DiscoverFailureException(">> Connection Failed <<\n\n" + str(e)) # prepend "Connection Failed" message to exception text
	finally:
		consoleClearLine()
	
	ipAddrStr = ssdp.extractIpAddressFromSSDPMessage(ssdpMessage)
	applog_i("Found camera at IP address " + ipAddrStr)
	return ipAddrStr
	
	
#
# starts an MTP session with the camera, including opening the TCP/IP
# socket connections, sending the MTP-WiFi host introduction primitive,
# and performing an MTP_OP_OpenSession
#		
def startMtpSession():

	(guidHigh,guidLow) = convertGuidStrToLongs(g.args['initcmdreq_guid'])
	
	#
	# discover camera/IP address if configured to do so
	#
	if g.args['ipaddress'] == "auto":
		ipAddressStr = ssdpDiscoverCameraIpAddress()
	else:
		ipAddressStr = g.args['ipaddress']
	
	#
	# open TCP/IP socket connection to camera
	#
	g.socketPrimary = mtpwifi.openConnection(ipAddressStr, True, g.args['connecttimeout'], g.args['socketreadwritetimeout'])

	#
	# get session ID
	#
	data = mtpwifi.sendInitCmdReq(g.socketPrimary, (guidHigh, guidLow), g.args['initcmdreq_hostname'], g.args['initcmdreq_hostver'])
	(g.sessionId,) = struct.unpack('<I', data[:4])
	applog_d("Session ID = 0x{:08x}".format(g.sessionId))
		
	#
	# open secondary socket for events
	#
	g.socketEvents = mtpwifi.openConnection(ipAddressStr, False, g.args['connecttimeout'], g.args['socketreadwritetimeout'])
	data = mtpwifi.sendInitEvents(g.socketEvents, g.sessionId)

	#
	# send a probe request on the event socket (not sure why this
	# is reqiured but failing to do so will cause the MTP session
	# to hang unless I replace the probe with a one-second delay)
	#
	mtpwifi.sendProbeRequest(g.socketEvents)
	
	#
	# get device information, which is needed now because some cameras
	# might require non-standard handling unique to their model
	#
	getMtpDeviceInfo()
	
	#
	# open session. Some newer Nikon cameras like the J5 return 0x0 for the session ID
	# from MTP_TCPIP_REQ_INIT_CMD_REQ, which the camera then rejects. The camera appears
	# to accept any non-zero session ID - Nikon's WMU uses a 0x1 so that's what we'll use
	# as well if the camera rejects the session ID we got from MTP_TCPIP_REQ_INIT_CMD_REQ
	#
	
	if g.args['opensessionid'] == None:
		fSessionIdFromCmdLine = False
	else:
		# cmd-line option to use specific session ID (mostly for debugging)
		fSessionIdFromCmdLine = True
		g.sessionId = g.args['opensessionid']		
	while True:
		try:
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_OpenSession, struct.pack('<I', g.sessionId))
			break # successful
		except mtpwifi.MtpOpExecFailureException as e:
			if not fSessionIdFromCmdLine and e.mtpRespCode != MTP_RESP_COMMUNICATION_ERROR:
				applog_d("MTP_OP_OpenSession failed: {:s} for sessionID 0x{:08x}".format(getMtpRespDesc(e.mtpRespCode), g.sessionId))
				if g.sessionId != 0x1:
					applog_d("Retrying MTP_OP_OpenSession with hard-coded ID of 0x1 (for some Nikons)")
					g.sessionId = 0x1
					continue
			# failed
			raise
		
	g.openSessionTimeEpoch = time.time()
	
	
#
# notifies the user via the camera that an airnefcmd transfer sequence is starting,
# for cameras that don't automatically notify the user of this
#	
def notifyCameraUserTransferSessionStarting():

	if g.cameraMake == CAMERA_MAKE_SONY:
		#
		# this causes the "Sending..." message on the 'Send to Computer' screen on the
		# camera. it was discovered by capturing a wireless session between a Sony camera
		# and Sony's Auto Import utility for OSX. note that all MTP_OP_Sony_Set_Request
		# operations be followed by a MTP_OP_Sony_Get_Request, otherwise the camera
		# reports MTP_RESP_DeviceBusy for all subsequent MTP_OP_Sony_Get_Request attempts
		#
		if g.args['sonyuniquecmdsenable'] & SONY_UNQIUECMD_ENABLE_SENDING_MSG:
			data = struct.pack('<5IB', 0x00000002, 0x00000002, 0x00000000, 0x00000000, 0x00020001, 0x00)
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Sony_Set_Request, struct.pack('<I', 0x4), data)
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Sony_Get_Request, struct.pack('<I', 0x4))

#
# notifies the user via the camera that an airnefcmd transfer sequence has ended
# for cameras that don't automatically notify the user of this.
#	
def notifyCameraUserTransferSessionEnding():

	if g.cameraMake == CAMERA_MAKE_SONY:
		#
		# Sony only supports one MTP session per user-initiaited 'Send to Computer'
		# sequence. If you attempt a second session the camera will accept the TCP/IP
		# socket connection but will not respond to the MTP_TCPIP_REQ_INIT_CMD_REQ.
		# The user is required to cancel out of 'Send to Computer' and then go back
		# into it for the camera to accept another MTP session. This is rather messy
		# and most users would be annoyed by it so as an alternative we put the camera
		# into slee mode at the end of a session, which guarantees that the camera
		# is kicked out of 'Send to Computer' mode. It has an additional benefit of
		# serving as a means to notify the user when the transfers are over, which is
		# useful for psuedo-realtime download support we implement for Sony cameras,
		# where the user has to go into 'Send to Computer' while shooting whenever he
		# wants to transfer images he's taken since our last download invocation during
		# this app session - putting the camera to sleep lets the user know all files
		# have been downloaded and he can continue shooting
		#
		# The sleep sequence wsa discovered by capturing a wireless session between a Sony
		# camera and Sony's Auto Import utility for OSX. The sequence the Auto Import utility
		# issues starts with the Sony commands in notifyCameraUserTransferSessionStarting(),
		# which causes a "Sending..." message to be displayed on the 'Send to Computer'
		# screen on the camera. After that the Auto Import utility issues a few more commands,
		# one of which it's not clear what it does, followed by another which causes
		# a "The saving process has been cancelled." message and then finally the command
		# that puts the camera into sleep mode. 
		#

		#
		# don't know what this does - it doesn't appear to have an effect on the camera but
		# is issued by Sony's Auto Import utility after the command that displays "Sending..."
		# on the LCD
		#
		if g.args['sonyuniquecmdsenable'] & SONY_UNQIUECMD_ENABLE_UNKNOWN_CMD_1:
			data = struct.pack('<4I3B', 0x00000000, 0x00000003, 0x00000000, 0x00000000, 0x02, 0x00, 0x30)
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Sony_Set_Request, struct.pack('<I', 0x4), data)
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Sony_Get_Request, struct.pack('<I', 0x4))

		#
		# this command causes a "The saving process has been cancelled." message to be displayed
		# on the LCD. The command only works if the command that displays "Sending..." is sentinel
		# first, otherwise it has no effect
		#
		if g.args['sonyuniquecmdsenable'] & SONY_UNQIUECMD_ENABLE_SAVING_PROCESS_CANCELLED_MSG:
			data = struct.pack('<4I3B', 0x00000000, 0x00000004, 0x00000000, 0x00000000, 0x02, 0x00, 0x00)
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Sony_Set_Request, struct.pack('<I', 0x4), data)
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Sony_Get_Request, struct.pack('<I', 0x4))			
					
		#
		# this causes the camera to leave 'Send to Computer' mode and sleep. this is necessary because the
		# camera only supports one MTP session per connection and if we try another one it'll
		# hang on the MTP_TCPIP_REQ_INIT_CMD_REQ when we try another session
		#
		if g.args['camerasleepwhendone'] == 'yes':
			data = struct.pack('<4I3B', 0x00000000, 0x00000005, 0x00000000, 0x00000000, 0x02, 0x00, 0x30)
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Sony_Set_Request, struct.pack('<I', 0x4), data)
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Sony_Get_Request, struct.pack('<I', 0x4))
		
		
#
# sends the high-level MTP_OP_CloseSession primitive to close the session 
# with the camera
#	
def endMtpSession():

	notifyCameraUserTransferSessionEnding()

	#
	# issue close session. There is a bug on Nikon cameras where if we end the session too
	# soon after starting one the camera will not respond to a subsequent MTP_TCPIP_REQ_INIT_CMD_REQ
	# the next time we connect to the camera. This typically only happens during airnef development since
	# not many user cases have us exiting less than 1 second before starting. But it's annoying for
	# me to have to keep cycling the WiFi on the camera during development :) So the fix is to delay
	# issuing the end session so that we allow a full second to elapse from the time the session was started.
	# I've seen this issue on a D7200 and J5 - it likely occurs on most/all of their cameras. I'm guessing
	# there's some deferred session-start processing in the camera that doesn't execute in time if we
	# end the session quickly. It can also be avoided if we delay between the time of issuing the
	# MTP_TCPIP_REQ_INIT_CMD_REQ and starting the session but then that delay would impact every
	# invocation (it actually was in v1.00 until I figured out a MTP_TCPIP_REQ_PROBE worked around the
	# start session issue)
	#
	secsElapsedSinceOpenSession = secondsElapsed(g.openSessionTimeEpoch)
	if secsElapsedSinceOpenSession < 1:
		applog_d("endMtpSession(): Delaying for {:.2f} seconds to work around Nikon bug".format(1 - secsElapsedSinceOpenSession))
		time.sleep(1 - secsElapsedSinceOpenSession)
	mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_CloseSession)

#
# called when we determine the make of a camera, this method sets internal flags
# that will control any make-sepcific behavior/logic 
#
def processCameraMakeDetermination():
	if g.args['rtd_pollingmethod'] != None:
		g.realtimeDownloadMethod = g.args['rtd_pollingmethod']
	else:
		if g.cameraMake == CAMERA_MAKE_NIKON:
			g.realtimeDownloadMethod = REALTIME_DOWNLOAD_METHOD_NIKON_EVENTS
		elif g.cameraMake == CAMERA_MAKE_SONY:
			g.realtimeDownloadMethod = REALTIME_DOWNLOAD_METHOD_SONY_EXIT
		else:
			g.realtimeDownloadMethod = REALTIME_DOWNLOAD_METHOD_MTPOBJ_POLLING


#
# performs a MTP_OP_GetDeviceInfo and saves the information into g.mtpDeviceInfo
#
def getMtpDeviceInfo():
	mtpTcpCmdResult = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetDeviceInfo)	
	mtpDeviceInfo = parseMtpDeviceInfo(mtpTcpCmdResult.dataReceived)
	if g.mtpDeviceInfo:
		# this is a retry invocation. make sure we're talking with the same camera as before
		if mtpDeviceInfo != g.mtpDeviceInfo:
			applog_e("Discovered different camera during retry invocation. Orig camera was Model \"{:s}\", S/N \":{:s}\", New camera is \"{:s}\", S/N \":{:s}\"".format(\
				g.mtpDeviceInfo.modelStr, g.mtpDeviceInfo.serialNumberStr, mtpDeviceInfo.modelStr, mtpDeviceInfo.serialNumberStr))
			sys.exit(ERRNO_DIFFERENT_CAMREA_DURING_RETRY)
	
	g.mtpDeviceInfo = mtpDeviceInfo
	applog_d(g.mtpDeviceInfo)
	
	#
	# determine make of camera for use in any make-specific logic in our app
	#
	makeStrUpper = g.mtpDeviceInfo.manufacturerStr.upper()	
	if makeStrUpper.find("NIKON") != -1:
		g.cameraMake = CAMERA_MAKE_NIKON
	elif makeStrUpper.find("CANON") != -1:
		g.cameraMake = CAMERA_MAKE_CANON
	elif makeStrUpper.find("SONY") != -1:
		g.cameraMake = CAMERA_MAKE_SONY
	else:
		g.cameraMake = CAMERA_MAKE_UNDETERMINED
				
	#
	# set any program options/behavior that is specific to the make of the camera 
	#
	processCameraMakeDetermination()


	#
	# build path (dir + rootfilename) that will serve as the template for all metadata
	# files we create and store locally. this name needs to be unique to the camera
	# attached and locatable on future invocations, so we use a combination of the camera
	# model and serial number
	#	
	g.cameraLocalMetadataPathAndRootName = os.path.join(g.appDataDir, "{:s}-SN{:s}".format(g.mtpDeviceInfo.modelStr, g.mtpDeviceInfo.serialNumberStr))
	
	applog_i("Camera Model \"{:s}\", S/N \"{:s}\"".format(g.mtpDeviceInfo.modelStr, g.mtpDeviceInfo.serialNumberStr))

	
#
# gets the slot index (1 or 2) from an MTP storage ID
#
def getSlotIndexFromStorageId(storageId):
	return storageId>>16
		

#
# selects the storage ID on the camera (ie, media card/slot) to use for this session
#	
def selectMtpStorageId():

	mtpTcpCmdResult = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetStorageIDs)
	mtpStorageIds = parseMptStorageIds(mtpTcpCmdResult.dataReceived)
	
	countCardSlots = len(mtpStorageIds.storageIdsList)

	applog_d("All Storage IDs:")
	for i in xrange(0, len(mtpStorageIds.storageIdsList)):
		applog_d("  storageId[{:d}] = 0x{:08x}".format(i, mtpStorageIds.storageIdsList[i]))
		
	# build a bitmap of which cards slots have media cards
	cardsPresentBitmap = 0x00
	firstCardPresent = -1
	countCardsPresent = 0
	for i in xrange(0, countCardSlots):
		if (mtpStorageIds.storageIdsList[i] & MTP_STORAGEID_PresenceBit):
			if firstCardPresent == -1:
				firstCardPresent = i
			cardsPresentBitmap |= 1<<i
			countCardsPresent += 1
			
			
	if not cardsPresentBitmap:
		applog_e("There are no media card(s) present or card(s) are busy!")
		sys.exit(ERRNO_NO_CARD_MEDIA_AVIALABLE)
		
	if g.args['slot'] == 'firstfound':
		# use first slot that's populated
		storageId = mtpStorageIds.storageIdsList[firstCardPresent]
		countCardsUsed = 1
	elif g.args['slot'] == 'first' or g.args['slot'] == 'second':		
		if g.args['slot'] == 'second' and countCardSlots <= 1:
			applog_e("Second card slot specified but camera only has one card slot!")
			sys.exit(ERRNO_NO_CARD_MEDIA_AVIALABLE)
		storageId = mtpStorageIds.storageIdsList[0 if g.args['slot'] == 'first' else 1]
		if (storageId & MTP_STORAGEID_PresenceBit) == 0:
			applog_e("No card present in specified slot or card is busy!")
			sys.exit(ERRNO_NO_CARD_MEDIA_AVIALABLE)
		countCardsUsed = 1			
	else: # both card slots to be used
		storageId = MTP_STORAGEID_ALL_CARDS
		countCardsUsed = countCardsPresent
	applog_d("  storageId to be used for this invocation: {:08x} [cardsPresentBitmap=0x{:04x}]".format(storageId, cardsPresentBitmap))
	g.countCardsUsed = countCardsUsed
	g.storageId = storageId
	g.mtpStorageIds = mtpStorageIds

	
#
# performs a MTP_OP_GetStorageInfo and saves the information into g.mtpStorageInfoList
#
def getMtpStorageInfo():
	g.mtpStorageInfoList = []
	if g.storageId != MTP_STORAGEID_ALL_CARDS:
		mtpTcpCmdResult = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetStorageInfo, struct.pack('<I', g.storageId))
		mtpStorageInfo = parseMtpStorageInfo(mtpTcpCmdResult.dataReceived)
		applog_d(mtpStorageInfo)
		g.mtpStorageInfoList.append(mtpStorageInfo)
	else:
		countCardSlots = len(g.mtpStorageIds.storageIdsList)
		for i in xrange(0, countCardSlots):
			storageId = g.mtpStorageIds.storageIdsList[i]
			if (storageId & MTP_STORAGEID_PresenceBit):				
				mtpTcpCmdResult = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetStorageInfo, struct.pack('<I', storageId))
				mtpStorageInfo = parseMtpStorageInfo(mtpTcpCmdResult.dataReceived)
				applog_d(mtpStorageInfo)
				g.mtpStorageInfoList.append(mtpStorageInfo)

				
#
# attempts deletion of a file, ignoring any errors
#
def deleteFileIgnoreErrors(filename):
	try:
		os.remove(filename)
	except:
		pass


#
# generates and saves a cache of all the MtpObjectInfo(s) we've retrieved this session.
# this is done to avoid having to re-retrieve these same MtpObjectInfo instances from
# the camera on subsequent sessions. we generate the cache by serializing the 
# MtpObjectInfo instances (and handle instances) via python's pickle's module. 
#		
MtpObjectInfoCacheTuple = namedtuple('MtpObjectInfoCacheTuple', 'mtpObjectInfoList objHandlesList timeSavedEpoch')
def saveMtpObjectsToDiskCache():

	if g.args['mtpobjcache'] == 'disabled' or g.args['mtpobjcache'] == 'readonly':
		return None	
	
	mtpObjectInfoCacheFilename = g.cameraLocalMetadataPathAndRootName + "-objinfocache"

	#
	# build mtpObjectInfoList[] and objHandlesList[] from the mtpObject entries that were
	# inserted by buildMtpObjects(). I'm rebuilding the lists here rather than using the
	# locally-available lists in buildMtpObjects() because I wanted this routine to
	# be callable in the future outside of just buildMtpObjects()
	#
	mtpObjectInfoList = []
	objHandlesList = []
	countObjs = MtpObject.getCount()
	mtpObject = MtpObject.getOldest()
	for nObjInex in xrange(0, countObjs):
		mtpObjectInfoList.append(mtpObject.mtpObjectInfo)
		objHandlesList.append(mtpObject.mtpObjectHandle)
		mtpObject = mtpObject.getNewer()
		
	#
	# generate the named-tuple (structure) that we'll be serializing to disk. this tuple
	# contains the mtpObjectInfoList[] and objHandlesList[] lists generated above, plus
	# a timestamp that can be used to evaluate the age of the cache in future invocations
	#
	mtpObjectInfoCacheTuple = MtpObjectInfoCacheTuple(mtpObjectInfoList, objHandlesList, time.time())

	#
	# build a hash of the tuple, which will be saved in the serialization data with the tuple. this
	# hash will allow us to validate the integirty of the serialized data when we use load it
	# on subsequent invocations to use as a cache. this validation is to protect against:
	#
	# -> Corruption of the cache data if the user inadvertently modifies the file holding the data
	# -> Future changes to the content of the cache data (a version number would work but since we're already generating the hash....)
	# -> Future changes to the python pickle implementation or the algorithm we use
	#
	# when loadMtpObjectsInfoCache() load this serialization data he generates a hash of the loaded
	# data and compares it against the hash that was generated+saved here
	#
	mtpObjectInfoCacheAsPickleBytes = pickle.dumps(mtpObjectInfoCacheTuple)	# generate byte array of the tuple
	hashOfMtpObjectInfoCacheTuple = hashlib.sha512(mtpObjectInfoCacheAsPickleBytes).hexdigest()	# generate a SHA-512 hash digest, represented in hex ASCII

	#
	# write the serialization data. if any error occurs, either I/O error or pickling/code error,
	# we close the file and delete it, to prevent any partially-written cache data from lingering
	# on disk. any error is treated as benign since the cache is not essential to the operation
	# of the program - it's only a performance optimization
	#
	try:
		fMtpObjectCache = open(mtpObjectInfoCacheFilename, "wb")
		fMtpObjectCache.write(mtpObjectInfoCacheAsPickleBytes)			# write the tuple. note we're using the already-pickled data instead of calling dump(). this is for performance
		pickle.dump(hashOfMtpObjectInfoCacheTuple, fMtpObjectCache)		# write the SHA-512 hash digest
		fMtpObjectCache.close()
	except IOError as e:
		if fMtpObjectCache:
			fMtpObjectCache.close()				
		applog_e("I/O error writing obj hash to {:s}, cache will not be available next session: {:s}".format(mtpObjectInfoCacheFilename, str(e)))
		deleteFileIgnoreErrors(mtpObjectInfoCacheFilename)	# delete cache in case some (partial) data was written before exception
	except (ImportError, pickle.PickleError, ValueError, AttributeError):
		# ImportError if the serialized data refers to a module that doesn't exist (changed module names between versions)
		# PickleError if the decoding of the serialized data failed (corrupt data, modified format between versions, etc...
		# ValueError if importing from different pickle protoocl
		applog_d("Exception serializing obj cache:\n")
		applog_d(traceback.format_exc())	
		if fMtpObjectCache:
			fMtpObjectCache.close()				
		applog_e("Non-I/O error generating obj hash to {:s}, cache will not be saved.".format(mtpObjectInfoCacheFilename))
		deleteFileIgnoreErrors(mtpObjectInfoCacheFilename)	# delete cache in case some (partial) data was written before exception
	applog_d("Saved {:d} MTP objects to disk cache".format(countObjs))

#
# loads the MtpObjectInfo cache info that was saved to disk on a previous session by
# saveMtpObjectsToDiskCache(). if the cache is loaded successfully and passes the
# hashed integrity check then a MtpObjectInfoCacheTuple is returned. note that 
# even if the cache is loaded successfully the caller must perform his own coherency
# check to make sure the cache contents are valid vs the objects on the camera. 
#
def loadMtpObjectInfoCacheFromDisk():

	if g.args['mtpobjcache'] == 'disabled':
		return None	

	mtpObjectInfoCacheFilename = g.cameraLocalMetadataPathAndRootName + "-objinfocache"
	
	#
	# read  the serialization data. if any error occurs, either I/O error or pickling/code error 
	# we close the file. we only delete the file if the hash is corrupt; that way the cache will
	# still be available on future invocations in case the I/O error we got here was transitory (even
	# though the file is about to get rewritten anyway once we fetch the objects from the camera and
	# later call saveMtpObjectsToDiskCache). any error is treated as benign since the cache is not
	# essential to the operation of the program - it's only a performance optimization
	#	
	if os.path.exists(mtpObjectInfoCacheFilename):
		if g.args['mtpobjcache'] == 'writeonly':
			applog_v("Ignoring found MTP object cache file per user configuration")
			return None
		fMtpObjectCache = None # needed so that exception handlers can know whether the file was opened before the exception and thus needs closing
		try:
			fMtpObjectCache = open(mtpObjectInfoCacheFilename, "rb")
			mtpObjectInfoCacheTuple = pickle.load(fMtpObjectCache)
			hashOfMtpObjectInfoCacheTuple_Loaded = pickle.load(fMtpObjectCache)
			fMtpObjectCache.close()
			
			mtpObjectInfoCacheAsPickleBytes = pickle.dumps(mtpObjectInfoCacheTuple)
			hashOfMtpObjectInfoCacheTuple_Calculated = hashlib.sha512(mtpObjectInfoCacheAsPickleBytes).hexdigest()
		except IOError as e:
			if fMtpObjectCache:
				fMtpObjectCache.close()				
			applog_e("I/O error reading obj hash from {:s}: {:s}".format(mtpObjectInfoCacheFilename, str(e)))
			return None
		except:
			# ImportError if the serialized data refers to a module that doesn't exist (changed module names between versions)
			# PickleError if the decoding of the serialized data failed (corrupt data, modified format between versions, etc...
			# ValueError if importing from different pickle protocol
			# AttributeError if the module name associated with the class/type objects being deserialized can't be found/mismatch
			# plus any others that the pickle case may throw - need a generic "except" in case I missed any, otherwise we'll
			# ungracefully throw an exception that terminates the app for what should be handled as discarded-cache case
			
			#
			# note: in v1.1 we moved the appdata for OSX out of app bundle and into user's home directory. this means the data
			# will be shared between the frozen OSX app and any non-frozen version of airnef run on the same machine (ie, running
			# airnef from source instead of OSX app). in the frozen app this module runs as airnefcmd (__name__ == airnefcmd) due
			# to the OSX wrapper importing it and executing it rather than airnefcmd being the main execution module,
			# whereas in all other cases on other platforms and OSX non-frozen this module runs as __main__. this v1.1 change causes
			# the OSX frozen app's picke load of the objcache to fail with an AttributeError, because the top-level module
			# associated with 'MtpObjectInfoCacheTuple' will be different (c__main__ vs cairnefcmd). one fix would be to move
			# the defintion of 'MtpObjectInfoCacheTuple' into its own module, that way the module in the pickle data would be 
			# the same no matter how airnefcmd was run. the problem with this is that the pickle data wouldn't be backwards
			# compatible with v1.0, which is fine except v1.0 wasn't catching the 'AttributeError' exception for the pickle load,
			# which means it'll throw an uncaptured exception rather than gracefully discarding the cache and recreate it. for
			# this reason I'm going to keep the situation as-is and let the OSX frozen vs non-frozen executions recreate the
			# cache upon experiencing the AttributeError, since that's gracefully handled now in v1.1. plus I don't expect
			# many users to be running both OSX frozen and non-frozen, and esp not switching between them enough to make the
			# cache recreation a (performance) issue
			#
			applog_d("Exception deserializing obj cache:\n")
			applog_d(traceback.format_exc())	
			if fMtpObjectCache:
				fMtpObjectCache.close()				
			applog_e("Non-I/O error reading obj hash from {:s}. Cache will be discarded. (err={:s})".format(mtpObjectInfoCacheFilename, str(sys.exc_info()[0])))
			deleteFileIgnoreErrors(mtpObjectInfoCacheFilename) # delete the potentially corrupt cache
			return None

		#
		# cache was read successfully. verify its integrity
		#
		if hashOfMtpObjectInfoCacheTuple_Loaded != hashOfMtpObjectInfoCacheTuple_Calculated:			
			applog_e("Obj cache in {:s} is corrupt - will delete and ignore".format(mtpObjectInfoCacheFilename))
			fMtpObjectCache.close()
			deleteFileIgnoreErrors(mtpObjectInfoCacheFilename)	# delete the corrupt cache
			return None
			
		#
		# have valid cache
		#
		cacheAgeSeconds = secondsElapsed(mtpObjectInfoCacheTuple.timeSavedEpoch)
		
		# display cache info (verbose/debug)
		applog_v("MTP Object cache has {:d} objects, age is {:s}".\
			format(len(mtpObjectInfoCacheTuple.mtpObjectInfoList), str(datetime.timedelta(seconds=cacheAgeSeconds))))
		if isDebugLog():
			applog_d("MTP object cache entries [count={:d}]".format(len(mtpObjectInfoCacheTuple.mtpObjectInfoList)))
			for i in xrange(len(mtpObjectInfoCacheTuple.mtpObjectInfoList)):
				applog_d("Entry {:4d}, handle = 0x{:08x}: {:s}".format(i, mtpObjectInfoCacheTuple.objHandlesList[i], str(mtpObjectInfoCacheTuple.mtpObjectInfoList[i])))
				
		#
		# ignore (discard) cache if its older than the max configured age
		#
		if g.args['mtpobjcache_maxagemins'] != 0 and cacheAgeSeconds/60 >= g.args['mtpobjcache_maxagemins']:
			applog_v("Discarding MTP object cache due to age (max age is {:s})".format(str(datetime.timedelta(minutes=g.args['mtpobjcache_maxagemins']))))
			return None
			
		return mtpObjectInfoCacheTuple
			
	else:
		return None


#
# Loads the MPT object info cache from the previous session (if available) and validates
# the cache's coherency. The coherency must be checked because MTP object handles
# aren't guaranteed to be persistent across camera power cycles (per the MTP spec), which
# means an obj handle may refer to a different file on the camera than what we have
# cached from the previous airnef session. This makes the entire proposition of caching
# these objs a bit risky, but the performance beneifts are too great to ignore because
# MTP_OP_GetObjectInfo can operate very slowly on some Nikon bodies. Based on my
# experimentation both Nikon and Canon encode object handles based on the filename
# and/or directory, the slot the media card is in, etc... This of course means that
# object handles can be reused and become stale relative to our cache, such as when
# users reformat cards and the same directory and filenames get reused to new images.
# What's needed is a way to detect when the camera might have reused an object handle
# in this fashion, short of performing MTP_OP_GetObjectInfo for all handles and defeating
# the purporse of the cache in the first place. The solution I came up with is to perform
# a spot check of just the directory objects, ie we perform MTP_OP_GetObjectInfo's for
# the directories we have in our cache, and compare the downloaded copies to our cache.
# If any directory object mismatches, specifically the timestamps, this means it's
# nearly certain that we have a a stale object cache and need to discard it.
#
# The directory timestamps will mismatch for any number of reasons, some of which
# are listed below. All signify a stale cache except for #3, which we'll still
# invalidate for since it doesn't make sense to get tricky for such an uncommon usage case.
#
#   1) There's a different media card in the camera
#   2) The user formatted the same media card
#   3) The user moved the media card to a different slot (on Nikon this flips a bit in the handles)
#   3) The user modified one or more files with the card inserted in an SD reader (unlikely)
#
# It's important to note some observations about how Nikon and Camera maintain timestamps on
# folders. On Nikon, the base DCIM directory uses a fixed timestamp of "19800000T000000" and
# the timestamp is never updated. This would be bad since we're relying on the timestamps for
# this algorithm; luckily this behavior is limited to the base DCIM directory. For all
# subdirectories under DCIM (that actually hold images), Nikon sets the timestamp of the folder
# at the time the folder is created, either after a card format or when a new folder is created
# when the image count in a folder exceeds 999 or 9999. Luckily nether Canon or Nikon keep
# the timestamps of these subfolders updated thereafter - they always keep the same timestamp
# even when images are being added to them (technically a filesystem's folder timestamp should
# update when any file within it is updated - they're probably avoiding doing so for performance
# reasons) - this is lucky for us because if they were to update the timestampsthen our algorithm
# would always find mismatching folder timestamps whenever there are new images in the folder.
# Note that any new directories on the camera (not in our cache) don't influence the algorithm
# since their existence doesn't affect the coherency of the directories we do have cached. 
#
# When a cache has been successfully loaded and validated this function returns a dictionary
# where the key is the object handle and the value is the cached MtpObjectInfo - the caller
# can then use the dictionary to perform a O(1) lookup against the object handle list
# obtained from the camera to know which objects it has available in the cache and thus
# can avoid a time-consuming MTP_OP_GetObjectInfo oeration. If the cache could not be loaded
# or is corrupt or the user has the cache disabled via a command-line arg or if coherency
# check performed by this function determines the cache is stale then None is returned.
#
# FYI, here's some analysis of how Nikon encodes obj handles (from the D7200):
#
# 0x0a19018e for DCIM\100D7200\DSC_0398.NEF (slot 2)
#        ^^^ ----> the 0x18e is the filename number (398 in hex)
#       ^ -------> the 0 is the directory number, encoded in some form
#    ^ ----------> the A means slot 2
#
# 0x0a19418e for DCIM\101D7200\DSC_0398.NEF (slot 2)
#        ^^^ ----> the 0x18e is the filename number (398 in hex)
#       ^ -------> the 4 is the directory number, encoded in some form
#    ^ ----------> the A means slot 2
#
# 0x0919418e for DCIM\101D7200\DSC_0398.NEF (slot 1)
#        ^^^ ----> the 0x18e is the filename number (398 in hex)
#       ^ -------> the 4 is the directory number, encoded in some form
#    ^ ----------> the 9 means slot 1
#
def loadAndValidateMtpObjectInfoCacheFromDisk(objHandlesFromCameraList):

	mtpObjectInfoCacheTuple = loadMtpObjectInfoCacheFromDisk()
	if not mtpObjectInfoCacheTuple:
		# no cache found or it failed its integrity test or usage was disabled by user configuration, etc...
		return None
	
	#
	# build a set of the camera's current object handles so that we can quickly do memebership
	# tests of our cached object handles for the directory entries we're checking. any miss
	# means that the cached directory handle we have is no longer present on the camera (or
	# less likely, the same card was moved to a different slot so that the encoded slot 
	# number in Nikon's object handle will now be different). this doesn't absolutely mean that
	# our other (file) objects are invalid but it probably does, and either way to be safe
	# we'll discard the cache in this case
	#
	objHandlesFromCameraSet = set(objHandlesFromCameraList) 
		
	#
	# the following loop scans through all the cached objects to perform two tasks:
	#
	# 1) Validate all objects that are directory entries by downloading the objects at those handles and verifying
	#    the directories are identical in name, date, etc.. If there is a mismatch then that means the cached object
	#    info we have is stale and the cache needs to be discaded
	#
	# 2) Builds dictionary that hashes the cached object handles to cached cached MtpObjectInfo objects - we'll use this
	#    to match up the object handles in the MTP_OP_GetObjectInfo loop to know which objects we have cached and thus
	#    don't have to fetch from the camera
	#
	# The tasks are somewhat unrelated but I'm performing them in the same loop as an optimziation.
	#
	bInvalidateCache = False
	cachedMtpObjectInfoListDict = {}
	for nObjIndex in xrange(0, len(mtpObjectInfoCacheTuple.mtpObjectInfoList)):
	
		objHandle = mtpObjectInfoCacheTuple.objHandlesList[nObjIndex]
		cachedMtpObjectInfo = mtpObjectInfoCacheTuple.mtpObjectInfoList[nObjIndex]

		# put cached object in cache dictionary we're building
		cachedMtpObjectInfoListDict[objHandle] = cachedMtpObjectInfo
					
		if mtpObjectInfoCacheTuple.mtpObjectInfoList[nObjIndex].associationType != MTP_OBJASSOC_GenericFolder:
			# this object is not a directory - nothing more to do with it
			continue
			
		#
		# this is a directory object. first make sure that this object handle 
		# still exists on the camera by checking it against the object handle
		# list obtained from the camera. if the handle doesn't even exist then
		# we know the directory is gone and we can immediately establish the 
		# cache is stale
		#
		if objHandle not in objHandlesFromCameraSet:
			applog_d("MTP obj handle 0x{:08x} for cache directory object \"{:s}\" does not exist".format(objHandle, cachedMtpObjectInfo.filename))
			bInvalidateCache = True
			break

		#
		# the directory object handle still exists on the camera. now we need
		# to perform a MTP_OP_GetObjectInfo of the handle and compare it against
		# our cached copy to confirm its the same directory/timestamp
		#		
		try:
			applog_d("Validating MTP obj cache directory object \"{:s}\" on handle 0x{:08x}".format(cachedMtpObjectInfo.filename, objHandle))
			mtpObjectInfo = getMtpObjectInfo(objHandle)
		except mtpwifi.MtpOpExecFailureException as e:
			if e.mtpRespCode == MTP_RESP_COMMUNICATION_ERROR:
				# request failed for reasons other than camera reporting an MPT error on the
				# cmd itself (ie, delivery of command failed) propagate exception and leave
				raise
			#
			# request failed, which really shouldn't happen because we already know the
			# object handle should be valid, even if the object data associated with it
			# might be stale. since we can't determine whether its stale without
			# successfully completing a MTP_OP_GetObjectInfo we'll just invalidate
			#
			applog_d("MTP object cache validation of \"{:s}\" resulted in {:s}".format(cachedMtpObjectInfo.filename, str(e)))
			bInvalidateCache = True
			break
			
		#
		# obtained the object data from the camera. now compare against our cached copy
		#
		if mtpObjectInfo != cachedMtpObjectInfo:
			# mismatches - the most likely cause is the timestamp
			applog_v("Found mismatch in MTP object cached directory \"{:s}\"".format(cachedMtpObjectInfo.filename))
			applog_d("    Cached copy: {:s}".format(str(cachedMtpObjectInfo)))
			applog_d("Downloaded copy: {:s}".format(str(mtpObjectInfo)))
			bInvalidateCache = True
			break;
								
	if bInvalidateCache:
		# generate a message if the cache was invalidated for any reason
		applog_v("The MTP object cache was detected as stale and will be discarded")
		return None
		
	#
	# cached passed all the coherency checks. it's good! hopefully :)
	#
	return cachedMtpObjectInfoListDict


#
# creates an MTP object instance for a given MTP handle, optionally recursing to create
# the MTP objects for the directory tree referenced by the object
# 
def createMtpObjectFromHandle(objHandle, createMtpObjectStatsStruct=None, cachedMtpObjectInfoListDict=None, fFindAndCreateAntecendentDirs=True, mtpObjectInfo=None):

	if not createMtpObjectStatsStruct:
		# use dummy local copy
		createMtpObjectStatsStruct = CreateMtpObjectStatsStruct()

	#
	# endless-recursion detection
	#
	createMtpObjectStatsStruct.recursionNesting += 1	
	if createMtpObjectStatsStruct.recursionNesting >= 100: # 100 is arbitary
		raise AssertionError("Recursive loop detected while building directory tree createMtpObjectFromHandle()")

	mtpObj = MtpObject.getByMtpObjectHandle(objHandle)
	if mtpObj:
		applog_d("MtpObject for handle 0x{:08x} already exists, skipping".format(objHandle))
		createMtpObjectStatsStruct.countMtpObjectsAlreadyExisting += 1
	else:
		fIsInCache = False
		if mtpObjectInfo == None: # caller didn't already retrieive the info for this object
			fIsInCache = cachedMtpObjectInfoListDict and (objHandle in cachedMtpObjectInfoListDict)
			if fIsInCache and g.args['mtpobjcache'] != 'verify':
				# found mtpObjectInfo for this handle in the cache - use cached copy
				applog_d("Found objHandle 0x{:08x} in cache".format(objHandle))
				mtpObjectInfo = cachedMtpObjectInfoListDict[objHandle]
			else:
				# didn't find mtpObjectInfo for this handle in the cache or we're validating cache - get the mtpObjectInfo from the camera
				mtpObjectInfo = getMtpObjectInfo(objHandle)
				if fIsInCache:
					# we're validating cache
					if mtpObjectInfo != cachedMtpObjectInfoListDict[objHandle]:
						applog_e("Found MTP object cache mismatch for \"{:s}\" vs  \"{:s}\"".format(mtpObjectInfo.filename, cachedMtpObjectInfoListDict[objHandle].filename))
						applog_e("    Cached copy: {:s}".format(str(cachedMtpObjectInfoListDict[objHandle])))
						applog_e("Downloaded copy: {:s}".format(str(mtpObjectInfo)))
						sys.exit(ERRNO_MTP_OBJ_CACHE_VALIDATE_FAILED)

		#
		# recurse to create MTP objects for the directory tree referenced by this object if we're instructed to do
		# so and this object has a parent dir and no MtpObject exists for the parent already
		#
		if fFindAndCreateAntecendentDirs and mtpObjectInfo.parentObject and MtpObject.getByMtpObjectHandle(mtpObjectInfo.parentObject)==None:
			applog_d("Recursing to get parent dir of \"{:s}\" - objHandle=0x{:08x}, parent=0x{:08x}".format(mtpObjectInfo.filename, objHandle, mtpObjectInfo.parentObject))
			createMtpObjectFromHandle(mtpObjectInfo.parentObject, createMtpObjectStatsStruct, cachedMtpObjectInfoListDict, fFindAndCreateAntecendentDirs)				

		#
		# create instance of MtpObject for this MtpObjectInfo
		#
		mtpObj = MtpObject(objHandle, mtpObjectInfo)
		if fIsInCache:
			createMtpObjectStatsStruct.countCacheHits += 1
			
	createMtpObjectStatsStruct.countObjectsProcessed += 1
	createMtpObjectStatsStruct.recursionNesting -= 1
	return mtpObj

	
#
# creates MTP object instances for each handle in a list
# 
def createMtpObjectsFromHandleList(objHandlesList, createMtpObjectStatsStruct=None, cachedMtpObjectInfoListDict=None, fFindAndCreateAntecendentDirs=True):
	numObjectHandles = len(objHandlesList)
	for nObjIndex in xrange(0, numObjectHandles):
		consoleWriteLine("\rRetrieving list of images/files from camera: {:d}/{:d}     ".format(nObjIndex, numObjectHandles))
		createMtpObjectFromHandle(objHandlesList[nObjIndex], createMtpObjectStatsStruct, cachedMtpObjectInfoListDict, fFindAndCreateAntecendentDirs)
	consoleClearLine()
		

#
# Enumerates all MTP objects on the camera, creating instances of our MtpObject()
# class for each object found.
#
# Some Background: In MTP, every file and folder on the camera is represented by
# an MTP object, which contains information such as the file's type, name,
# size, image dimensions, timestamps, etc.. Rather than passing full objects
# around for each MTP command, every object is represented by a unique MTP
# object handle, which is an opaque (to us anyway) 32-bit handle.
#
# The full list of all object handles for a given media card can be quickly
# obtained via the MTP_OP_GetObjectHandles. Then the slow part comes - we have
# to perform a MTP_OP_GetObjectInfo against each of those handles to get
# the actual MTP object info (ie, filename, size, type, etc...). The process
# enumerating through all the handles via MTP_OP_GetObjectInfo was found to
# be intermittently very slow on Nikon cameras, esp when performed for the first
# time after the camera has been powered on or if the media card was swapped out
# while the camera was on. To help ameliorate this we cache the MTP objects
# across arnef sessions on a per camera and S/N basis, so that we can at least
# avoid having to download the same objects on subsequent sessions, assuming
# they still exist in the camera on those subsequent sessions. Caching has its
# risks because MTP states that the object handles aren't persistent across
# camera sessions - see the comments in loadAndValidateMtpObjectInfoCacheFromDisk()
# for details on how we maintain coherency of the cache.
#		
def buildMtpObjects(fReportObjectTotals=True):

	#
	# get full list of MTP objects for storage ID
	#
	fullObjHandlesList =  getMtpObjectHandles(g.storageId)
	countFullObjHandlesList = len(fullObjHandlesList)

	# check if camera has a transfer list (user-selected images on camera). if so, download it
	g.fAllObjsAreFromCameraTransferList = False
	if g.args['cameratransferlist'] != 'ignore':
		if g.fRealTimeDownloadPhaseStarted:
			raise AssertionError("buildMtpObjects(): Checking for transfer list but already entered realtime download phase!")	
		#
		# some Nikon models like J4 don't include MTP_OP_GetTransferList in their operationsSupportedSet even
		# though they support MTP_OP_GetTransferList
		#
		if MTP_OP_GetTransferList in g.mtpDeviceInfo.operationsSupportedSet or g.cameraMake == CAMERA_MAKE_NIKON: 
			try:
				mtpTcpCmdResult = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetTransferList)
				(objHandlesListToGet, bytesConsumed) = parseMtpCountedWordList(mtpTcpCmdResult.dataReceived)
				numObjectHandlesToGet = len(objHandlesListToGet)
				g.fAllObjsAreFromCameraTransferList = True
				applog_i("Transfer list detected in camera - {:d} images/file(s) will be downloaded".format(numObjectHandlesToGet))
			except mtpwifi.MtpOpExecFailureException as e:
				#
				# we ignore non-MTP_RESP_COMMUNICATION_ERROR errors, since it's normal for this
				# command to fail when the camera doesn't have a transfer list. Most bodies
				# return MTP_RESP_NoTransferList. The WU-1a returns 0xa081.
				#
				if (e.mtpRespCode == MTP_RESP_COMMUNICATION_ERROR):
					raise
				# else the error is normal and means the user didn't selected any images for upload in the camera
		# else camera does not support transfer lists					
		if not g.fAllObjsAreFromCameraTransferList:
			if g.args['cameratransferlist'] == 'exitifnotavail':
				applog_e("Camera reports no user-selected images/movies to transfer or not-supported")
				if g.args['realtimedownload'] == 'disabled':
					sys.exit(ERRNO_NO_CAMERA_TRANSFER_LIST)
				# even though 'exitifnotavail' is configured, realtime-download means we should proceed to realtime download
				# we don't need to retrieve the initial object list
				return
					
	if not g.fAllObjsAreFromCameraTransferList:
		#
		# not using a user-selected transfer list. use full MTP object list from the camera
		#
		objHandlesListToGet = fullObjHandlesList
		numObjectHandlesToGet = countFullObjHandlesList
	
	if isDebugLog():
		applog_d("All MTP object handles (count={:d}):".format(countFullObjHandlesList))
		applog_d(strutil.hexdump(struct.pack('<' + 'I'*countFullObjHandlesList, *fullObjHandlesList), bytesPerField=4, includeASCII=False))
		if g.fAllObjsAreFromCameraTransferList:
			applog_d("Transfer List MTP object handles (count={:d}):".format(numObjectHandlesToGet))
			applog_d(strutil.hexdump(struct.pack('<' + 'I'*numObjectHandlesToGet, *objHandlesListToGet), bytesPerField=4, includeASCII=False))
			

	#
	# load MtpObjectInfo cache from previous session. if the cache was not available or
	# was found to be stale then cachedMtpObjectInfoListDict will be None
	#
	cachedMtpObjectInfoListDict = loadAndValidateMtpObjectInfoCacheFromDisk(fullObjHandlesList)

	#
	# create the MTP objects, downloading those not already in cache
	#
	createMtpObjectStatsStruct = CreateMtpObjectStatsStruct()
	createMtpObjectsFromHandleList(objHandlesListToGet, createMtpObjectStatsStruct, cachedMtpObjectInfoListDict, True)		
	if fReportObjectTotals or isDebugLog(): # always report object totals when debug logging is enabled
		applog_i("Processed info for {:d} files/dirs [{:d} from object cache, {:d} previous]".format(\
			createMtpObjectStatsStruct.countObjectsProcessed, createMtpObjectStatsStruct.countCacheHits, createMtpObjectStatsStruct.countMtpObjectsAlreadyExisting))
	
	#
	# serialized object list to file to cache it for future sessions. if we're using
	# a camera transfer list (user-selected files) don't update the cache if all the
	# objects were satisified by the cache (otherwise we'd be overwriting the cache with
	# a smaller subset of the cache, throwing away all cached entries for objects not
	# on the transfer list) or if the number of objects in the transfer list is less
	# than half the number of cache entries, otherwise again we'd be ovewriting the
	# cache with a smaller subset
	#
	countObjectsInCache = len(cachedMtpObjectInfoListDict) if cachedMtpObjectInfoListDict else 0
	if g.fAllObjsAreFromCameraTransferList:
		if createMtpObjectStatsStruct.countCacheHits < createMtpObjectStatsStruct.countObjectsProcessed and createMtpObjectStatsStruct.countObjectsProcessed >= countObjectsInCache/2:
			saveMtpObjectsToDiskCache()
		else:
			applog_d("Not updating MPT cache for transferlist items")
		g.lastFullMtpHandleListProcessedByBuildMtpObjects = None
	else:
		saveMtpObjectsToDiskCache()
		g.lastFullMtpHandleListProcessedByBuildMtpObjects = fullObjHandlesList


#
# returns the file extension of an MTP-obtained filename
#
def extractMtpFileExtension(fileNameStr):
	fileExtensionPos = fileNameStr.rfind(".", 0)
	if fileExtensionPos == -1:
		return ""
	extensionStr = fileNameStr[fileExtensionPos+1:]
	return extensionStr	# may be empty string if there were no characters after final "." in filename	


#
# generates a unique filename based on an original name by
# adding a -new-%d suffix, repeating until it finds a suffix
# number that's unique for the directory the file is in
#
def generateUniqueFilename(origFilenameWithPath):
	newSuffixCounter = 1
	while True:
		rootfilename = os.path.splitext(origFilenameWithPath)
		newFilename = "{:s}-new-{:d}{:s}".format(rootfilename[0], newSuffixCounter, rootfilename[1])
		if not os.path.exists(newFilename):
			return newFilename
		newSuffixCounter += 1
		

#
# prompts the user for a single-character selection (+enter),
# only allowing characters specfied in validKeyList. check
# is case-insensitive.
# 		
def promptWithSingleKeyResponse(promptStr, validKeyListStr):
	while True:
		key = raw_input(promptStr).upper()
		if key and validKeyListStr.upper().find(key.upper()) != -1:
			return key			

	
#
# Open/create download history file for this camera. We use this file to track
# which images we've alread downloaded in previous invocations, allowing the
# user to optionally skip these files for this or future invocations. 
#
# The history file contains one line of text for every file downloaded. The text
# is separated into two areas - a 'key area' and an 'additional info' area. The key
# area doubles as a unique identifier for a particular file along with holding
# information about the file. The 'addtional info' area has extra info about the
# download of the file, including a time stamp of when it was download and the path
# it was downloaded to.
#
# Here's the format of the history line for a file:
#
# 	localFilenameWithoutPath::MTP capture data str::Size in human-readable comma form::::download date/time string::outputDirPathAbsolute
#
# Examples:
#	DSC_0094.NEF::20150804T120900::22,719,774:::05/05/15 13:44::c:\pics
#	DSC_2570.JPG.sthumb.jpg::20150828T112418::3,419,512::::09/02/15 22:22:43::c:\pics\vacation
#
# The 'key area' and 'additional info area' are demarcated by four consecutive colons.
# Each field within those areas are separated by two consecutive colons. The 'key area'
# has enough information to uniquely identify a file and protect against false history
# positives/negatives, since it's the combination of the (camera-generated) filename,
# capture date+time, and file size. The likelihood that the camera's reuse of the filename will 
# have the same capture date+time and size should be nearly impossible.
#
# Generation of the history text to store in the history file is simple. Loading and using that
# history for the skip-alreayd-downloaded feature (on subsequent sessions) requires a little more
# work. To accomplish this we load and parse the file into a Python dictionary, with the 'key area'
# serving as the dictionary key and the 'addtional info area' serving as the value. Before downloading
# a file we build the history key and additional area strings for this session and then do a membership
# test of the key string against the dictionary we built from the history; if the keys match and
# we've been instructed to skip matches for this session then we wont download the file. If those
# conditions aren't met then we do download the file and then use the built key/additional area strings
# to generate the history event in the file.
#
# Some additional notes:
#
# I use 'localFilenameWithoutPath' insead of 'mtpObject.mtpObjectInfo.filename' so that we can
# track separate history for different types of downloads of the same file (full-sized, small thumbnail,
# and large thumbnail). 
#
# Even if we've been instructed to ignore the history this session (ie, to download files even if
# they're in the history), we still store entries for files we download this session, to support
# the ability of future sessions to skip these files if the user desires.
#	
def loadDownloadHistory():
	downloadHistoryFilename = g.cameraLocalMetadataPathAndRootName + "-downloadhist";
	if g.downloadHistoryDict:
		downloadHistoryDict = g.downloadHistoryDict # we already have download history loaded this session
	else:
		downloadHistoryDict = dict() # in case load fails we'll return an empty dictionary
		if (os.path.exists(downloadHistoryFilename)):
			if g.args['downloadhistory'] == 'clear':
				#
				# user instructed clearing the history file. we'll delete the file but then recreate it to allow
				# history to be generated for the files we download this session. since we're deleting the history
				# file there wont be any history to use for this session, thus no files will be skipped this session
				#
				applog_v("Deleting download history file \"{:s}\" per user configuration".format(downloadHistoryFilename))
				os.remove(downloadHistoryFilename)
			else:
				#
				# load download history into a dictionary. the 'downloadHistoryDict =' composite below separates the
				# 'key area' and 'additional info area' so that a dictionary entry is created for each line in the file.
				# here is a break-down of that line to make it easier to understand:
				#
				#   downloadHistoryDict = { for line in f } - the entire block is in curly braces, indicating a dictionary is
				#	being built. The expression starts by reading a line from the file into variable 'line'
				#
				# 	The left side of the expression then builds the key from the string loaded into 'line':
				#
				#		"{:s}".format(line[0:line.index("::::")])
				#		The 0: specifies the string starts at character 0. The end of the string is determined by
				#		line.index(":::"), which does a forward pattern match looking for the ":::" separator between the
				#		'key area' and 'additional info' area. index() returns the starting character position of the ":::",
				#		which serves as our ending subscript for the string of the 'key area'. The "{:s}" isn't really
				#		necessary but makes clear that the expression results in a string.
				#
				#	The right side of the expression then builds the 'additonal info area' from the string loaded into 'line':
				#
				#		"{:s}".format(line[line.index("::::", 0)+4: line.rindex("\n")])
				#		The line.index(":::", 0)+4 does the same pattern match performed on the key to find the same separator,
				#		but this time adds 4 to the result to get the starting charactor position of the substring we're extracting.
				#		The ending character position of the substring is determined via line.rindex("\n"), which finds the newline
				#
				#	Note that both index() and rindex() throw an exception if their substring searches fail - we catch this
				#	exception and report the history file as corrupt when we do. We then ignore its contents and delete the file,
				#	allowing a fresh file to be created when we reopen it for writing at the end of the routine
				#
				try:
					with open(downloadHistoryFilename) as f:
						downloadHistoryDict_Temp = { "{:s}".format(line[0:line.index("::::")])  :  "{:s}".format(line[line.index("::::", 0)+4: line.rindex("\n")]) for line in f }
					# succesfully loaded history
					downloadHistoryDict = downloadHistoryDict_Temp
					applog_v("Download history file \"{:s}\" loaded - {:d} entries".format(downloadHistoryFilename, len(downloadHistoryDict)))
				except ValueError:
					applog_e("Download history file \"{:s}\" appears corrupt and will be ignored and deleted".format(downloadHistoryFilename))
					os.remove(downloadHistoryFilename)
				except IOError as e:
					applog_e("Error openg/reading download history file \"{:s}\". No history will be available this session.".format(downloadHistoryFilename))
		else:
			applog_v("Download history file \"{:s}\" not found - will create".format(downloadHistoryFilename))
			
		g.downloadHistoryDict = downloadHistoryDict
		
	#
	# re(open) the download history file for appending to support new history entries generated
	# this session. return both the download history dictionary and the reopened history file
	#
	fileDownloadHistory = open(downloadHistoryFilename, "a")
	return (downloadHistoryDict, fileDownloadHistory)
	
	
#
# writes data to a file being downloaded from the camera. 
#			
def writeDataToDownloadedFile(fileHandleIfAlreadyOpen, filenameWithPath, data, bCloseAfterWriting, bIsAppending):
	applog_d("{:s} writing 0x{:x} bytes, closeAfterWriting={:d}".format(filenameWithPath, len(data), bCloseAfterWriting))
	#
	# during a download we use a .part name in case we exit abnormally without being able to
	# clean up (delete) the file - that way the user doesn't think he has a valid image/movie file
	# for incomplete downloads
	#
	fileNameTemp = filenameWithPath + ".part"
	fo = fileHandleIfAlreadyOpen
	try:
		if fo == None:
			if fileNameTemp not in g.filesToDeleteOnAppExit:
				#
				# add the file to the delete list in case either the write we're
				# about to perform fails or if the (potentially) ongoing download
				# fails. we do this because we don't want to leave a file around
				# which has only partailly downloaded data. it's up to the
				# caller to remove the file from the delete list when he deems
				# it safe - we can't do it here after writing in case we're only
				# writing one piece and the caller still wants to close the file,
				# such as after receiving a partial piece during an MTP error
				#
				g.filesToDeleteOnAppExit.append(fileNameTemp)
			if not bIsAppending:
				fo = open(fileNameTemp, "wb") # create/truncate and open for binary writing
			else:
				fo = open(fileNameTemp, "ab") # open for binary appending
		fo.write(data)
		if bCloseAfterWriting:
			fo.close()
			return None
		return fo		
	except IOError as e:
		if fo:
			fo.close()
		applog_e("\nError creating or writing to \"{:s}\". {:s}".format(filenameWithPath, str(e)))
		sys.exit(ERRNO_DOWNLOAD_FILE_OP_FAILED)

	
#
# checks if the extension of an MTP filename is in a list of file extensions
#
def isMtpFilenameExtInList(mtpFilename, extList):
	extension = extractMtpFileExtension(mtpFilename)
	if extension: # if filename has an extension
		if extension not in extList:
			return False
	else: # file has no extension
		if "<NOEXT>" not in extList:
			return False
	return True

	
#
# determines if an MTP object is a file object and if so, whether it passes
# the user-configured filter (ie, file should be processed)
#
def doesMtpObjectPassUserFileFilter(mtpObject, fPrintFilterAction=True):

	# first filter out objects that don't correspond to files
	if mtpObject.mtpObjectInfo.objectFormat == MTP_OBJFORMAT_Assocation or mtpObject.mtpObjectInfo.objectFormat == MTP_OBJFORMAT_NONE:
		if fPrintFilterAction:
			applog_d("Skipping {:s} - object is not file - {:s}".format(mtpObject.mtpObjectInfo.filename, getMtpObjFormatDesc(mtpObject.mtpObjectInfo.objectFormat)))
		return False

	if g.fAllObjsAreFromCameraTransferList == True:
		# all objects presently in list are from the camera transfer list, so all bypass user filters
		return True
		
	# filter against user-specified extensions
	if g.args['extlist'] and isMtpFilenameExtInList(mtpObject.mtpObjectInfo.filename, g.args['extlist']) == False:
			if fPrintFilterAction:
				applog_v("Skipping {:s} - filename extension not in user-specified list".format(mtpObject.mtpObjectInfo.filename))
			return False
		
	# filter against capture date range
	if g.objfilter_dateStartEpoch != None and mtpObject.captureDateEpoch < g.objfilter_dateStartEpoch:
		# user specified starting date filter and this object has a capture date earlier than specified filter
		if fPrintFilterAction:
			applog_v("Skipping {:s} - has capture date earlier than user-specified start date filter".format(mtpObject.mtpObjectInfo.filename))
		return False
	if g.objfilter_dateEndEpoch != None and mtpObject.captureDateEpoch > g.objfilter_dateEndEpoch:
		# user specified ending date filter and this object has a capture date later than specified filter
		if fPrintFilterAction:
			applog_v("Skipping {:s} - has capture date later than user-specified end date filter".format(mtpObject.mtpObjectInfo.filename))
		return False
		
	# filter against folders
	if g.args['onlyfolders']:
		cameraFolder = mtpObject.getImmediateDirectory()
		if (cameraFolder=="" and ("<ROOT>" not in g.args['onlyfolders'])) or cameraFolder not in g.args['onlyfolders']:
			# image is in root directory of camera and "<ROOT>" not in list, or image is in directory not in list
			if fPrintFilterAction:
				applog_v("Skipping {:s}\\{:s} - folder not in --onlyfolders".format(cameraFolder, mtpObject.mtpObjectInfo.filename))
			return False
	if g.args['excludefolders']:
		cameraFolder = mtpObject.getImmediateDirectory()
		if (cameraFolder=="" and "<ROOT>" in g.args['excludefolders']) or cameraFolder in g.args['excludefolders']:
			# image is in root directory of camera and "<root>" is in list, or image is in directory in list
			if fPrintFilterAction:
				applog_v("Skipping {:s}\\{:s} - folder in --excludefolders".format(cameraFolder, mtpObject.mtpObjectInfo.filename))
			return False

	# passes all user filters
	return True


#
# Returns the next MTP file object that passes the user-configured filters. This
# function is used in MTP file object enumeration loops. Call with -1 to start
# the enumeration. Returns None when there are no more file(s).
#	
def getNextUserFilteredMtpFileObject(prevObject, fileTransferOrder = FILE_TRANSFER_ORDER_USER_CONFIGURED):
	if prevObject == None:
		return None
	if fileTransferOrder == FILE_TRANSFER_ORDER_USER_CONFIGURED:
		fileTransferOrder = g.fileTransferOrder
	if prevObject == -1:
		mtpObject = MtpObject.getNewest() if fileTransferOrder==FILE_TRANSFER_ORDER_NEWEST_FIRST else MtpObject.getOldest()
	else:
		mtpObject = prevObject.getOlder() if fileTransferOrder==FILE_TRANSFER_ORDER_NEWEST_FIRST else prevObject.getNewer()	
	while mtpObject != None and not doesMtpObjectPassUserFileFilter(mtpObject):
		mtpObject = mtpObject.getOlder() if fileTransferOrder==FILE_TRANSFER_ORDER_NEWEST_FIRST else mtpObject.getNewer()	
	return mtpObject


#
# generates a partial dictionary for use by rename.performRename() with
# keys common to all files this session
#	
def genRenameDictKeysCommonToAllMtpObjects():	
	renameDict = dict()
	renameDict['downloadDateEpoch'] = g.appStartTimeEpoch
	renameDict['cameramake'] = g.mtpDeviceInfo.manufacturerStr.split(' ')[0] # just use the first word. for example, Nikon returns "Nikon Corporation"
	renameDict['cameramodel'] = g.mtpDeviceInfo.modelStr
	renameDict['cameraserial'] = g.mtpDeviceInfo.serialNumberStr
	return renameDict

	
#
# updates a dictionary for use by rename.performRename() with keys specific
# to a particular MTP object
#	
def updateRenameDictKeysSpecificToMtpObject(renameDict, mtpObject, dlnum, dlnum_lifetime, localFilename=None, path=None):
	captureFilename = mtpObject.mtpObjectInfo.filename
	if not localFilename:
		localFilename = captureFilename
	if not path:
		path = g.args['outputdir']
	renameDict['path'] = path
	renameDict['filename'] = localFilename	
	renameDict['capturefilename'] = captureFilename
	renameDict['captureDateEpoch'] = mtpObject.captureDateEpoch
	renameDict['dlnum'] = dlnum+1
	renameDict['dlnum_lifetime'] = dlnum_lifetime+1
	renameDict['camerafolder'] = mtpObject.getImmediateDirectory()
	renameDict['slotnumber'] = getSlotIndexFromStorageId(mtpObject.mtpObjectInfo.storageId)


#
# uses the rename engine to generate a directory and filename. caller passes a fully-
# initialized rename dict
#	
def performDirAndFileRename(renameDict, fCreateDirs=False):
	filenameAfterRename = renameDict['filename']
	dirAfterRename = g.args['outputdir'] # note this may be an empty string when 'dirnamespec' was specified by user
	# note that syntax for both filenamespec and dirnamespec were verified during cmd-line arg parsing
	if g.args['dirnamespec']:
		dirAfterRename = os.path.join(dirAfterRename, rename.performRename(g.args['dirnamespec'], renameDict))
		if fCreateDirs and not os.path.exists(dirAfterRename):
			applog_v("Creating directory tree \"{:s}\"".format(dirAfterRename))
			os.makedirs(dirAfterRename)	
		renameDict['path'] = dirAfterRename # update dict with possible generated directory from above	
	if g.args['filenamespec']:
		filenameAfterRename = rename.performRename(g.args['filenamespec'], renameDict)
		if not filenameAfterRename:
			applog_e("--filenamespec resulted in an empty filename. Please review your specification string")
			sys.exit(ERRNO_FILENAMESPEC_RESULT_EMPTY_STR)
		if '/' in filenameAfterRename or '\\' in filenameAfterRename:
			applog_e("--filenamespec can not have a path or path characters in it ('/' or '\\')")
			sys.exit(ERRNO_FILENAMESPEC_HAS_PATH_CHARACTERS)
	dirAfterRenameAbsolute = os.path.abspath(dirAfterRename)
	return (dirAfterRenameAbsolute, filenameAfterRename)


#
# performs  launch of application and arguments specified in 'downloadexec' command-line option
#	
def doDownloadExec(renameDict, mtpObject):

	if g.args['downloadexec_extlist'] and isMtpFilenameExtInList(mtpObject.mtpObjectInfo.filename, g.args['downloadexec_extlist']) == False:
		return

	execArgs = []
	# note that syntax for rename args were verified during cmd-line arg parsing
	for arg in g.args['downloadexec']:
		renamedArg = rename.performRename(arg, renameDict)
		if renamedArg != "":
			if 'notildereplacement' not in g.args['downloadexec_options']:
				#
				# replace all tildes with dashes, to support passing arguments with leading - or --.
				# this mechanism must be used because any leading - or -- is intepreted by
				# argparse as an argument to ourselves
				#
				if execArgs: # only do this replacement on args that aren't the first, to allow tidles in application/script name
					renamedArg = renamedArg.replace('~', '-')				
			execArgs.append(renamedArg)
		else:
			#
			# rename resulted in an empty string, which is allowed. if this is the first
			# argument, which corresponds to the name of the app/script we're launching,
			# then treat this as a signal to not launch for this file. this capability
			# allows the use of @replace@ specifiers to create empty strings on files
			# that the user wants to skip
			#
			if not execArgs:
				# first arg - we'll skip exec for this file
				applog_v("Skipping 'downloadexec' for \"{:s}\" due to empty first argument of rename string".format(renameDict['filename']))
				break;
	applog_d("download exec args input: " + str(g.args['downloadexec']))
	applog_d("download exec args output: " + str(execArgs))
	if execArgs:
		applog_v("Launching 'downloadexec': {:s}".format(str(execArgs)))
		try:
			process = subprocess.Popen(execArgs)
		except:
			# different platforms can throw different platform-specific exceptions
			errStr = "Error launching for 'downloadexec' {:s}: {:s} {:s}".format(str(execArgs), str(sys.exc_info()[0]), str(sys.exc_info()[1]))
			if 'ignorelauncherror' in g.args['downloadexec_options']:
				applog_d(errStr)
				return
			applog_e(errStr)
			sys.exit(ERRNO_DOWNLOADEXEC_LAUNCH_ERROR)
		if 'wait' in g.args['downloadexec_options']:
			#
			# we're instructed to wait until launched app exits before
			# continuing to next download. we'll wait in a loop,
			# calling mtpSessionKeepAlive() to make sure the camera
			# keeps the MTP session going
			#
			timeLastCameraKeepAlive = None
			while process.poll() == None:
				timeLastCameraKeepAlive = mtpSessionKeepAlive(timeLastCameraKeepAlive)
				time.sleep(.10) # sleep for 100ms between each process completion check				
			retCode = process.wait()
			if 'exitonfailcode' in g.args['downloadexec_options']:
				if retCode != 0:
					applog_i("Exiting due to non-zero return code ({:d}) of launched app for '--downloadexec'".format(retCode))
					sys.exit(ERRNO_DOWNLOADEXEC_NON_ZERO_EXIT_CODE)
		if 'delay' in g.args['downloadexec_options']:
			time.sleep(5)
			
						
#
# determines if an MTP_RESP_* error encountered during a download was (likely) caused
# by the user deleting the file in the camera while we were downloading it
#	
def respErrorDuringDownload_checkIfFileDeletedOnCamera(mtpObject, localFilename, mtpOpExecFailureException):

	#
	# non-communication error (ie, camera completed request with MTP error).
	# some cameras like Canon allow users to delete images while in WiFi
	# mode (Nikon presently does not). On Canon the error observed when
	# transferring a file that gets deleted was MTP_RESP_GeneralError. Rather
	# than trying to parse specific MTP_RESP_* values instead perform a
	# MTP_OP_GetObjectInfo to see if the object still exists
	#
	applog_d("RESP error downloading \"{:s}\": {:s}".format(localFilename, getMtpRespDesc(mtpOpExecFailureException.mtpRespCode)))
	try:
		objectInfo = getMtpObjectInfo(mtpObject.mtpObjectHandle, False)
		# hmmm, MTP_OP_GetObjectInfo() completed successfully. doesn't appear file was deleted then
		return False
	except mtpwifi.MtpOpExecFailureException as e:
		# guess at which errors are indicactive of an object that was deleter
		mtpRespCodesIndicatingFileDeleted = [ MTP_RESP_InvalidObjectHandle, MTP_RESP_OperationNotSupported, MTP_RESP_ParameterNotSupported,\
			MTP_RESP_AccessDenied, MTP_RESP_PartialDeletion, MTP_RESP_NoValidObjectInfo, MTP_RESP_InvalidParentObject, MTP_RESP_InvalidParameter ]	
		if e.mtpRespCode in mtpRespCodesIndicatingFileDeleted:
			applog_e("Error downloading \"{:s}\" - file appears to have been deleted in-camera by user - ignoring ({:s}/{:s})".format(localFilename,\
				getMtpRespDesc(mtpOpExecFailureException.mtpRespCode), getMtpRespDesc(e.mtpRespCode)))
			return True
		# camera reported an error that we don't think corresponds to a deleted file
		return False


#
# download progress callback for MTP get requests issued by downloadMtpFileObjects().
# displays the progress to console as a percentage of completion.
#			
def downloadMtpFileObjects_DownloadProgressCallback(bytesReceivedAllCurrentPayloads, totalBytesExpectedAllCurrentPayloads, bytesReceivedPriorPayloads, totalFileSizeIfKnown):
	if not hasattr(downloadMtpFileObjects_DownloadProgressCallback, "lastPctPrinted"):
		downloadMtpFileObjects_DownloadProgressCallback.lastPctPrinted = -1 # static var to track last percentage printed, to avoid unnecessary updates

	bytesReceived = bytesReceivedAllCurrentPayloads + bytesReceivedPriorPayloads
	if totalFileSizeIfKnown:
		totalObjSizeBytes = totalFileSizeIfKnown
	else:
		totalObjSizeBytes = totalBytesExpectedAllCurrentPayloads		
	pctDone = int(float(bytesReceived) / totalObjSizeBytes * 100)
	if pctDone != downloadMtpFileObjects_DownloadProgressCallback.lastPctPrinted:
		# only update if it's changed. it's ok if we miss a single % update when switching files
		downloadMtpFileObjects_DownloadProgressCallback.lastPctPrinted = pctDone
		consoleWriteLine("\b\b\b{:2d}%".format(pctDone))


#
# Performs download of all file objects that pass the user-configured filters.
#
# When I first wrote this routine I was experiencing very flaky wireless behavior from
# all Nikon bodies I tested it with (D7200, J4, D750, WU-1a). About halfway through a
# NEF  download via MTP_OP_GetObject the transfer rate would become erratic and sometimes
# the camera would completely stop transferring and then eventually time out on a socket
# receive. It wouldn't do this on every file but about once every few files. To handle
# this behavior I added significant amounts of recovery logic, both in the low-levels
# of mtpwifi.py and the upper levels of this module (appMain), both of which were designed
# to retain any partially transferred data and allow the retry of downloads. Luckily when
# a Nikon body hits this condition it could  be revived by dropping the TCP/IP connection
# and restarting everything over again, from the opening of the TCP/IP socket through the
# MTP start session and back to this routine to retrieve the portion of the file we have
# left to download via MTP_OP_GetPartialObject.
#
# It later occured to me that the issue might be specific to Nikon's implementation of 
# MTP_OP_GetObject, as it appeared the camera's erratic behavior was related to how large
# the object was - JPEGs were fine but larger NEFs should issues and very large MOV
# files were the worst. It seemed the camera has some type of memory leak associated with
# the command, perhaps committing internal resources to the entire file rather than to each
# payload piece. So I experimented with transfers that relied solely MTP_OP_GetPartialObject,
# using varoius tranfers sizes, and confirmed my suspicion - there's a bug in Nikon's firmware
# related to large transfers, both from the atomic MTP_OP_GetObject request and also 
# large MTP_OP_GetPartialObject requests. Based on these results I rewrote this method
# to use only MTP_OP_GetPartialObject and with smaller transfer sizes and all the erratic
# Nikon behavior disappeared. Fortunately performance did not suffer - I found that using
# a transfer size of 1MB (vs the full object size in the orig implementation) yielded the
# same performance as the latter, and actually much better when you consider that we didn't
# have to go through time-consuming connection tear-downs and re-establishment cycles. On
# both my D7200 and J4 I see approx 2.3 MB/s of sustained xfer performance on the adhoc wifi
# conneciton when the camera is next to the computer.
#
# Resolving the transfer issue meant that all the retry logic I originally put in was now
# unnecessary. Rather than take it out I decided it best to leave it in place, to support
# any scenarios where the wifi connection can be marginal, such as when the camera is further
# away from the computer. I left the max-transfer size configurable, to allow for future
# tweaking/experimentation of different camera models, in g.maxGetObjTransferSize
#
def downloadMtpFileObjects(firstMtpObjectToDownload = None):

	#
	# load download history and open history file for writing for new history to be generated this session
	#
	(downloadHistoryDict, fileDownloadHistory) = loadDownloadHistory()
	fSkipDownloadedFiles = (g.args['downloadhistory'] != 'ignore') # skip files if instructed to do so
	
	#
	# various forms of the filename/path are used in this routine for different purposes. here's a guide to 
	# the variables that hold the filename/path
	#
	# filenameWithObjTypeSuffixBeforeRename - The capture filename with .sthumb.jpg or ".lthumb.jpg" optionally added
	# to it if we're downloading a thumbnail instead of the file. This filename is used as the key in the download history
	#
	# filenameAfterRename - Filename after optionally renaming it using the rename engine (if user used --filenamespec). If
	# the rename engine was not used then filenameAfterRename == filenameWithObjTypeSuffixBeforeRename
	#
	# dirAfterRename - Directory name generated optionally genreated if using the rename engine (if user used --filenamespec). If
	# the rename engine was not used then dirAfterRename == g.args['outputpath'] only
	#
	# localFilenameWithoutPath - Filename actually used to store downloaded image locally. It's set to filenameAfterRename plus
	# an optional suffix '-new-x' suffix in case dirAfterRename conflicted with an existing file.
	#
	# localFilenameWithPath - os.join(dirAfterRename, localFilenameWithoutPath)
	#
	# localFilenameWithPath_TemporaryFilename - localFilenameWithPath + ".part" (temporary filename until complete, then renamed
	# on disk to localFilenameWithPath)
	#
	# mtpObject.partialDownloadObj().getLocalFilenameWithoutPath() - To support recovery/resumption of interrupted downloads we
	# need to save the potentially unique filename generated with the '-new-x' suffix across invocations of this routine. For
	# the path of a retried invocation of this routine we simply regenerate the (same) path again (ie, use dirAfterRename) since
	# nothing should cause it o change change across invocations of this routine
	#
	
	
	fUsingRenameEngineForDirOrFile = g.args['filenamespec'] != None or g.args['dirnamespec'] != None
	fUsingRenameEngineForAnyParameter = fUsingRenameEngineForDirOrFile or g.args['downloadexec']
	if fUsingRenameEngineForAnyParameter:
		renameDict = genRenameDictKeysCommonToAllMtpObjects()		
		
	#
	# scan all objects and download each file that passes the user-configured filters
	#
	if firstMtpObjectToDownload == None:
		#
		# caller didn't specify specific starting point/object. we'll start at the
		# beginning of the object list if this is our first time downloading or at
		# the last file we were downloading/completed downloading if we're resuming
		# a download interrupted by error
		#
		mtpObject = g.downloadMtpFileObjects_LastMtpObjectDownload
		if mtpObject == None:
			mtpObject = getNextUserFilteredMtpFileObject(-1)
	else:
		#
		# caller passed in starting point/object. this object hasn't been checked
		# against the user filters so we'll do so now, skipping until we find
		# an object from the starting point that does pass, or return if no passing
		# object is found
		#
		mtpObject = firstMtpObjectToDownload
		while not doesMtpObjectPassUserFileFilter(mtpObject):
			mtpObject = getNextUserFilteredMtpFileObject(mtpObject)
			if mtpObject == None:
				return		
			
	fFirstLoopIteration = True # unfortunate hack because Python doesn't support do-while or post conditions on for loops
	while True:
	
		#
		# get next file object to process
		#
		if fFirstLoopIteration:
			# use first object set in 'mtpObject' before start of while loop
			fFirstLoopIteration = False
		else:
			mtpObject = getNextUserFilteredMtpFileObject(mtpObject)
						
		if not mtpObject:
			# no more files to process
			break
	
		if mtpObject.wasDownloadedThisSession():
			# file was already downloaded on a previous invocation of downloadMtpFileObjects()
			applog_d("Skipping {:s} - already downloaded this session".format(mtpObject.mtpObjectInfo.filename))
			continue
			
		g.downloadMtpFileObjects_LastMtpObjectDownload = mtpObject
				
		mtpOpGet = CmdLineActionToMtpTransferOpDict[g.args['action']]
		
		# build local filename that will hold image
		filenameWithObjTypeSuffixBeforeRename = mtpObject.mtpObjectInfo.filename
		if mtpOpGet == MTP_OP_GetThumb:
			filenameWithObjTypeSuffixBeforeRename += ".sthumb.jpg"
		elif mtpOpGet == MTP_OP_GetLargeThumb:
			filenameWithObjTypeSuffixBeforeRename += ".lthumb.jpg"
			
		#
		# perform rename engine on directory and/or filename if specified by user
		#
		if fUsingRenameEngineForAnyParameter:
			# update dict with fields that change for each file
			updateRenameDictKeysSpecificToMtpObject(renameDict, mtpObject, g.countFilesDownloadedPersistentAcrossStatsReset, len(downloadHistoryDict), filenameWithObjTypeSuffixBeforeRename)
		if fUsingRenameEngineForDirOrFile:
			(dirAfterRename, filenameAfterRename) = performDirAndFileRename(renameDict, True)
		else:
			filenameAfterRename = filenameWithObjTypeSuffixBeforeRename
			dirAfterRename = os.path.abspath(g.args['outputdir'])
			
			
		#
		# build download history description, which is used both to check if we've already
		# downloaded the file (to optionally skip it) and also to write the history for
		# this file if we do download it. to uniquely identify the file we use a combination
		# of the filename, capture date, and size - these three elements togethre should
		# prevent us from any false positives/negatives for future images. note that for
		# filename we use the original name with the appended sthumb/lthumb suffix if we'read
		# downloading thumbs - that way we can uniquely track the downloading of the thumbs vs
		# the actual image/video file. see the comments for loadDownloadHistory() for
		# more information on how the history is handled
		#
		# format:
		# 	filenameWithObjTypeSuffixBeforeRename::MTP capture data str::Size in human-readable comma form::::current time str::outputDirAnFilename
		# example:
		#   DSC_0094.NEF::20150804T120900::22,719,774:::05/05/15 13:44::c:\pics\DSC_0094.NEF
		#
		downloadHistoryDescStr_Key = "{:s}::{:s}::{:,}".format(filenameWithObjTypeSuffixBeforeRename, mtpObject.mtpObjectInfo.captureDateStr, mtpObject.mtpObjectInfo.objectCompressedSize)
		if fSkipDownloadedFiles and downloadHistoryDescStr_Key in downloadHistoryDict:
			#
			# this file is in history. put the 'additional info area' into a named tuple for clarity and then
			# log the information so the user knows the file has been skipped and when and where it was originally
			# downloaded. note that a file may have been previously  downloaded multiple times, which is possible
			# if the user instructed us to ignore history on one of those sessions - we only write the history on
			# the first/original download, thus the history reflects that instead a more recent re-download
			#
			DownloadHistoryElement = namedtuple('DownloadHistoryElement', 'dateDownloadedStr pathDownloadedToStr')
			listDownloadHistory = str.split(downloadHistoryDict[downloadHistoryDescStr_Key], '::') # each field of the additional info area is separated by two colons
			downloadHistoryElementTuple = DownloadHistoryElement(listDownloadHistory[0], listDownloadHistory[1])				
			applog_v("Skipping \"{:s}\" - downloaded on {:s} to \"{:s}\" ".\
				format(filenameWithObjTypeSuffixBeforeRename, downloadHistoryElementTuple.dateDownloadedStr, downloadHistoryElementTuple.pathDownloadedToStr))
			g.dlstats.countFilesSkippedDueToDownloadHistory += 1
			mtpObject.setAsDownloadedThisSession() # mark as downloaded so it wont be re-evaluated on subsequent scans
			continue
						
			
		#
		# check if the output file already exists (if this isn't a file we're resuming a
		# failed download on)
		#
		if mtpObject.partialDownloadObj().getLocalFilenameWithoutPath() == None:
			localFilenameWithoutPath = filenameAfterRename
			localFilenameWithPath = os.path.join(dirAfterRename, localFilenameWithoutPath)
			if (os.path.exists(localFilenameWithPath)):
				if g.args['ifexists'] == 'prompt':
					applog_i("\"{:s}\" exists".format(localFilenameWithPath))
					#
					# note that if the user takes too long to respond the MTP session may
					# time out. we'll recover but it'll look messy. need to implement a
					# multi-platform method  to poll for keys so that we can mtpSessionKeepAlive()
					# while we're waiting for a keypress (todo-todo)
					#
					keyResponse = promptWithSingleKeyResponse("(S)kip, (O)verwrite, (U)niquename, (E)xit [+enter]: ", 'soue')
				else:
					keyResponse = ''			
				if g.args['ifexists'] == 'skip' or keyResponse == 'S':
					if not keyResponse:
						applog_i("Skipping \"{:s}\" - file exists".format(localFilenameWithPath))
					g.dlstats.countFilesSkippedDueToFileExistingLocally += 1
					continue
				elif g.args['ifexists'] == 'overwrite' or keyResponse == 'O':
					if not keyResponse:
						applog_v("\"{:s}\" exists - will be overwritten".format(localFilenameWithPath))
					applog_d("{:s} - deleting existing file per user config".format(localFilenameWithPath))
					os.remove(localFilenameWithPath)
				elif g.args['ifexists'] == 'uniquename' or keyResponse == 'U':
					uniqueFilenameWithPath = generateUniqueFilename(localFilenameWithPath)
					uniqueFilenameWithoutPath = os.path.basename(uniqueFilenameWithPath)
					if not keyResponse:
						applog_v("\"{:s}\" exists - will write to \"{:s}\"".format(localFilenameWithPath, uniqueFilenameWithoutPath))
					localFilenameWithPath = uniqueFilenameWithPath
					localFilenameWithoutPath = uniqueFilenameWithoutPath
				elif g.args['ifexists'] == 'exit' or keyResponse == 'E':
					applog_i("\"{:s}\" exists - exiting per user config".format(localFilenameWithPath))
					sys.exit(ERRNO_FILE_EXISTS_USER_SPECIFIED_EXIT)
			#
			# save the local filename in case we had to generate a unique name and the
			# transfer fails this invocation (we'll need the potentially unique filename
			# on the retry invocation)
			#
			mtpObject.partialDownloadObj().setLocalFilenameWithoutPath(localFilenameWithoutPath)
					
		else:
			#
			# this is a retry of a failed transfer and we generated the
			# local filename when the transfer was started. we need to use
			# that originally generated name in case it involved creating
			# a unique filename due to an pre-existing local file
			#
			localFilenameWithoutPath = mtpObject.partialDownloadObj().getLocalFilenameWithoutPath()
			localFilenameWithPath = os.path.join(dirAfterRename, localFilenameWithoutPath)

		#
		# generate download history strings based on the final path and filename. note that the key
		# was already generated and is based on the pre-rename of the filename
		# 
		currentTimeStr = strutil.getDateTimeStr(fMilitaryTime=True)
		downloadHistoryDescStr_Info = "{:s}::{:s}\n".format(currentTimeStr, localFilenameWithPath)
		downloadHistoryDescStr_Full = downloadHistoryDescStr_Key + "::::" + downloadHistoryDescStr_Info
			
					
		# notify camera of acquisition start for this object if it was selected by the user in the camera (in camera transfer list)
		if g.fAllObjsAreFromCameraTransferList:
			mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_NotifyFileAcquisitionStart, struct.pack('<I', mtpObject.mtpObjectHandle))
		
		# get the object
		applog_d(">> {:s}".format(getMtpOpDesc(mtpOpGet)))
		
		consoleWriteLine("Downloading \"{:s}\":  0%".format(localFilenameWithoutPath))

		#
		# do the get/download
		#			
		bUsingGetPartialObject = (mtpOpGet == MTP_OP_GetObject) # as opposed to MTP_OP_GetThumb or MTP_OP_GetLargeThumb
		foDownloadedFile = None # no (new) data written to file yet this invocation
		fFileDeletedOnCamera = False
		localFilenameWithPath_TemporaryFilename = localFilenameWithPath + ".part"
		if bUsingGetPartialObject:
			
			try:

				#
				# we may have already written some of the file on a previous invocation. if
				# so it will be reflected in the partialDownloadObj()
				# 
				fileSizeBytes = mtpObject.mtpObjectInfo.objectCompressedSize
				bytesWritten = mtpObject.partialDownloadObj().getBytesWritten()
	
				if bytesWritten > 0:
					#
					# as a data integrity safeguard, make sure the size of the file is equal to
					# the number of bytes we think we've written
					#
					applog_d("{:s} - resuming download - bytesWritten=0x{:x}, fileSize=0x{:x}".format(localFilenameWithoutPath, bytesWritten, fileSizeBytes))
					if (os.path.exists(localFilenameWithPath_TemporaryFilename)):
						statInfo = os.stat(localFilenameWithPath_TemporaryFilename)
						if statInfo.st_size != bytesWritten:									
							raise AssertionError("About to resume download for \"{:s}\" but it's filesize is not equal the how much data we've already downloaded and written (expected 0x{:x}, actual 0x{:x}".format(localFilenameWithoutPath, bytesWritten, statInfo.st_size))
					else:
						raise AssertionError("About to resume download for \"{:s}\" but the file is missing. It should be present and have a size of 0x{:x}".format(localFilenameWithoutPath, bytesWritten))									

						
				#
				# note there's a corner case where bytesWritten can already
				# be equal to fileSizeBytes. this can happen if there was a
				# communication error on the previous invocation after we
				# received the final data payload but during the cmd response
				# phase. the logic below is designed to gracefully handle this case
				#

				#
				# loop to download and write each piece of the object. the size of each
				# transfer is constrained by g.maxGetObjTransferSize
				#
				offsetIntoImage = bytesWritten
				dataReceived = six.binary_type()
				while offsetIntoImage < fileSizeBytes:
					bytesToDownloadThisPiece = min(g.maxGetObjTransferSize, fileSizeBytes-offsetIntoImage)
					if len(dataReceived)+bytesToDownloadThisPiece > g.maxGetObjBufferSize:
						# the amount of data we already have + size of this transfer would exceed our configure maxgetobjbuffersize - constrain it
						bytesToDownloadThisPiece -= (len(dataReceived)+bytesToDownloadThisPiece) - g.maxGetObjBufferSize
					if bytesToDownloadThisPiece == 0:
						# shouldn't happen
						raise AssertionError("bytesToDownloadThisPiece is zero! offset=0x{:x}, fileSize=0x{:x}, dataReceived=0x{:x}, max=0x{:x}/0x{:x}".format(\
							offsetIntoImage, fileSizeBytes, len(dataReceived), g.maxGetObjTransferSize, g.maxGetObjBufferSize))
					applog_d("{:s} - downloading next piece, offset=0x{:x}, count=0x{:x}".format(localFilenameWithoutPath, offsetIntoImage, bytesToDownloadThisPiece))
					timeStart = secondsElapsed(None)
					mtpTcpCmdResultGetObj = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetPartialObject, struct.pack('<III',\
						mtpObject.mtpObjectHandle, offsetIntoImage, bytesToDownloadThisPiece),\
						rxTxProgressFunc=lambda bytesReceivedAllCurrentPayloads, totalBytesExpectedAllCurrentPayloads :\
						downloadMtpFileObjects_DownloadProgressCallback(bytesReceivedAllCurrentPayloads, totalBytesExpectedAllCurrentPayloads, offsetIntoImage, fileSizeBytes))
					mtpObject.partialDownloadObj().addDownloadTimeSecs(secondsElapsed(timeStart))
												
					dataReceived += mtpTcpCmdResultGetObj.dataReceived				
					offsetIntoImage += bytesToDownloadThisPiece

					bIsFinalPiece = (offsetIntoImage == fileSizeBytes)
					if bIsFinalPiece or len(dataReceived) >= g.maxGetObjBufferSize:
						# we've reached/exceeded our max buffer size or this is the final piece. write out the data we have
						foDownloadedFile = writeDataToDownloadedFile(foDownloadedFile, localFilenameWithPath, dataReceived, bIsFinalPiece, (bytesWritten != 0)) # close file if this is the last piece
						mtpObject.partialDownloadObj().addBytesWritten(len(dataReceived))
						bytesWritten += len(dataReceived)
						dataReceived = six.binary_type()						

				#
				# we've completed the download and writing of the file
				#
				fileDownloadTimeSecs = mtpObject.partialDownloadObj().getDownloadTimeSecs()
				
			except mtpwifi.MtpOpExecFailureException as e:

				applog_i("") # newline since console is on "Downloading ...." message

				if e.mtpRespCode != MTP_RESP_COMMUNICATION_ERROR and respErrorDuringDownload_checkIfFileDeletedOnCamera(mtpObject, localFilenameWithoutPath, e):
					# file was deleted on camera - ignore error so we can move on to next file
					fFileDeletedOnCamera = True
						
				if fFileDeletedOnCamera == False:
			
					mtpObject.partialDownloadObj().addDownloadTimeSecs(secondsElapsed(timeStart))
					applog_d("{:s} - error during download, writing 0x{:x} bytes of buffered data".format(localFilenameWithoutPath, len(dataReceived)))
					
					# flush out any unwritten data we have in 'dataReceived'
					if dataReceived:
						foDownloadedFile = writeDataToDownloadedFile(foDownloadedFile, localFilenameWithPath, dataReceived, False, (bytesWritten != 0))
						bytesWritten += len(dataReceived)
						mtpObject.partialDownloadObj().addBytesWritten(len(dataReceived))
					if e.partialData:
						#
						# more data was received before the communication failure. write
						# that partial data to the file so that we don't have to incur the
						# performance penalty of re-downloading it on the next retry invocation
						# 
						applog_d("{:s} - writing partial payload data of 0x{:x} bytes".format(localFilenameWithoutPath, len(e.partialData)))
						foDownloadedFile = writeDataToDownloadedFile(foDownloadedFile, localFilenameWithPath, e.partialData, False, (bytesWritten != 0))
						bytesWritten += len(e.partialData)
						mtpObject.partialDownloadObj().addBytesWritten(len(e.partialData))
					if foDownloadedFile:
						foDownloadedFile.close()
					raise
					
		else: # else of if bUsingGetPartialObject

			timeStart = secondsElapsed(None)
			try:
				mtpTcpCmdResultGetObj = mtpwifi.execMtpOp(g.socketPrimary, mtpOpGet, struct.pack('<I', mtpObject.mtpObjectHandle),\
					rxTxProgressFunc=lambda bytesReceivedAllCurrentPayloads, totalBytesExpectedAllCurrentPayloads : downloadMtpFileObjects_DownloadProgressCallback(bytesReceivedAllCurrentPayloads, totalBytesExpectedAllCurrentPayloads, 0, 0))
				dataReceived = mtpTcpCmdResultGetObj.dataReceived
				fileDownloadTimeSecs = secondsElapsed(timeStart)
				fileSizeBytes = len(dataReceived)
				writeDataToDownloadedFile(foDownloadedFile, localFilenameWithPath, dataReceived, True, False)					
			except mtpwifi.MtpOpExecFailureException as e:
				applog_i("") # newline since console is on "Downloading ...." message
				if e.mtpRespCode != MTP_RESP_COMMUNICATION_ERROR and respErrorDuringDownload_checkIfFileDeletedOnCamera(mtpObject, localFilenameWithoutPath, e):
					# file was deleted on camera - ignore error so we can move on to next file
					fFileDeletedOnCamera = True
				else:
					# error doesn't appear to be due to a file deleted in camera
					raise

		#
		# this completion path is common for both the get-object case and the small/large thumb case
		# both paths are required to have these vars set:
		#
		#		fileDownloadTimeSecs - total download time of file
		#		fileSizeBytes - size of file
		#
		# now write data to file. for the get-object case this will be the last piece of
		# data received for the file (after zero or more other pieces have already
		# been written). for the small/large thumb case this will always been the
		# only piece of data for the file
		#
		consoleClearLine()	# erase "Downloading..." status line
		
		if not fFileDeletedOnCamera:
		
			# success
									
			#
			# mark the file as downloaded. this means any exception that occurs
			# in logic after marking the download complete wont trigger a re-download
			# on a subsequent invocation of this routine. as such, be careful where
			# any future logic is place relative to this sentinel
			#
			mtpObject.setAsDownloadedThisSession()
			mtpObject.releasePartialDownloadObj()
			os.rename(localFilenameWithPath_TemporaryFilename, localFilenameWithPath) # download done - safe to rename to final filename
			g.filesToDeleteOnAppExit.remove(localFilenameWithPath_TemporaryFilename)
			
			#
			# print download completion message with transfer rate calculation
			#
			if fileDownloadTimeSecs > 0: # avoid divide-by-zero, though not expecting ever expecting 'fileDownloadTimeSecs' to be zero
				thisFileDownloadRateMbSec = fileSizeBytes / fileDownloadTimeSecs / 1048576
			else:
				thisFileDownloadRateMbSec = 0
			applog_i("{:s} [size = {:,}] in {:.2f} seconds ({:.2f} MB/s)".format(localFilenameWithPath,\
				fileSizeBytes, fileDownloadTimeSecs, thisFileDownloadRateMbSec))
									
			#
			# update running stats and mark the file as downloaded
			#
			g.dlstats.totalDownloadTimeSecs += fileDownloadTimeSecs
			g.dlstats.totalBytesDownloaded += fileSizeBytes
			g.dlstats.countFilesDownloaded += 1
			g.countFilesDownloadedPersistentAcrossStatsReset += 1


			#
			# notify camera of acquisition end for this object if it was selected by the user in the camera (in camera transfer list).
			# this action removes the image/file from the transfer list in the camera
			#
			if g.fAllObjsAreFromCameraTransferList:
				mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_NotifyFileAcquisitionEnd, struct.pack('<I', mtpObject.mtpObjectHandle))

			#
			# add this file to the download history file. also note when
			# fSkipDownloadedFiles==FALSE (user specified to ignore download history and
			# force download), there may already be an entry in the history file for
			# this image - to prevent duplicates we check membership first
			#
			if downloadHistoryDescStr_Key not in downloadHistoryDict:
				# if this file is not already in the history
				fileDownloadHistory.write(downloadHistoryDescStr_Full)
				fileDownloadHistory.flush()
				# add file to the in-memory copy of the history
				downloadHistoryDict[downloadHistoryDescStr_Key] = downloadHistoryDescStr_Info

									
			#
			# set the file's last modification+access time to the original creation
			# time reported that the camera reported for this object, which is the
			# behavior the user gets when he transfers images off the camera or media
			# card directly. note that we're doing this *after* we've marked the download
			# complete - the call to os.utime() is not critical in terms of retrying it,
			# so we still want to consider the download/file complete even if this call fails
			#
			os.utime(localFilenameWithPath, (mtpObject.captureDateEpoch, mtpObject.captureDateEpoch))
			
			#
			# launch optional user-specific program for this downloaded file
			#
			if g.args['downloadexec']:
				renameDict['filename'] = localFilenameWithoutPath # update dict in case filename changed due to ifexists unique creation
				doDownloadExec(renameDict, mtpObject)
					
		else:
			
			#
			# file was deleted on the camera before/during the download. we could delete the
			# object but instead we'll just mark it as downloaded so it'll be skip on any future
			# loop (same result)
			#
			if foDownloadedFile:
				foDownloadedFile.close()			
			mtpObject.setAsDownloadedThisSession()
			mtpObject.releasePartialDownloadObj()
			
			#
			# delete the partially-downloaded portion of file (if any of it was written
			# before we detected the deletion)
			#
			if localFilenameWithPath_TemporaryFilename in g.filesToDeleteOnAppExit:
				deleteFileIgnoreErrors(localFilenameWithPath_TemporaryFilename)
				g.filesToDeleteOnAppExit.remove(localFilenameWithPath_TemporaryFilename)
				

	# do any post-operation cleanup
	fileDownloadHistory.close()	
		

#
# prints a directory listing of all MTP file objects that pass the user-configured filters
#
def printMtpObjectDirectoryListing():	

	applog_i("") # newline separator for logging

	fUsingRenameEngine = g.args['filenamespec'] != None or g.args['dirnamespec'] != None
	if fUsingRenameEngine:
		renameDict = genRenameDictKeysCommonToAllMtpObjects()
		
	#
	# scan all objects and generate listing for each file that passes the user-configured filters
	#
	totalBytesOfImagesInObjectsListed = 0
	countFilesListed = 0
	mtpObject = getNextUserFilteredMtpFileObject(-1)
	while mtpObject:
	
		if fUsingRenameEngine:		
			# update dict with fields that change for each file. note we're using session download count as lifetime for the preview of the renaming
			updateRenameDictKeysSpecificToMtpObject(renameDict, mtpObject, countFilesListed, countFilesListed)
			(dirAfterRename, filenameAfterRename) = performDirAndFileRename(renameDict, False)
			dirAndFilenameAfterRename = os.path.join(dirAfterRename, filenameAfterRename)
	
		#
		# print information about this file
		#
		timeStr = strutil.getDateTimeStr(mtpObject.captureDateEpoch, fMilitaryTime=False)
		sizeStr = "{:13,}".format(mtpObject.mtpObjectInfo.objectCompressedSize)
		fullPathStr = mtpObject.genFullPathStr()
		if g.countCardsUsed > 1:
			# prepend slot number of file to path string
			fullPathStr = "CARD{:d}\\".format(getSlotIndexFromStorageId(mtpObject.mtpObjectInfo.storageId)) + fullPathStr		
		if not fUsingRenameEngine:
			applog_i("{:s}  {:s} {:s}".format(timeStr, sizeStr, fullPathStr))
		else:
			applog_i("{:s}  {:s} {:s} -> {:s}".format(timeStr, sizeStr, fullPathStr, dirAndFilenameAfterRename))
		totalBytesOfImagesInObjectsListed += mtpObject.mtpObjectInfo.objectCompressedSize
		countFilesListed += 1
		# get next file that passes user-configured filters
		mtpObject = getNextUserFilteredMtpFileObject(mtpObject)
	
	#
	# print listing summary
	#		
	applog_i("        {:4d} File(s)  {:13,} bytes".format(countFilesListed, totalBytesOfImagesInObjectsListed))
	applog_i("        {:4d} Dir(s)  {:13,} bytes free {:s}".format(MtpObject._CountMtpObjectDirectories, g.mtpStorageInfoList[0].freeSpaceBytes,\
				"[CARD 1]" if g.countCardsUsed > 1 else ""))
	for cardIndex in xrange(1, g.countCardsUsed):
		applog_i("                     {:13,} bytes free [CARD {:d}]".format(g.mtpStorageInfoList[cardIndex].freeSpaceBytes, cardIndex+1))



#
# retrieves an MTP device property from the camera. mtpPropteryCode is a
# MTP_DeviceProp_* value. If fIgnoreIfNotSupported is TRUE then
# empty data is returned if the camera reports that the property is
# not supported.
#		
def getMtpDeviceProperty(mtpDevicePropCode, fIgnoreIfNotSupported=False):
	try:
		mtpTcpCmdResultGetObj = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_GetDevicePropValue, struct.pack('<I', mtpDevicePropCode))
		return mtpTcpCmdResultGetObj.dataReceived
	except mtpwifi.MtpOpExecFailureException as e:
		if fIgnoreIfNotSupported and e.mtpRespCode != MTP_RESP_COMMUNICATION_ERROR:
			return six.binary_type() # empty data
		raise


#
# sets an MTP property in the camera. mtpDevicePropCode is a
# MTP_DeviceProp_* value. If fIgnoreIfNotSupported is TRUE then
# any "not-supported" error will be ignored
#		
def setMtpDeviceProperty(mtpDevicePropCode, devicePropData, fIgnoreIfNotSupported=False):
	try:
		mtpTcpCmdResultGetObj = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_SetDevicePropValue, struct.pack('<I', mtpDevicePropCode), devicePropData)
		return False
	except mtpwifi.MtpOpExecFailureException as e:
		if fIgnoreIfNotSupported and e.mtpRespCode != MTP_RESP_COMMUNICATION_ERROR:
			return True
		raise

		
#
# sets an MTP property for a Canon property. If fIgnoreIfNotSupported is
# TRUE then any "not-supported" error will be ignored
#		
def setMtpDeviceProperty_Canon(devicePropData, fIgnoreIfNotSupported=False):
	try:
		mtpTcpCmdResultGetObj = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_Canon_SetDevicePropValue, dataToSend=devicePropData)
		return False
	except mtpwifi.MtpOpExecFailureException as e:
		if fIgnoreIfNotSupported and e.mtpRespCode != MTP_RESP_COMMUNICATION_ERROR:
			return True
		raise


#
# set's the camera's date using standard MTP device property
#
def setCameraDateTime(timeEpoch=0):

	if not timeEpoch:
		timeEpoch = time.time()
	newCameraTimeHumanReadableStr = strutil.getDateTimeStr(timeEpoch, fMilitaryTime=False)
	
	if g.cameraMake == CAMERA_MAKE_CANON:
		propData = struct.pack('<II', MTP_DeviceProp_Canon_DateTimeUTC, int(timeEpoch))
		fSetDateTimeFailed = setMtpDeviceProperty_Canon(struct.pack('<I', len(propData)+4) + propData, True)
	else:
		newCameraTimeStruct = time.localtime(timeEpoch)
		newCameraTimeMtpStr = time.strftime("%Y%m%dT%H%M%S", newCameraTimeStruct)
		newCameraTimeCountedUtf16 = strutil.stringToCountedUtf16(newCameraTimeMtpStr, True)
		fSetDateTimeFailed = setMtpDeviceProperty(MTP_DeviceProp_DateTime, newCameraTimeCountedUtf16, True)
	if not fSetDateTimeFailed:		
		applog_i("Camera's date/time set to {:s}".format(newCameraTimeHumanReadableStr))
	else:
		applog_w("Failed setting camera's date/time to {:s}".format(newCameraTimeHumanReadableStr))

	
#
# converts an MTP date-time string in the format of 'yyyymmddThhmmss'
# to epoch time. note that this conversion involves using the system's
# local time configuration including time zone and DST setting, so
# if the camera has those elements configured differently then the
# converted time wont match up
# 
def mtpTimeStrToEpoch(mtpDateTimeStr):
	if len(mtpDateTimeStr) != 15 or mtpDateTimeStr[8] != 'T':
		# doesn't appear to be a valid MTP date-time string
		return 0
	if mtpDateTimeStr == '19800000T000000':
		# nikon uses this timestamp for some non folder/file objects
		return 0		
	return time.mktime(time.strptime(mtpDateTimeStr, "%Y%m%dT%H%M%S"))
		
#
# retrieves the camera's date-time and converts it to local epoch time
#
def getCameraDateTime():
	mtpDateTime = getMtpDeviceProperty(MTP_DeviceProp_DateTime, True)
	(mtpDateTimeStr, byteLen) = mtpCountedUtf16ToPythonUnicodeStr(mtpDateTime)
	return mtpTimeStrToEpoch(mtpDateTimeStr)


#
# sychronizes the camera's time to the system's time if they're off more than the
# configured allowable delta
#
def syncCameraDateTimeIfNecessary():

	if g.args['maxclockdeltabeforesync'] == 'disablesync':
		# time sync disabled
		return
		
	if g.cameraMake != CAMERA_MAKE_CANON: # we don't suppor retriving current time on Canon bodies, so we always set it unconditionally
		
		if MTP_DeviceProp_DateTime not in g.mtpDeviceInfo.devicePropertiesSupportedSet:
			applog_v("Camera does not support synching clock")
			return

		cameraCurrentTimeEpoch = getCameraDateTime()
		if not cameraCurrentTimeEpoch:
			applog_w("Unable to obtain camera's time to decide if clock synching is required")
			return

		systemCurrentTimeEpoch = time.time() # note that is some inherent skew between retrieving the camera's time vs getting system time
		
		cameraTimeStr = strutil.getDateTimeStr(cameraCurrentTimeEpoch, fMilitaryTime=False)
		systemTimeStr = strutil.getDateTimeStr(systemCurrentTimeEpoch, fMilitaryTime=False)
		
		applog_d("Camera time epoch: {:.2f}, System time epoch: {:.2f}".format(cameraCurrentTimeEpoch, systemCurrentTimeEpoch))
		applog_d("Clocks: Camera: {:s}, System: {:s}".format(cameraTimeStr, systemTimeStr))
			
		if g.args['maxclockdeltabeforesync'] != 'alwayssync':	
			# if we're only to sync when the skew is beyond a user-configured threshold
			deltaTime = math.trunc(abs(cameraCurrentTimeEpoch - systemCurrentTimeEpoch))
			if (deltaTime <= int(g.args['maxclockdeltabeforesync'])):
				# time delta between camera and system is within configured allowance
				return		
			applog_i("Clocks skewed: Camera: {:s}, System: {:s}".format(cameraTimeStr, systemTimeStr))			
			
	#
	# set camera's date/time to system's current date/time
	#	
	setCameraDateTime()
	
	
#
# displays the next character of a twirlling ASCII progress character. this routine
# is called multiple times during a long-running loop, giving the appearance of
# a spinning character. it's used to show the user that we're still alive
# 
#
def printSpinningProgressCharToConsole():
	progressChars = "-\|/"
	
	if not hasattr(printSpinningProgressCharToConsole, "lastProgressCharPrinted"):	# static variable to track last progress character printed
		printSpinningProgressCharToConsole.lastProgressCharPrinted = -1
	
	printSpinningProgressCharToConsole.lastProgressCharPrinted += 1
	if printSpinningProgressCharToConsole.lastProgressCharPrinted >= len(progressChars):
		printSpinningProgressCharToConsole.lastProgressCharPrinted = 0
	consoleWriteLine('\b' + progressChars[printSpinningProgressCharToConsole.lastProgressCharPrinted])


#
# parses an event list returned from MTP_OP_NkonGetEvent, generating a list of
# of MtpEventTuple's describing each event
# 
MtpEventTuple = namedtuple('MtpEvent', 'eventCode eventParameter')	
def parseNikonMtpEventData(data):
	mtpEventTupleList = []
	(eventCount,) = struct.unpack('<H', data[0:2])
	for nthEvent in xrange(eventCount):
		(eventCode, eventParameter) = struct.unpack('<HI', data[2+nthEvent*6:2+nthEvent*6 + 6])
		mtpEventTupleList.append(MtpEventTuple(eventCode, eventParameter))
	return mtpEventTupleList

	
#
# prints an event list that was generated by parseNikonMtpEventData()
# 
def genNikonEventListDescription(mtpEventList):
	str = ""
	for nthEvent in xrange(len(mtpEventList)):
		if mtpEventList[nthEvent].eventCode == MTP_EVENT_DevicePropChanged:
			parameterDesc = getMtpDevicePropDesc(mtpEventList[nthEvent].eventParameter)
		else:
			parameterDesc = "0x{:08x}".format(mtpEventList[nthEvent].eventParameter)
		if nthEvent > 0:
			str += "\n" 
		str += "E#{:d}: {:s}, Param: {:s}".format(nthEvent, getMtpEventDesc(mtpEventList[nthEvent].eventCode), parameterDesc) 
		
	return str		
	
	
#
# retrieves any queued events from Nikon camera, returning parsed event list
#	
def getNikonMtpEvents():
	mtpTcpCmdResultGetObj = mtpwifi.execMtpOp(g.socketPrimary, MTP_OP_NkonGetEvent)
	return parseNikonMtpEventData(mtpTcpCmdResultGetObj.dataReceived)
	
#
# realtime download loop using Nikon-specific event mechanism
#
def realTimeCapture_NikonEventsMethod():

	fRedrawWaitingMessage = True
	try:
		while True:
		
			if fRedrawWaitingMessage:
				consoleWriteLine("\rWaiting for realtime photos from camera to download. Press <ctrl-c> to exit  ")
				fRedrawWaitingMessage = False
			printSpinningProgressCharToConsole()
		
			#
			# retrieve any pending events
			#		
			nikonMtpEventList = getNikonMtpEvents()
			if nikonMtpEventList:

				#
				# process the events, creating MTP objects for any new directories/files
				#
				applog_d(genNikonEventListDescription(nikonMtpEventList))
				countNewFileObjects = 0
				firstNewMtpFileObject = None
				for nthEvent in xrange(len(nikonMtpEventList)):
					if nikonMtpEventList[nthEvent].eventCode == MTP_EVENT_ObjectAdded:
						objHandle = nikonMtpEventList[nthEvent].eventParameter
						if MtpObject.getByMtpObjectHandle(objHandle):
							applog_d("realTimeCapture: MtpObject for handle 0x{:08x} already exists, skipping".format(objHandle))
							continue
						mtpObjectInfo = getMtpObjectInfo(objHandle)
						if g.storageId != MTP_STORAGEID_ALL_CARDS and mtpObjectInfo.storageId != g.storageId:
							if isVerboseLog():
								consoleClearLine()
								fRedrawWaitingMessage = True
								applog_v("Ignoring \"{:s}\" because it's not from your configured --slot".format(mtpObjectInfo.filename))
						else:
							# create MTP object for this new obj
							mtpObject = createMtpObjectFromHandle(objHandle, mtpObjectInfo=mtpObjectInfo)
							if mtpObject.mtpObjectInfo.associationType != MTP_OBJASSOC_GenericFolder:
								countNewFileObjects += 1
								if firstNewMtpFileObject == None:
									firstNewMtpFileObject = mtpObject
							
				if countNewFileObjects:
					consoleClearLine()
					fRedrawWaitingMessage = True
					downloadMtpFileObjects(firstNewMtpFileObject)
					continue # check for new events immediately without sleeping first
			
			#
			# no new files in this event list. sleep before checking again
			#
			time.sleep(g.args['realtimepollsecs'])
			
	except KeyboardInterrupt as e: # <ctrl-c> pressed
		consoleClearLine()
		g.dlstats.reportDownloadStats(g.args['realtimedownload'] != 'only') # print stats even if no files downloaded only if this was a realtime-only session
		raise

		
#
# realtime download loop using generic MTP-object count polling method
#
def realTimeCapture_MtpObjPollingMethod():

	#
	# there are two polling methods for detecting the possibility of
	# new images - either poll the object count and when it changes
	# download the new object handle list or poll the object handle list
	# itself by downloading it every interval. it would seem polling the
	# couunt would be more efficient since there is less data to move every
	# polling interval, and possibly less work for the camera to do
	# to deliver the data (ie, may have to do media access to retrieve
	# the object handle list but not the count). however a big drawback
	# of polling the object count is that it'll miss the case of the user
	# deleting an image in the camera and then taking another, which
	# will result in a non-changing object count if both events occur between
	# our polling inteval. so we're going to use the objlist polling method
	# instead, but I've left in the numobjs polling method just in case the
	# objlist method causes problems for some cameras (method selectable via
	# a command-line argument). during development I timed both methods on
	# a Canon 6D and it actually turned out that retrieving the object handle
	# list was faster than retrieving the object handle count (20ms vs 50ms).
	#
	# whichever polling method is used, the end result is we download the
	# new object handle list and do a subtraction between it and the previous
	# object handle list we have to get a list of new objects, then insert those
	# new objects into the MTP object tree and do a download cycle starting
	# from the first newly-inserted object.
	#
	# for the initial full object list we use the list obtained by
	# the most recent invocation of buildMtpObjects(). using that list
	# gurantees we wont miss any images taken between the interval of
	# the most recent build/download sequence. note that this initial
	# full object list will be empty for realtime-only configuraitons 
	# and this is the first invocation of the realtime phase - in this
	# case we simply download the list now (no risk of missing images
	# because the user hasn't been told we're ready for realtime until
	# the message that will be posted below to the console)
	#
	
	lastFullMtpHandleList = g.lastFullMtpHandleListProcessedByBuildMtpObjects
	if not lastFullMtpHandleList:
		# this is a realtime-only session and this is first invocation (no recovery retries yet)
		lastFullMtpHandleList = getMtpObjectHandles(g.storageId)
		if isDebugLog():
			applog_d("realTimeCapture_MtpObjPollingMethod(): First MTP object list (count={:d}):".format(len(lastFullMtpHandleList)))
			applog_d(strutil.hexdump(struct.pack('<' + 'I'*len(lastFullMtpHandleList), *lastFullMtpHandleList), bytesPerField=4, includeASCII=False))
		
	fRedrawWaitingMessage = True
	try:
		while True:
		
			if fRedrawWaitingMessage:
				consoleWriteLine("\rWaiting for realtime photos from camera to download. Press <ctrl-c> to exit  ")
				fRedrawWaitingMessage = False
			printSpinningProgressCharToConsole()
			
			fNumObjsChanged = False
			if g.args['rtd_mtppollingmethod_newobjdetection'] == 'numobjs':
				#
				# see if the number of MTP objects on the camera has changed since
				# the last time we've processed the camera's object list
				#
				numMtpObjects = getNumMtpObjects(g.storageId)
				fNumObjsChanged = numMtpObjects != len(lastFullMtpHandleList)
				if fNumObjsChanged:
					applog_d("fNumObjsChanged TRUE: (previous=0x{:d}, new=0x{:d}".format(len(lastFullMtpHandleList), numMtpObjects))
				
			if fNumObjsChanged or g.args['rtd_mtppollingmethod_newobjdetection'] == 'objlist':
			
				#
				# get current list of object handles from camera if we're using the
				# numobjs method for detection and the number of objects changed or if
				# we're using the objlist method (to see if there are new objects)
				#
				currentFullMtpHandleList = getMtpObjectHandles(g.storageId)
				newMtpHandleList = list(set(currentFullMtpHandleList).difference(lastFullMtpHandleList))				
				lastFullMtpHandleList = currentFullMtpHandleList
				
				if isDebugLog() and (fNumObjsChanged or newMtpHandleList):
					applog_d("realTimeCapture_MtpObjPollingMethod(): Current MTP object list (count={:d}):".format(len(currentFullMtpHandleList)))
					applog_d(strutil.hexdump(struct.pack('<' + 'I'*len(currentFullMtpHandleList), *currentFullMtpHandleList), bytesPerField=4, includeASCII=False))
					applog_d("realTimeCapture_MtpObjPollingMethod(): New MTP object list (count={:d}):".format(len(newMtpHandleList)))
					applog_d(strutil.hexdump(struct.pack('<' + 'I'*len(newMtpHandleList), *newMtpHandleList), bytesPerField=4, includeASCII=False))				
								
				if newMtpHandleList:
										
					# we have new objects to process
					consoleClearLine()
					fRedrawWaitingMessage = True
														
					createMtpObjectsFromHandleList(newMtpHandleList)
					downloadMtpFileObjects()
					
					continue # check for new objects immediately without sleeping first
				
			#
			# no new objects. sleep before checking again
			#
			time.sleep(g.args['realtimepollsecs'])
			
	except KeyboardInterrupt as e: # <ctrl-c> pressed
		consoleClearLine()
		g.dlstats.reportDownloadStats(g.args['realtimedownload'] != 'only') # print stats even if no files downloaded only if this was a realtime-only session
		raise

		
#
# realtime download entry for Sony cameras. There is no support
# for camera option while in Sony's 'Send to Computer' mode so
# we implement an offline method where the user selecitvely goes
# back into 'Send to Computer' mode whenever he wants to transfer
# images he's taken. To trigger this we'll do a sys.exit() here
# with a retryable exit code, which will execute the usualy Sony-sleep
# end session logic but then re-enter the retry loop.
#
def realTimeCapture_SonyExitMethod():
	applog_i("\nSony transfer session done - entering staged realtime wait for new images")
	sys.exit(ERRNO_SONY_REALTIME_ENTER_RETRY_LOOP)


#
# function that implements realtime capture of images
#
def realTimeCapture():

	#
	# modify the filter configuration so that it functions with realtime downloads.
	# we have to be careful that any filters added in future versions are properly
	# accounted for here as well - I put a note in processCmdLine() to that effect
	#
	
	#
	# reset any capture filter in place from the 'normal' download phase. I clear
	# the capture date filter rather than setting it to the app launch time because
	# we don't have to worry about downloading files created before launch time because
	# all the realtime polling methods prevent the MTP Object list from being scanned,
	# meaning we don't run the risk of older files being found for download. I go out
	# of my way to avoid having to rely on the launch-time capture date filter so that
	# we can accommodate clock skew between camera and system (for cameras we don'tail
	# support time sync for)
	# 
	clearCaptureDateFilter()
		
	g.args['cameratransferlist']  = 'ignore'	# so that recovery operations use the full camera object list rather than any transfer list already processed
	g.fAllObjsAreFromCameraTransferList = False	# we'll be adding non-transfer list objects (ie, the files we download in realtime)
	g.args['transferorder'] = 'oldestfirst'		# so that downloadMtpFileObjects() will properly enumerate through multiple realtime images as we add them
	g.fRealTimeDownloadPhaseStarted = True		# used by logic when making decisions on reporting for downloads, recovery operations, etc..
			
	#
	# reset download stats of the original, non-real time download. this way we
	# capture stats specific to the realtime phase
	#
	resetDownloadStats()
	
	#
	# start realtime capture loop
	#
	if g.realtimeDownloadMethod == REALTIME_DOWNLOAD_METHOD_NIKON_EVENTS:
		realTimeCapture_NikonEventsMethod()
	elif g.realtimeDownloadMethod == REALTIME_DOWNLOAD_METHOD_MTPOBJ_POLLING:
		realTimeCapture_MtpObjPollingMethod()
	elif g.realtimeDownloadMethod == REALTIME_DOWNLOAD_METHOD_SONY_EXIT:
		realTimeCapture_SonyExitMethod()
		
#
# main work routine
#
def appMain():

	if not hasattr(appMain, "lastConnectErrMsg"):
		appMain.lastConnectErrMsg = "" # static var to track last connect err msg to allow supressing reporting while waiting for connection across retries

	bSessionStarted = False
	bAttemptCloseSessionAtTermination = False
	bEchoNewlineBeforeReturning = True
	try:
		#
		# start wireless session
		#
		startMtpSession()
		bSessionStarted = True						# we're now in a session
		bAttemptCloseSessionAtTermination = True	# we're now in a session, so set flag to close it when we're done
		appMain.lastConnectErrMsg = ""				# clear out last connection error msg now that we're connected
		
		#
		# sync clocks if necessary
		#
		syncCameraDateTimeIfNecessary()
							
		#
		# select appropriate media card slot (storage ID)
		#
		selectMtpStorageId()
		
		#
		# get information on media card
		#
		getMtpStorageInfo()
		
		#
		# notify camera user that we're about to start any potential transfers
		#
		notifyCameraUserTransferSessionStarting()
		
		#
		# populate our list of MTP objects. we bypass this if we've retrieved all objects
		# on a previous retry this session and if we haven't already entered the realtime capture
		# phase. we can't bypass if we've entered realtime operation in case the user captured images
		# while we were re-establishing the connection to the camera during a retry, otherwise we'd miss
		# those objects and fail to download them. Note that we bypass the initial object retrieval (which
		# can be very time consuming depending on the camera and how many images are on the cards) if
		# we're in realtime-only mode and we were able to establish a connection to the camera within
		# 10 seconds (configurable) of the user starting our app (any longer and we run the risk that the
		# user already started taking photos that he expects us to download and since the realtime logic
		# only detects images taken after they enter their polling loop we would miss those initial images)
		#
		if (g.fRetrievedMtpObjects == False and g.args['realtimedownload'] != 'only') or g.fRealTimeDownloadPhaseStarted\
			or secondsElapsed(g.appStartTimeEpoch) > g.args['rtd_maxsecsbeforeforceinitialobjlistget']:
			buildMtpObjects()
			g.fRetrievedMtpObjects = True
			
		#
		# do primary action
		#
		if g.args['action'] == 'listfiles':
			printMtpObjectDirectoryListing()
		else:
		
			applog_i("") # newline separator for logging

			#
			# download files. we skip this if if we're in realtime-only capture mode
			# and this isn't a recovery invocation (for recovery invocations we need
			# to download even in realtime-only mode to get any files we missed while
			# in recovery) and if we established an initial connection to the camera
			# fast enough to allow us to avoid worrying about missing any initial photos
			#
			if g.fRetrievedMtpObjects:
			
				if g.fRealTimeDownloadPhaseStarted or g.args['realtimedownload'] == 'only':
					#
					# either the realtime phase has already started (and so we're in a recovery
					# cycle) or we had to download all objectsbefore reaching the realtime phase
					# due to the time elapsed between app launchand when we were able to establish
					# our initial connection to the camera. we need to download any files we
					# potentially missed since launch or while performing recovery (plus also to support
					# the workflow where the user can turn WiFi off on the camera for as long as he
					# wants for intervals he doesn't want realtime capture). for this recovery
					# buildMtpObjects() retrieved all objects from the camera, including those captured
					# before the user launched airnefcmd. to exclude those files we set the capture date
					# filter to our app's launch time. rather than permanently keeping this capture date
					# filter in place for realtime operation we only set while perfomring downloadMtpFileObjects();
					# that way we're only sensitive to camera vs system time skew during the recovery
					# downloads (such as for camera models we don't support synching the clock to). the
					# launch-time capture date filter will be removed by realTimeCapture()
					#
					changeCaptureDateFilterToAppStartTime()
			
				downloadMtpFileObjects()
				g.dlstats.reportDownloadStats(g.fRealTimeDownloadPhaseStarted or g.args['realtimedownload'] == 'only') # don't print stats if no files downloaded if we're in realtime phase or in a session recovery of a realtime-only session

				
			#
			# enter realtime image download loop if enabled
			#
			if g.args['realtimedownload'] != 'disabled':
				realTimeCapture()
		
		#
		# successful completion
		#
		bEchoNewlineBeforeReturning = False
		return (0, False)
		
	except (mtpwifi.MtpConnectionFailureException, ssdp.DiscoverFailureException) as e:
		newConnectErrMsg = str(e)
		if newConnectErrMsg != appMain.lastConnectErrMsg or g.args['suppressdupconnecterrmsgs'] == 'no':
			applog_e(newConnectErrMsg)
			appMain.lastConnectErrMsg = newConnectErrMsg
		else:
			# don't do newline since we're keeping the last connection error message displayed
			bEchoNewlineBeforeReturning = False
		if g.args['printstackframes'] == 'yes':
			applog_e(traceback.format_exc())				
		return (ERRNO_COULDNT_CONNECT_TO_CAMERA, True)
	except mtpwifi.MtpOpExecFailureException as e:
		applog_e(str(e))
		if g.args['printstackframes'] == 'yes':
			applog_e(traceback.format_exc())				
		if e.mtpRespCode == MTP_RESP_COMMUNICATION_ERROR:
			bAttemptCloseSessionAtTermination = False	# since there was a communication error, no sense in attempting to close the MTP session (wastes time, will likely fail anyway)
			return (ERRNO_CAMERA_COMMUNICATION_FAILURE, True)
		else:
			return (ERRNO_CAMERA_UNEXPECTED_RESP_CODE, False) # don't retry on a high-level MTP error - we're trying to do something the camera doesn't like
	except mtpwifi.MtpProtocolException as e:
		applog_e(str(e))
		if g.args['printstackframes'] == 'yes':
			applog_e(traceback.format_exc())
		bAttemptCloseSessionAtTermination = False	# since there was a communication error, no sense in attempting to close the MTP session (wastes time, will likely fail anyway)
		return (ERRNO_CAMERA_PROTOCOL_ERROR, True)
	except socket.error as e:
		applog_e("Socket Error: " + str(e))
		if g.args['printstackframes'] == 'yes':
			applog_e(traceback.format_exc())
		bAttemptCloseSessionAtTermination = False	# since there was a communication error, no sense in attempting to close the MTP session (wastes time, will likely fail anyway)		
		if e.errno != 0: # make sure we're returning a non-zero exit code (not all socket exceptions can be relied on to do so)
			return (e.errno, True)
		else:
			# socket.timeout doesn't define errno. use errno.ETIMEDOUT. also in case the
			# other socket excpetions don't place an errno either
			return (errno.ETIMEDOUT, True)
	except IOError as e:
		applog_e("IOError: " + str(e))
		if g.args['printstackframes'] == 'yes':
			applog_e(traceback.format_exc())
		return (e.errno, False)
	except KeyboardInterrupt as e:
		applog_e("\n>> Terminated by user keypress - cleaning up, please wait... <<")
		if g.args['printstackframes'] == 'yes':
			applog_e(traceback.format_exc())			
		return (errno.EINTR, False)
	except SystemExit as e:
		#
		# someone called sys.exit(). we use sys.exit() for cases where the
		# error condition was captured by higher-level code and a user message
		# generated, thus to avoid printing an exception by this routine.
		# we can still retry these conditions - it depends on whether the caller
		# selected an errno within the "don't retry" range
		#
		if g.args['printstackframes'] == 'yes':
			applog_e(traceback.format_exc())			
		return (e.code, e.code < ERRNO_FIRST_CUSTOM_DONT_RETRY or  e.code > ERRNO_LAST_CUSTOM_DONT_RETRY)
	except: # capture remainder of exceptions, in particular syntax/programming exceptions
		applog_e("An exception occurred. Here is the stack trace information:\n" + traceback.format_exc()) # we always print stack frames for programming errors ('printstackframes' is  ignored)
		return (errno.EFAULT, False)
			
	finally:
		bEndMtpSessionIssuedSuccessfully = False
		if bAttemptCloseSessionAtTermination:
			#
			# end MTP session (MTP_OP_CloseSession). We avoid doing this if we got here from
			# a communication error, since the MTP_OP_CloseSession would likely fail
			# anyway and just take up extra time. However even if a communication error
			# didn't occur there are other situations where the MTP_OP_CloseSession we're about
			# to send might be expected to fail, such as if we were in the middle of an MTP
			# command when the user quit via KeyboardInterrupt. For this reason we squelch
			# any errors/exceptions that might occur during MTP_OP_CloseSession, only reporting
			# the exception to the debug log
			#
			try:
				endMtpSession()
				bEndMtpSessionIssuedSuccessfully = True
			except:
				applog_d("Exception during endMtpSession()")
				applog_d(traceback.format_exc())
		if g.cameraMake == CAMERA_MAKE_SONY:
			if bSessionStarted and (not bEndMtpSessionIssuedSuccessfully or g.args['camerasleepwhendone'] == 'no'):
				#
				# if we started a session and did not put the Sony camera to sleep afterwards then it
				# will remain in the 'Send to Computer' screen/mode. the camera will accept future TCP/IP
				# socket connections but will not respond to any MTP requests, so warn user about this
				#
				applog_i("\nBefore running airnef again please press 'Cancel' on your Sony camera's\n"\
						 "'Send to Computer' screen and select 'Send to Computer' again. Failing to\n"\
						 "do this will cause the next airnef session to not negotiate successfully.")
						 
		if bEchoNewlineBeforeReturning:
			applog_i("")
				
		closeSockets()


#
# deletes all files marked for deletion upon exit. this mechanism is necessary to
# delete a file we were downloading/writing but failed before the operation could
# completed. we don't want to leave a partially written file, otherwise the user
# might think it's a valid file
#
def deleteFilesMarkedForDeletionOnExit():
	for filenameWithPath in g.filesToDeleteOnAppExit:
		applog_d("deleteFilesMarkedForDeletionOnExit(): Processing {:s}".format(filenameWithPath))
		try: # ignore os.path.exists() errors
			if (os.path.exists(filenameWithPath)):
				applog_v("Deleting \"{:s}\" because of a failed download or file operation".format(filenameWithPath))
				deleteFileIgnoreErrors(filenameWithPath)
		except:
			pass

			
#
# invoked near  exit, issues a final log message which is used by utils to signify a gracefully
# shutdown and then tells the applog module to shut itself down
#			
def shutdownApplog():
	applog(">>>> airnefcmd session over - App Exit Time: {:s}".format(strutil.getDateTimeStr(fMilitaryTime=True)), APPLOGF_LEVEL_INFORMATIONAL | APPLOGF_DONT_WRITE_TO_CONSOLE) # used by utils to see if we exited gracefully
	applog_shutdown()

	
#
# main app routine
#			
def main():	

	#
	# establish our app environment, including our app-specific subdirectories
	#
	establishAppEnvironment()
	
	#
	# init applog, to allow logging of output to log files
	#
	_errno = applog_init(APPLOGF_LEVEL_INFORMATIONAL | APPLOGF_LEVEL_ERROR, os.path.join(g.appDataDir, "airnefcmd-log-last.txt"),\
		os.path.join(g.appDataDir, "airnefcmd-log-lifetime.txt"))
	if _errno:
		sys.exit(_errno)
	
	#
	# display app banner
	#
	applog_i("\nairnef v{:s} - Wireless transfer of images/movies for Nikon cameras [GPL v3]".format(AIRNEFCMD_APP_VERSION))
	applog_i("Copyright (c) TestCams.com, Time: {:s}, Py: {:d}.{:d}.{:d}, OS: {:s}\n".format(strutil.getDateTimeStr(fMilitaryTime=True),\
		sys.version_info.major, sys.version_info.minor, sys.version_info.micro,
		platform.system()))
	g.appStartTimeEpoch = time.time()
	
	#
	# verify we're running under a tested version of python
	#
	verifyPythonVersion()	
	
	#
	# process command line arguments
	#
	processCmdLine()
		
	#
	# do app's main work
	#
	attemptNumber = 0
	while True:	
		try:
		
			(_errno, retryRecommended) = appMain()
			if retryRecommended == False:
				# if successful or if user terminated app
				break;
				
			attemptNumber += 1
			if attemptNumber >= g.args['retrycount']:
				applog_i("\nNumber of attempts ({:d}) has reached maximum configured value - exiting".format(attemptNumber))
				break;
						
			# delay until next retry
			secondsToNextRetry = g.args['retrydelaysecs']			
			consoleWriteLine("\rDelaying {:d} seconds before retrying. Press <ctrl-c> to exit [{:d} attempts]: ".format(g.args['retrydelaysecs'], attemptNumber))
			while secondsToNextRetry:
				secondsToNextRetryStr = "{:d}".format(secondsToNextRetry)
				consoleWriteLine(secondsToNextRetryStr)				
				time.sleep(1)
				consoleWriteLine("\b" * len(secondsToNextRetryStr) + " " * len(secondsToNextRetryStr) + "\b" * len(secondsToNextRetryStr))
				secondsToNextRetry -= 1
			consoleClearLine()
			
		except KeyboardInterrupt as e: # in case <ctrl>-c is pressed in delay above
			try: 
				applog_e("\n>> Terminated by user keypress <<\n")
				_errno = errno.EINTR
			except KeyboardInterrupt as e:
				# for some reason we intermittently get a second SIGINT running on Linux frozen; ignore the 2nd
				pass
			break;

	#
	# cleanup and then exit
	#
	deleteFilesMarkedForDeletionOnExit()
	shutdownApplog()
	return _errno

#
# program entry point
#	
if __name__ == "__main__":
	_errno = main()
	sys.exit(_errno)
