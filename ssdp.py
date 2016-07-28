#!/usr/bin/env python

#
#############################################################################
#
# ssdp.py - SSDP routines
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
import socket
#from applog import *
import struct
import select
import time
import sys
import platform
from applog import *

#	
# ssdpTypeFromResponseStr() return values
#
SSDP_TYPE_NONE				= 0	
SSDP_TYPE_MSEARCH			= 1		# "M-SEARCH"
SSDP_TYPE_NOTIFY			= 2		# "NOTIFY"
SSDP_TYPE_RESPONSE			= 3		# "HTTP/1.1"

#
# discover() flags
#
SSDP_DISCOVERF_CREATE_EXTRA_SOCKET_FOR_HOSTNAME_IF			= 0x00000001 # Windows SSDP discovery service workaround - create additional socket and set mutlicast IF to local hostname
SSDP_DISCOVERF_USE_TTL_31									= 0x00000002 # by default we use a TTL of 1 for our SSDP M-SEARCH broadcasts. this options changes it to 31 for wider reach
SSDP_DISCOVERF_ENABLE_MULTICAST_RX_ON_PRIMARY_SOCKET		= 0x00000100 # enable multicast listening on the primary socket
SSDP_DISCOVERF_ENABLE_MULTICAST_RX_ON_HOSTNAME_IF_SOCKET	= 0x00000200 # enable multicast listening on socket created by SSDP_DISCOVERF_CREATE_EXTRA_SOCKET_FOR_HOSTNAME_IF
SSDP_DISCOVERF_ENABLE_MULTICAST_RX_ON_ADDITIONAL_SOCKETS	= 0x00000400 # enable multicast listening on additional socket(s) created by discover(additionalMulticastInterfacesList)

#
# exception thrown by discover() for any encountered errors
#
class DiscoverFailureException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)


'''	

Sample SSDP messages observed on tested cameras. All lines in an SSDP message are suffixed with \r\n.
Some devices also have an empty line at the end of the message.


Sony A7s (multicast advertising):
------------------------------------------------
NOTIFY * HTTP/1.1
HOST: 239.255.255.250:1900
CACHE-CONTROL: max-age=1800
LOCATION: http://192.168.1.209:1900/DeviceDescription.xml
NT: urn:microsoft-com:service:MtpNullService:1
NTS: ssdp:alive
SERVER: FedoraCore/2 UPnP/1.0 MINT-X/1.8.1
USN: uuid:00000000-0001-0010-8000-98f17039c6fc::urn:microsoft-com:service:MtpNullService:1	

Sony A7s (unicast message to our M-SEARCH):
------------------------------------------------
HTTP/1.1 200 OK
CACHE-CONTROL: max-age=1800
EXT:
LOCATION: http://192.168.1.209:1900/DeviceDescription.xml
SERVER: FedoraCore/2 UPnP/1.0 MINT-X/1.8.1
ST: urn:microsoft-com:service:MtpNullService:1
USN: uuid:00000000-0001-0010-8000-98f17039c6fc::urn:microsoft-com:service:MtpNullService:1

Canon 6D (multicast advertising):
------------------------------------------------
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
Cache-Control: max-age=1800
Location: http://192.168.1.10:49152/upnp/CameraDevDesc.xml
NT: urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1
NTS: ssdp:alive
Server: Camera OS/1.0 UPnP/1.0 Canon Device Discovery/1.0
USN: uuid:00000000-0000-0000-0001-2C9EFCD137BE::urn:schemas-canon-com:service:IC
PO-SmartPhoneEOSSystemService:1

Canon 6D (unicast message to our M-SEARCH):
------------------------------------------------
HTTP/1.1 200 OK
Cache-Control: max-age=1800
EXT:
Location: http://192.168.1.10:49152/upnp/CameraDevDesc.xml
Server: Camera OS/1.0 UPnP/1.0 Canon Device Discovery/1.0
ST: urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1
USN: uuid:00000000-0000-0000-0001-2C9EFCD137BE::urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1

Canon 6D (multicast advertising when going to sleep):
------------------------------------------------
NOTIFY * HTTP/1.1
Host: 239.255.255.250:1900
NT: urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1
NTS: ssdp:byebye
USN: uuid:00000000-0000-0000-0001-2C9EFCD137BE::urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1

'''

