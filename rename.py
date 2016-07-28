#!/usr/bin/env python

#
#############################################################################
#
# rename - File renaming engine
# Copyright (C) 2015, testcams.com
#
# This module is licensed under GPL v3: http://www.gnu.org/licenses/gpl-3.0.html
#
#############################################################################
#

from __future__ import print_function
from __future__ import division
import six
import os
import re
import time

#
# exception class for rename parsing errors
#
class GenerateReplacementNameException(Exception):
		def __init__(self, message):
			Exception.__init__(self, message)

#
# converts a day of year (1-366) to a season string
# 	
def dayOfYearToSeason(dayOfYear):
	if dayOfYear >= 80 and dayOfYear < 172:
		season = "Spring"
	elif dayOfYear >= 172 and dayOfYear < 264:
		season = "Summer"
	elif dayOfYear >= 264 and dayOfYear < 355:
		season = "Fall"
	else:
		season = "Winter"
	return season


#
# verifies the syntax of a rename format string
#	
def verifyRenameFormatStringSyntax(formatString):
	renameDict = createTestRenameDict()
	performRename(formatString, renameDict)


#
# gets the starting and ending character position of the next
# specifier in the format string
#	
def getNextSpecifierPos(formatString, formatStringPos):
	nextSpecifierStartPos = formatString.find('@', formatStringPos)
	if nextSpecifierStartPos == -1:
		# no more specifiers
		return (-1, -1)
	#
	# find end of the specifier
	#
	nextSpecifierEndPos = formatString.find('@', nextSpecifierStartPos+1)
	if nextSpecifierEndPos == -1:
		raise GenerateReplacementNameException("Missing specifier after @ at character #{:d}".format(nextSpecifierStartPos))
		
	return (nextSpecifierStartPos, nextSpecifierEndPos)
	