#
# performs an SSDP discovery broadcast for a specific service.
#
def discover(serviceNameList, ssdpServiceVerifyOkCallback=None, numAttempts=3, timeoutSecsPerAttempt=2, flags=None, additionalMulticastInterfacesList=None):

	#
	# SSDP discovery service involves devices (Cameras for our case) offering services and systems searching for those
	# services. Devices send service availability notifications via "NOTIFY" SSDP messages - computers search for services
	# using "M-SEARCH" SSDP messages. A computer can choose to either passively wait for a device to send a "NOTIFY"
	# message or it can actively send an "M-SEARCH" requests to prompt the device to send it a service response.
	# "NOTIFY" messages are multicasted by devices. Computers multicast "M-SEARCH" as well - a device responds to
	# an "M-SEARCH" by unicasting a response message (prefixed with "HTTP/1.1"). Thus in terms of socket programming
	# there are two methods to discover a device service - either a multicast listen or a multicast sent followed
	# by a unicast listen. The typical way to implement this is the M-SEARCH send/unicast listen, which involves
	# a single socket that sends the M-SEARCH request, which automatically binds the socket to its local port, allowing it to then
	# receive unicast replies from devices, without having to filter out SSDP messages from other devices since the response
	# is unicasted.
	#
	# However during development I found an issue on some Windows machines that prevent outgoing SSDP broadcasts (M-SEARCH) from
	# being transmitted on the wire, which in turn prevents us from ever seeing a unicasted response from the device. The issue
	# appears to be caused by Microsoft's "SSDP Discovery" service - when that service is enabled it cycles which interface
	# our INADDR_ANY UDP multicasts go out over, even on systems with only a single physical interface (for example, virtual network
	# interfaces created by VMware on the Host OS). I created a stack overflow article about this here:
	# http://stackoverflow.com/questions/32682969/windows-ssdp-discovery-service-throttling-outgoing-ssdp-broadcasts
	#
	# The workaround is to create an additional socket (Windows only) and set its explicit multicast IF to the IP address associated
	# with the local hostname (default interface). I also provided the ability for additional sockets to be created that listen
	# on specific interfaces (additionalMulticastInterfacesList paramter)
	#

	group = ("239.255.255.250", 1900)
	message = "\r\n".join([
		'M-SEARCH * HTTP/1.1',
		'HOST: {}:{}',
		'MAN: "ssdp:discover"',
		'ST: {}','MX: 1','USER-AGENT: Windows/7.0/7.0','',''])
		
	if flags == None:
		# no flags specified - decide best flags based on platform
		if platform.system() == 'Windows':
			flags = SSDP_DISCOVERF_CREATE_EXTRA_SOCKET_FOR_HOSTNAME_IF # Windows SSDP Discovery service
		else:
			flags = 0
			
	#
	# we will be creating one or more sockets that will be used for sending SSDP multicasts
	# and listening for a response
	#
	sockList = []

	#
	# create primary socket that will be used to TX M-SEARCH and receive unicasted RX responses. We can optionally
	# make this socket a multicast listener as well
	#
	try:
		sock = createUdpSocket(flags)
		if flags & SSDP_DISCOVERF_ENABLE_MULTICAST_RX_ON_PRIMARY_SOCKET:
			setUdpSocketForMulticastReceive(sock, group, "0.0.0.0") # INADDR_ANY
		sockList.append(sock)
	except socket.error as e:
		raise DiscoverFailureException("Networking error preparing for SSDP Discovery: {:s}".format(str(e)))
		
	#
	# create extra socket for the hostname interface if specified(Windows SSDP Discovery service workaruond)
	#
	if flags & SSDP_DISCOVERF_CREATE_EXTRA_SOCKET_FOR_HOSTNAME_IF:
		try:
			hostNameIpAddr = getHostnameIpAddrStr()
			sock = createUdpSocket(flags)
			sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(hostNameIpAddr))
			if flags & SSDP_DISCOVERF_ENABLE_MULTICAST_RX_ON_HOSTNAME_IF_SOCKET:
				setUdpSocketForMulticastReceive(sock, group, hostNameIpAddr)
			sockList.append(sock)
		except socket.error as e:
			applog_w("Warning: Unable to prepare hostname socket for SSDP Discovery: {:s}".format(str(e)))
			# let attempt continue since we have a primary socket to use
			
	#
	# create additional sockets if specified
	#	
	if additionalMulticastInterfacesList:
		for ipAddressStr in additionalMulticastInterfacesList:
			try:
				sock = createUdpSocket(flags)
				sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ipAddressStr))
				if flags & SSDP_DISCOVERF_ENABLE_MULTICAST_RX_ON_ADDITIONAL_SOCKETS:
					setUdpSocketForMulticastReceive(sock, group, ipAddressStr)
				sockList.append(sock)
			except socket.error as e:
				raise DiscoverFailureException("Error creating additional socket for \"{:s}\": {:s}".format(ipAddressStr, str(e)))	
			
		
	#
	# loop for sending M-SEARCH messages and listening for unicasted responses/multicasted service advertisements
	#
	for nthAttempt in xrange(numAttempts):
	
		try:
		
			timeStartThisAttempt = time.time()
		
			#
			# send our M-SEARCH multicasts on each socket
			#
			for sockIndex,sock in enumerate(sockList):
				for serviceNameStr in serviceNameList:
					applog_d("SSDP TX broadcast[{:d}]: {:s}".format(sockIndex, serviceNameStr))
					sock.sendto(message.format(group[0], group[1], serviceNameStr).encode(), group)
			
			#			
			# listen for unicasted responses and/or multicasted service advertisements
			#			
			while True:
				elapsedTimeThisAttemptSecs = time.time() - timeStartThisAttempt
				if elapsedTimeThisAttemptSecs >= float(timeoutSecsPerAttempt):
					# exceed time allowance for this attempt
					break
				# wait for one or more sockets to have data
				(socketsWithRxData, socketsReadyTxData, socketsError) = select.select(sockList, [], [], float(timeoutSecsPerAttempt) - elapsedTimeThisAttemptSecs)
				# perform receive of queued data for all sockets with data available
				for sock in socketsWithRxData:
					ssdpMessageRaw = sock.recv(4096)
					ssdpMessage = six.text_type(ssdpMessageRaw, 'utf-8')
					if ssdpMessage.startswith("M-SEARCH"):
						# this is a search packet, either our own or someone else's - disregard
						continue
					#
					# received an SSDP unicasted response/multicasted advertisement. we generally don't
					# need to qualify unicasted responses since they're directed to us for the service
					# we ask for whereas we need to qualify multicasted advertisements since those
					# can come from anyone. I qualify the unicasted responses anyway to make sure it
					# conforms to the service we need. note that we optionally invoke a user callback
					# to further qualify the service as being suitable for what he needs
					#
					applog_d("SSDP Message [socket #{:d}]:\n{:s}".format(sockList.index(sock), ssdpMessage))
					for serviceNameStr in serviceNameList:
						if isMessageForService(ssdpMessage, serviceNameStr) and (ssdpServiceVerifyOkCallback == None or ssdpServiceVerifyOkCallback(ssdpMessage)):
							# SSDP message is for a service caller wants and he optionally qualify it further - we're done
							for sock in sockList:
								sock.close()							
							return ssdpMessage
		except (socket.timeout, socket.error, select.error) as e:
			# FYI, shouldn't see a socket.timeout since we're using select()
			for sock in sockList:
				sock.close()		
			raise DiscoverFailureException("Network error during SSDP Discovery: {:s}".format(str(e)))

				
	#
	# all attempts failed to discover a service the caller wanted
	#
	for sock in sockList:
		sock.close()
	return None	