#
# performs a rename operation
#
def performRename(formatString, parmsDict):

	#
	# build dictionary that translates specifiers
	#
	
	captureTimeStruct = time.localtime(parmsDict['captureDateEpoch'])
	downloadTimeStruct = time.localtime(parmsDict['downloadDateEpoch'])
	
	specifierTranslationDict = dict()
	
	specifierTranslationDict['capturedate'] = time.strftime("%Y%m%d", captureTimeStruct)      	# date captured full (numeric)
	specifierTranslationDict['capturedate_m'] = time.strftime("%m", captureTimeStruct)				# date captured month (numeric)
	specifierTranslationDict['capturedate_d'] = time.strftime("%d", captureTimeStruct)				# date captured day (numeric)
	specifierTranslationDict['capturedate_y'] = time.strftime("%Y", captureTimeStruct)				# date captured year (numeric)
	specifierTranslationDict['capturedate_dow'] = str(captureTimeStruct.tm_wday+1)					# date captured day of week (numeric, 1=Monday)
	specifierTranslationDict['capturedate_woy'] = time.strftime("%W", captureTimeStruct)			# date captured week of year (numeric, Monday first day of week)
	specifierTranslationDict['capturedate_month'] = time.strftime("%B", captureTimeStruct)			# date captured month (text)
	specifierTranslationDict['capturedate_dayofweek'] = time.strftime("%A", captureTimeStruct)		# date captured day of week (text)
	specifierTranslationDict['capturedate_season'] = dayOfYearToSeason(captureTimeStruct.tm_yday)	# date captured season (text)

	specifierTranslationDict['capturetime'] = time.strftime("%H%M%S", captureTimeStruct)			# time captured full
	specifierTranslationDict['capturetime_h'] = time.strftime("%H", captureTimeStruct)				# time captured hour (military)
	specifierTranslationDict['capturetime_m'] = time.strftime("%M", captureTimeStruct)				# capure time minute
	specifierTranslationDict['capturetime_s'] = time.strftime("%S", captureTimeStruct)				# time captured seconds
	
	specifierTranslationDict['dldate'] = time.strftime("%Y%m%d", downloadTimeStruct)      			# date downloaded full (numeric)
	specifierTranslationDict['dldate_m'] = time.strftime("%m", downloadTimeStruct)					# date downloaded month (numeric)
	specifierTranslationDict['dldate_d'] = time.strftime("%d", downloadTimeStruct)					# date downloaded day (numeric)
	specifierTranslationDict['dldate_y'] = time.strftime("%Y", downloadTimeStruct)					# date downloaded year (numeric)
	specifierTranslationDict['dldate_dow'] = str(downloadTimeStruct.tm_wday+1)						# date downloaded day of week (numeric, 1=Monday)
	specifierTranslationDict['dldate_woy'] = time.strftime("%W", downloadTimeStruct)				# date downloaded week of year (numeric, Monday first day of week)
	specifierTranslationDict['dldate_month'] = time.strftime("%B", downloadTimeStruct)				# date downloaded month (text)
	specifierTranslationDict['dldate_dayofweek'] = time.strftime("%A", downloadTimeStruct)			# date downloaded day of week (text)
	specifierTranslationDict['dldate_season'] = dayOfYearToSeason(downloadTimeStruct.tm_yday)		# date downloaded season (text)

	specifierTranslationDict['dltime'] = time.strftime("%H%M%S", downloadTimeStruct)				# time downloaded full
	specifierTranslationDict['dltime_h'] = time.strftime("%H", downloadTimeStruct)					# time downloaded hour (military)
	specifierTranslationDict['dltime_m'] = time.strftime("%M", downloadTimeStruct)					# capure time minute
	specifierTranslationDict['dltime_s'] = time.strftime("%S", downloadTimeStruct)					# time downloaded seconds

	specifierTranslationDict['filename'] = parmsDict['filename']									# local filename 
	specifierTranslationDict['filename_root'] = os.path.splitext(parmsDict['filename'])[0]			# local filename base (filename without extension)
	specifierTranslationDict['filename_ext'] = os.path.splitext(parmsDict['filename'])[1][1:]		# local filename extension	
	specifierTranslationDict['capturefilename'] = parmsDict['capturefilename']						# capture filename 
	specifierTranslationDict['capturefilename_root'] = os.path.splitext(parmsDict['capturefilename'])[0]	# capture filename base (filename without extension)
	specifierTranslationDict['capturefilename_ext'] = os.path.splitext(parmsDict['capturefilename'])[1][1:]	# capture filename extension
	specifierTranslationDict['path'] = parmsDict['path']											# path
	specifierTranslationDict['pf'] = os.path.join(parmsDict['path'], parmsDict['filename'])			# path+filename
		
	specifierTranslationDict['camerafolder'] = parmsDict['camerafolder']							# camera folder file is in
	specifierTranslationDict['slotnumber'] = str(parmsDict['slotnumber'])							# camera media slot # file was downloaded from

	specifierTranslationDict['cameramake'] = parmsDict['cameramake']								# camera make
	specifierTranslationDict['cameramodel'] = parmsDict['cameramodel']								# camera model
	specifierTranslationDict['cameraserial'] = parmsDict['cameraserial'] 							# camera serial number
	
	specifierTranslationDict['dlnum'] = "{:04d}".format(parmsDict['dlnum'])							# download number this session
	specifierTranslationDict['dlnum_lifetime'] = "{:04d}".format(parmsDict['dlnum_lifetime'])		# download number lifetime for this model/serial

	formatStringLen = len(formatString)
	formatStringPos = 0
	outputName = ""
	while formatStringPos < formatStringLen:

		#
		# find next specifier
		#
		(nextSpecifierStartPos, nextSpecifierEndPos) = getNextSpecifierPos(formatString, formatStringPos)
	
		if nextSpecifierStartPos == -1:
			# no more specifiers - insert remainder of format string into output
			outputName += formatString[formatStringPos:]
			break;
				
		#
		# insert from format string up to start of this specifier
		#
		outputName += formatString[formatStringPos:nextSpecifierStartPos]
			
		formatStringPos = nextSpecifierEndPos+1 # advance past specifier in preparation for next loop iteration
		
		#
		# extract specifier to do replacment insertion. example specifier formats:
		#	@filename@			- Filename
		#	@filename:0:2@ 		- Filename, characters 0 through 1
		#	@filename:4:@		- Filename, characters 4 through end
		#	@filename::1@		- Filename, character 0
		#	@filename:-2:@		- Filename, last two characters
		#	@filename:4:-2:@	- Filename, characters 4 through to last two characters
		#
		#
		specifierForReporting = formatString[nextSpecifierStartPos:nextSpecifierEndPos+1]	# for use in reporting errors, entire specifier in original case including enclosing @@
		specifierWithArgs = formatString[nextSpecifierStartPos+1:nextSpecifierEndPos]		# the entire specifier with optional args included (everything between @@)
		if not specifierWithArgs:
			# found '@@', which means literal '@'
			outputName += '@'
			continue			
		specifierWithArgsLowercase = specifierWithArgs.lower()
			
		if specifierWithArgsLowercase.find('replace',0,7) != -1:
			#
			# special case specifier that does search/replace on output string built
			# up to this point. Matches case of search/replace string as written. Formats:
			#
			# @replace~findstr~newstr@
			# @replacere~findstr~newstr~ (regular expression version)
			#
			replaceList = specifierWithArgs.split('~')
			if len(replaceList)==1:
				raise GenerateReplacementNameException("No search string specified after specifier {:s} at character #{:d}".format(specifierForReporting, nextSpecifierStartPos))
			if len(replaceList)==2:
				raise GenerateReplacementNameException("No replacement string specified after specifier {:s} at character #{:d}".format(specifierForReporting, nextSpecifierStartPos))
			if len(replaceList) > 3:
				raise GenerateReplacementNameException("Too many fields for specifier {:s} at character #{:d}".format(specifierForReporting, nextSpecifierStartPos))			
			if replaceList[0] == 'replace':				
				outputName = outputName.replace(replaceList[1], replaceList[2])
			elif replaceList[0] == 'replacere':
				outputName = re.sub(replaceList[1], replaceList[2], outputName)
			else:
				raise GenerateReplacementNameException("Unknown specifier {:s} at character #{:d}".format(specifierForReporting, nextSpecifierStartPos))			
			continue
		
		specifierList = specifierWithArgs.split(':')
		speciferName = specifierList[0]
		specifierListLowercase = specifierWithArgsLowercase.split(':')
		speciferNameLowercase = specifierListLowercase[0]
								
		if speciferNameLowercase not in specifierTranslationDict:
			raise GenerateReplacementNameException("Unknown specifier {:s} at character #{:d}".format(specifierForReporting, nextSpecifierStartPos))		

		if len(specifierListLowercase) > 4:
			raise GenerateReplacementNameException("Too many subscripts to specifier {:s} at character #{:d}".format(specifierForReporting, nextSpecifierStartPos))		
		specifierSubscript_Start = 0
		specifierSubscript_End = 9999 # arbitrary large number to get all of string
		if len(specifierListLowercase) >= 2:
			if specifierListLowercase[1]:
				try:
					specifierSubscript_Start = int(specifierListLowercase[1])
				except ValueError as e:
					raise GenerateReplacementNameException("First subscript value is not integer for specifier {:s} at character #{:d}".format(specifierForReporting, nextSpecifierStartPos))
		if len(specifierListLowercase) >= 3:
			if specifierListLowercase[2]:
				try:
					specifierSubscript_End = int(specifierListLowercase[2])
				except ValueError as e:
					raise GenerateReplacementNameException("Second subscript value is not integer for specifier {:s} at character #{:d}".format(specifierForReporting, nextSpecifierStartPos))
		optionsLowercase = ""
		if len(specifierListLowercase) >= 4:
			if specifierListLowercase[3]:
				optionsLowercase = specifierListLowercase[3]
									
		strToAdd = specifierTranslationDict[speciferNameLowercase][specifierSubscript_Start:specifierSubscript_End]
		
		# process options
		if optionsLowercase.find('u') != -1:
			# uppercase
			strToAdd = strToAdd.upper()
		if optionsLowercase.find('l') != -1:
			# lowercase
			strToAdd = strToAdd.lower()
		if optionsLowercase.find('c') != -1:
			# capitalize
			strToAdd = strToAdd.capitalize()
		
		# add generated specifier output to string we're building
		outputName += strToAdd
		
	return outputName	


#
# determines if a particular specifier is in the format string
#
def isSpecifierInFormatString(formatString, specifierName):
	specifierName = specifierName.lower() # for case-insensitive match
	formatStringLen = len(formatString)
	formatStringPos = 0
	while formatStringPos < formatStringLen:
		# find next specifier
		(nextSpecifierStartPos, nextSpecifierEndPos) = getNextSpecifierPos(formatString, formatStringPos)	
		if nextSpecifierStartPos == -1:
			return False
		specifierWithArgs = formatString[nextSpecifierStartPos+1:nextSpecifierEndPos]		# the entire specifier with optional args included (everything between @@)
		specifierList = specifierWithArgs.split(':')
		speciferName = specifierList[0].lower()
		if speciferName == specifierName:
			return True
		formatStringPos = nextSpecifierEndPos+1 # advance past specifier for next loop iteration
	return False


#
# creates a dummy rename dictionary, which is used for verifying syntax
# of format string and for module testing
#
def createTestRenameDict():
	renameDict = dict()
	renameDict['captureDateEpoch'] = time.time()
	renameDict['downloadDateEpoch'] = time.time()
	renameDict['filename'] = "DSC_0014.sthumb.jpg"
	renameDict['capturefilename'] = "DSC_0014.NEF"
	renameDict['path'] = "c:\pics"
	renameDict['camerafolder'] = "100D7200"
	renameDict['slotnumber'] = 1
	renameDict['captureDateEpoch'] = time.time()
	renameDict['downloadDateEpoch'] = time.time()	
	renameDict['cameramake'] = "Nikon"
	renameDict['cameramodel'] = "D7200"
	renameDict['cameraserial'] = "3434234"
	renameDict['dlnum'] = 0
	renameDict['dlnum_lifetime'] = 1000
	return renameDict