def createUdpSocket(discoverFlags):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 31 if (discoverFlags & SSDP_DISCOVERF_USE_TTL_31) else 1)
	return sock
	
#
# prepares a UDP socket for multicast receives
#
def setUdpSocketForMulticastReceive(sock, multicastGroupTuple, ipAddressStrOfMulticastInterface):
	sock.bind(("", multicastGroupTuple[1]))
	sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(multicastGroupTuple[0]) + socket.inet_aton(ipAddressStrOfMulticastInterface))

	
#
# gets the IP address (as string) of local hostname
#	
def getHostnameIpAddrStr():
	ipAddrStr = socket.gethostbyname(socket.gethostname())
	applog_d("getHostnameIpAddrStr(): " + ipAddrStr)
	return ipAddrStr
	
	
#
# gets the contents of the specified header for a given SSDP advertise (NOTIFY) or response (HTTP/1.1) string
#
def getHeader(ssdpMessage, headerNameStr):
	#
	# note that the header field name is case-insensitive but the field value (after colon)
	# is case-sensitive, per the UPnP spec
	#
	if ssdpMessage == None:
		return None					
	headerNameStr = headerNameStr.upper() + ':'	
	messageLines = ssdpMessage.split('\n')
	for line in messageLines:
		line = line.lstrip()
		if line.upper().startswith(headerNameStr): # field names are case-insensitive, so both are compared in uppercase
			return line[len(headerNameStr):].lstrip().rstrip()
	return None

	
#
# determines the type of an SSDP message
# 	
def ssdpTypeFromMessage(ssdpMessage):
	if ssdpMessage == None:
		return None
	s = ssdpMessage.lstrip()
	if s.startswith("M-SEARCH"):
		return SSDP_TYPE_MSEARCH
	if s.startswith("NOTIFY"):
		return SSDP_TYPE_NOTIFY
	if s.startswith("HTTP"):
		return SSDP_TYPE_RESPONSE
	return SSDP_TYPE_NONE


#
# determines if an SSDP advertise (NOTIFY) or response (HTTP/1.1) string is for a given service 
#	
def isMessageForService(ssdpMessage, serviceNameStr):

	ssdpType = ssdpTypeFromMessage(ssdpMessage)
	
	if ssdpType == SSDP_TYPE_MSEARCH:
		# this is a search packet, either our own or someone else's - disregard
		return False
		
	#
	# if this is a NOTIFY (multicast advertising of service rather than 
	# a unicast response to our M-SEARCH) then the message should include
	# a notification status - make sure the status indicates that the
	# service is available (ie,  SSD:ALIVE rather than SSDP:BYEBYE). Canon
	# cameras send out a SSDP:BYEBYE when going into sleep mode
	#
	notificationStatus = getHeader(ssdpMessage, "nts")
	if notificationStatus and notificationStatus.startswith("ssdp:alive") == False:
		return False
	
	#
	# check for both Notification Type (unicast response to our search request) and
	# Service Type (unsolicited multicast advertising of service)
	#
	typeContents = getHeader(ssdpMessage, "st")
	if typeContents == None:
		typeContents = getHeader(ssdpMessage, "nt")
		if typeContents == None:
			return False
			
	if not typeContents.startswith(serviceNameStr):
		return False
		
	return True
	
#
# extracts the IP address from the "LOCATION:" header of an SSDP message
#	
def extractIpAddressFromSSDPMessage(ssdpMessage):
	# sample: http://192.168.1.209:1900/DeviceDescription.xml\n
	locationStr = getHeader(ssdpMessage, "location")
	if locationStr == None:
		return None
	startIpAddrPos = locationStr.find("http://")
	if startIpAddrPos != -1:
		startIpAddrPos += 7 # past "http://"
		endIpAddrPos = locationStr.find(":", startIpAddrPos)
		if endIpAddrPos != -1:
			ipAddrStr = locationStr[startIpAddrPos:endIpAddrPos]
			return ipAddrStr
	return None


#
# module test
#
'''
def applog_w(str):
	print(str)
def applog_e(str):
	print(str)
def applog_i(str):
	print(str)
def applog_d(str):
	print(str)
	
def testModule():	
	print("calling discover()")
	resp = discover(["urn:microsoft-com:service:MtpNullService:1", "urn:schemas-canon-com:service:ICPO-SmartPhoneEOSSystemService:1" ],\
		lambda (ssdpMessage) : extractIpAddressFromSSDPMessage(ssdpMessage) != None,
		numAttempts=999999, timeoutSecsPerAttempt=2)
	if resp:
		print("Matched SSDP Message:\n" + resp)
		ipAddress = extractIpAddressFromSSDPMessage(resp)
		print("IP Address: " + ipAddress)	
testModule()
'''