#
# tests the functioning of this module
#
def testModule():

	renameDict = createTestRenameDict()

	print(performRename("date capture: @capturedate@ = @capturedate_m@-@capturedate_d@-@capturedate_y@", renameDict))
	print(performRename("date capture: @capturedate_dow@ = @capturedate_dayofweek@, Week of Year = @capturedate_woy@, Month = @Capturedate_month@, Season = @Capturedate_season@", renameDict))
	print(performRename("time capture: @capturetime@ = @capturetime_h@:@capturetime_m@:@capturetime_s@", renameDict))
	print(performRename("date downloaded: @dldate@ = @dldate_m@-@dldate_d@-@dldate_y@", renameDict))
	print(performRename("date downloaded: @dldate_dow@ = @dldate_dayofweek@, Week of Year = @dldate_woy@, Month = @Dldate_month@, Season = @Dldate_season@", renameDict))
	print(performRename("time downloaded: @dltime@ = @dltime_h@:@dltime_m@:@dltime_s@", renameDict))
	print(performRename("pf=@pf@, filename=@filename@, root=@filename_root@, ext=@filename_ext@, dir=@CAMERAFOLDER@", renameDict))
	print(performRename("capfilename=@capturefilename@, capturefilenameroot=@capturefilename_root@, capturefilenameext=@capturefilename_ext@, path=@PATH@", renameDict))
	print(performRename("camera make=@Cameramake@, model=@Cameramodel@, serial=@cameraserial@", renameDict))
	print(performRename("download # this session @dlnum@, lifetime=@dlnum_lifetime@", renameDict))
	print(performRename("camera make=@Cameramake:::c@@replace~Nikon~Canon@@replacere~Canon~Nikon@", renameDict))
	
	print(isSpecifierInFormatString("this is a test @first@ @second@ @cameramake:343:434@ of this routine", "cameramake"))
	print(isSpecifierInFormatString("this is a test @first@ @second@ @cameramake@ of this routine@test@", "cameramakes"))
	
#testModule()