#!/usr/bin/env python

#
#############################################################################
#
# mtpwifi.py - Nikon MTP over Wifi interface
# Copyright (C) 2015, testcams.com
#
# This module is licensed under GPL v3: http://www.gnu.org/licenses/gpl-3.0.html
#
# This module is based on the awesome work done by Joe FitzPatrick in
# reverse engineering the Nikon Wifi interface. Information about his work
# can be found in the following links, including sample python source this
# module was based on.
#
# https://nikonhacker.com/wiki/WU-1a
# https://github.com/securelyfitz/Nikon/tree/master/wu-1a%20hacking
#
#############################################################################
#

from __future__ import print_function
from __future__ import division
import six
import socket
import sys
import struct
import time
import strutil
import errno
from applog import *
from mtpdef import *
from collections import namedtuple

#
# module constants
#
SOCKET_TIMEOUT_CONNECT_SECS_DEFAULT		= 10	# timeout for connect attempts
SOCKET_TIMEOUT_READS_WRITES_DEFAULT		= 5		# we configure the socket to time out send/receive requests after 5 seconds

#
# types of low-level PTP-TCP/IP commands that can be send
# from Host -> Camera
#
MTP_TCPIP_REQ_INIT_CMD_REQ			= 0x01	# "host introduction" is arbtirary name - don't know what undocumented PTP-TCP/IP spec calls it
MTP_TCPIP_REQ_INIT_EVENTS			= 0x03	# "init events" is arbtirary name - don't know what undocumented PTP-TCP/IP spec calls it
MTP_TCPIP_REQ_PROBE					= 0x0d  # "probe request"

#
# identifiers for types of payloads that can be sent
# between Host <-> Camera
#
MTP_TCPIP_PAYLOAD_ID_CmdReq				= 0x06	# "cmd req" is arbtirary name - don't know what undocumented PTP-TCP/IP spec calls it
MTP_TCPIP_PAYLOAD_ID_CmdResponse		= 0x07	# "cmd response" is arbtirary name - don't know what undocumented PTP-TCP/IP spec calls it
MTP_TCPIP_PAYLOAD_ID_DataStart			= 0x09	# "data start" is arbtirary name - don't know what undocumented PTP-TCP/IP spec calls it
MTP_TCPIP_PAYLOAD_ID_DataPayload		= 0x0a 	# "data payload" is arbtirary name - don't know what undocumented PTP-TCP/IP spec calls it
MTP_TCPIP_PAYLOAD_ID_DataPayloadLast	= 0x0c	# "data payload last" is arbtirary name - don't know what undocumented PTP-TCP/IP spec calls it

MTP_TCPIP_CmdReq_DataDir_CameraToHost_or_None = 0x1	# data direction is Camera -> Host or No Data
MTP_TCPIP_CmdReq_DataDir_HostToCamera = 0x2			# data direction is Host -> Camera

#
# structure (named tuple) returned by our execMtpOp() method
#
MtpTcpCmdResult = namedtuple('MTPTcpCmdResult', 'mtpRespCode mtpResponseParameter dataReceived')

#
# exceptions thrown by our methods. 
#
class MtpOpExecFailureException(Exception):
	def __init__(self, mtpRespCode, message, partialData=None, totalPayloadSizeIndicated=None):
		Exception.__init__(self, message)
		self.mtpRespCode = mtpRespCode
		self.partialData = partialData
		self.totalPayloadSizeIndicated = totalPayloadSizeIndicated
		
class MtpProtocolException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)
			
class MtpConnectionFailureException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)

#
# global data
#
gTransferInterruptedBySIGINT = False
g_PartialRxDataPayloadData = None
g_PartialRxDataPayloadData_SizeIndicated = None


#
# Iterator that generates a transaction ID for MTP-TCP/IP requests,
# which increments by one for each generation
#
def transactionIdCounter():
	k = 0
	while True:
		k += 1
		yield k
generateTransactionId = transactionIdCounter()

#
# Transmits data over MTP-TCP/IP socket
#
def txdata(s, data):
	if isDebugLog():
		applog_d(strutil.hexdump(data[:min(len(data),1024)]))
	s.send(struct.pack('<I',len(data)+4)+data)
	
#
# Receives a payload over a MTP-TCP/IP socket
#
def rxPayload(s, rxProgressFunc=None):

	global g_PartialRxDataPayloadData, g_PartialRxDataPayloadData_SizeIndicated

	totalPayloadBytes = 0			# need to initialize here in case exception occurs before var is set
	payloadBytesReceived = 0		# need to initialize here in case exception occurs before var is set
	payloadId = None
	data = six.binary_type()
	g_PartialRxDataPayloadData = None
	g_PartialRxDataPayloadData_SizeIndicated = 0
	try:
	
		# transmitter first sends word indicating size of payload to follow
		dataPreamble = s.recv(4)
		if len(dataPreamble) < 4:
			raise socket.error(errno.EBADF, "TCP/IP error receiving data - received insufficient payload preamble bytes (exp=4, got=0x{:x})".format(len(dataPreamble)))
		(totalBytesIncludingPreamble,) = struct.unpack('<I', dataPreamble)
		totalPayloadBytes = totalBytesIncludingPreamble-4

		# receive the payload
		while (payloadBytesReceived < totalPayloadBytes):		
			data += s.recv(totalPayloadBytes - payloadBytesReceived)
			if not payloadId and len(data) >= 4:
				# if we have not received the payload ID and we have at least 4 bytes of data (first four bytes has payload ID)
				(payloadId,) = struct.unpack('<I', data[0:4])
			payloadBytesReceived = len(data)
			if rxProgressFunc and payloadBytesReceived >= 8 and (payloadId == MTP_TCPIP_PAYLOAD_ID_DataPayload or payloadId == MTP_TCPIP_PAYLOAD_ID_DataPayloadLast):
				rxProgressFunc(payloadBytesReceived - 8) # -8 to exclude header data from count
				
		# return the data received [not including 4-byte size preamble]
		return data
	except socket.error as error:
		if payloadBytesReceived and (payloadId == MTP_TCPIP_PAYLOAD_ID_DataPayload or payloadId == MTP_TCPIP_PAYLOAD_ID_DataPayloadLast) and\
		  payloadBytesReceived >= 12:
			#
			# if this is a data payload and we received at least 12 bytes of data (8 bytes of header data, so at least 4 bytes of actual data),
			# save it to off to support retry invocation logic (use MTP_OP_GetPartialObject for future retry)
			#
			g_PartialRxDataPayloadData = data
			g_PartialRxDataPayloadData_SizeIndicated = totalPayloadBytes
		raise # let upper levels print out contents of actual socket.error exception

		
#
# Transmits request and receives response payload(s)
#
def txrxdata(s, data):
	txdata(s, data)
	return rxPayload(s)
	

#
# perform an MTP operation/command
#
# Here is brief summary of the communication protocol, as reversed enginerred by Joe.
# There are four types of frames - MTP_TCPIP_PAYLOAD_ID_CmdReq, MTP_TCPIP_PAYLOAD_ID_DataStart,
# MTP_TCPIP_PAYLOAD_ID_DataPayload/MTP_TCPIP_PAYLOAD_ID_DataPayloadLast  and
# MTP_TCPIP_PAYLOAD_ID_CmdResponse. Every frame is preceded by a single 32-word that
# describes the byte length of the frame, including the 4-byte frame length itself.
#
# Starts with host sending a command request frame to the camera:
#
#	bytes 0x00 - 0x03: 0x00000006 (MTP_TCPIP_PAYLOAD_ID_CmdReq)
#	bytes 0x04 - 0x07: MTP_TCPIP_CmdReq_DataDir_CameraToHost_or_None(0x00000001) or MTP_TCPIP_CmdReq_DataDir_HostToCamera(0x00000002)
#	bytes 0x08 - 0x09: MTP_OP_* opcode, such as MTP_OP_GetNumObjects
#	bytes 0x0a - 0x0d: transaction ID [increments every request]
#	bytes 0x0e - ....: command-specific arguments
#
# If the command's data direction is Host->Camera, we then send DataStart
# and DataPayload frames.
#
# DataStart:
#
#	bytes 0x00 - 0x03: 0x00000009 MTP_TCPIP_PAYLOAD_ID_DataStart
#	bytes 0x04 - 0x07: transaction ID [same value sent in MTP_TCPIP_PAYLOAD_ID_CmdReq]
#	bytes 0x08 - 0x0b: Data size
#   bytes 0x0c - 0x0f: Always 0x00000000
#
# DataPayload - Nikon only uses one payload (MTP_TCPIP_PAYLOAD_ID_DataPayloadLast),
#				Canon uses MTP_TCPIP_PAYLOAD_ID_DataPayload for 1..n-1, then
#				MTP_TCPIP_PAYLOAD_ID_DataPayloadLast for the final data payload
#
#	bytes 0x00 - 0x03: 0x0000000a or 0x0000000c: MTP_TCPIP_PAYLOAD_ID_DataPayload or MTP_TCPIP_PAYLOAD_ID_DataPayloadLast
#	bytes 0x04 - 0x07: transaction ID [same value send in MTP_TCPIP_PAYLOAD_ID_CmdReq]
#	bytes 0x08 - ....: data payload
#
# If the command's data direction is Camera->Host, then the camera sends the above
# Data Start and DataPayload frames. If the command has no data associated with it
# then no Data Start/DataPayload frames are sent by either side.
#
# After the command request and potential data start/payload frames are sent, the
# camera sends a command response frame when it has completed processing the command:
#
# CmdResponse:
#
#	bytes 0x00 - 0x03: 0x00000007: MTP_TCPIP_PAYLOAD_ID_CmdResponse
#	bytes 0x04 - 0x05: MTP response code (see nikmtp.MTP_RESP_* values)
#	bytes 0x06 - 0x09: transaction ID [same value send in MTP_TCPIP_PAYLOAD_ID_CmdReq]
#	bytes 0x0a - 0x0d: response parameter [32-bit "return value" for certain commands]
#
def execMtpOp_rxPayloadProgressFunc(totalBytesReceivedThisPayload, rxTxProgressFunc, countBytesReceivedAcrossAllPayloads, totalDataTransferSizeBytesExpectedAcrossAllPayloads):
	if rxTxProgressFunc:
		rxTxProgressFunc(countBytesReceivedAcrossAllPayloads + totalBytesReceivedThisPayload,
			totalDataTransferSizeBytesExpectedAcrossAllPayloads)

def execMtpOp(s, mtpOp, cmdArgsPacked=six.binary_type(), dataToSend=six.binary_type(), rxTxProgressFunc=None):

	mtpDataDirToCmdReqDataDirectionCode={
		MTP_DATA_DIRECTION_NONE : MTP_TCPIP_CmdReq_DataDir_CameraToHost_or_None,
		MTP_DATA_DIRECTION_CAMERA_TO_HOST : MTP_TCPIP_CmdReq_DataDir_CameraToHost_or_None,
		MTP_DATA_DIRECTION_HOST_TO_CAMERA : MTP_TCPIP_CmdReq_DataDir_HostToCamera,
	}
	
	global gTransferInterruptedBySIGINT
	if gTransferInterruptedBySIGINT:
		#
		# if a previous invocation was interrupted we can't perform any more requests during
		# this session because the camera may still be sending us data from the interrupt request
		#
		raise MtpProtocolException("Previous transfer interrupted - session in unknown state")

	dataReceivedSoFar = six.binary_type()
	dataDirection = getMtpOpDataDirection(mtpOp)

	#
	# send the MTP op command request
	#
	txTransactionId = next(generateTransactionId) # transaction ID, increments by 1 for each transaction
	theCmdReq = struct.pack('<IIHI', MTP_TCPIP_PAYLOAD_ID_CmdReq, mtpDataDirToCmdReqDataDirectionCode[dataDirection], mtpOp, txTransactionId) + cmdArgsPacked
	applog_d("execMtpOp: {:s} - CmdReq payload:".format(getMtpOpDesc(mtpOp)))
	txdata(s, theCmdReq)
	
	#
	# if this MTP op has Host -> Camera data ,send it now
	#
	if dataDirection == MTP_DATA_DIRECTION_HOST_TO_CAMERA:
		applog_d("execMtpOp: Sending MTP_TCPIP_PAYLOAD_ID_DataStart")
		txdata(s, struct.pack('<IIII', MTP_TCPIP_PAYLOAD_ID_DataStart, txTransactionId, len(dataToSend), 0))
		applog_d("execMtpOp: Sending MTP_TCPIP_PAYLOAD_ID_DataPayloadLast:")
		txdata(s, struct.pack('<II', MTP_TCPIP_PAYLOAD_ID_DataPayloadLast, txTransactionId) + dataToSend)
			
	#
	# loop, processing inbound data payloads (MTP_DATA_DIRECTION_CAMERA_TO_HOST) and
	# the final cmd-response payload
	#
	totalDataTransferSizeBytesExpectedAcrossAllPayloads = 0
	while True:
	
		try:
	
			data = rxPayload(s, lambda totalBytesReceivedThisPayload : execMtpOp_rxPayloadProgressFunc(totalBytesReceivedThisPayload, 
				rxTxProgressFunc, len(dataReceivedSoFar), totalDataTransferSizeBytesExpectedAcrossAllPayloads))
			(payloadId,) = struct.unpack('<I', data[0:4])
			
			if payloadId == MTP_TCPIP_PAYLOAD_ID_DataStart:
			
				if dataDirection != MTP_DATA_DIRECTION_CAMERA_TO_HOST:
					raise MtpProtocolException("Camera Protocol Error: {:s}: Received unexpected MTP_TCPIP_PAYLOAD_ID_DataStart for non-inbound transfer".\
						format(getMtpOpDesc(mtpOp)))
			
				# process MTP_TCPIP_PAYLOAD_ID_DataStart
				(rxTransactionId,) = struct.unpack('<I', data[4:8])
				if rxTransactionId != txTransactionId:
					raise MtpProtocolException("Camera Protocol Error: {:s}: Incorrect transaction ID for MTP_TCPIP_PAYLOAD_ID_DataStart (exp={:08x}, got={:08x})".\
						format(getMtpOpDesc(mtpOp), txTransactionId, rxTransactionId))
				(totalDataTransferSizeBytesExpectedAcrossAllPayloads,) = struct.unpack('<I', data[8:12])				
				
				# debug dump of DataStart payload
				if isDebugLog():
					applog_d("execMtpOp: {:s} - DataStart payload [expected data bytes is 0x{:x}]".format(getMtpOpDesc(mtpOp), totalDataTransferSizeBytesExpectedAcrossAllPayloads))
					applog_d(strutil.hexdump(data))	

			elif payloadId == MTP_TCPIP_PAYLOAD_ID_DataPayload or payloadId == MTP_TCPIP_PAYLOAD_ID_DataPayloadLast:

				if isDebugLog():
					if mtpOp == MTP_OP_GetObject or mtpOp == MTP_OP_GetPartialObject or mtpOp == MTP_OP_GetLargeThumb or mtpOp == MTP_OP_GetThumb:
						maxBytesToDump = 64
					else:
						maxBytesToDump = 4096
					applog_d("execMtpOp: {:s} - Data payload [ID {:x}] (0x{:08x} bytes):".format(getMtpOpDesc(mtpOp), payloadId, len(data)))
					applog_d(strutil.hexdump(data[:min(len(data), maxBytesToDump)]))

				(rxTransactionId,) = struct.unpack('<I', data[4:8])
				if rxTransactionId != txTransactionId:
					raise MtpProtocolException("Camera Protocol Error: {:s}: Incorrect transaction ID for data payload (exp={:08x}, got={:08x})".format(\
						getMtpOpDesc(mtpOp), txTransactionId, rxTransactionId))				
				
				dataReceivedSoFar += data[8:]				
					
			elif payloadId == MTP_TCPIP_PAYLOAD_ID_CmdResponse:
					
				(mtpRespCode, rxTransactionId) = struct.unpack('<HI', data[4:10])
				if rxTransactionId != txTransactionId:
					raise MtpProtocolException("Camera Protocol Error: {:s}: Incorrect transaction ID for MTP_TCPIP_PAYLOAD_ID_CmdResponse (exp={:08x}, got={:08x})".\
						format(getMtpOpDesc(mtpOp), txTransactionId, rxTransactionId))

				if len(data)>=14:				
					(mtpResponseParameter,)=struct.unpack('<I', data[10:14])
				else:
					mtpResponseParameter = None
					
				# debug dump of CmdResonse payload
				if isDebugLog():
					applog_d("execMtpOp: {:s} - CmdResponse payload (resp=\"{:s}\"):".format(getMtpOpDesc(mtpOp), getMtpRespDesc(mtpRespCode)))
					applog_d(strutil.hexdump(data))
				
				if mtpRespCode != MTP_RESP_Ok:
					raise MtpOpExecFailureException(mtpRespCode, "Camera Command Failed: {:s}, Error: {:s}".format(getMtpOpDesc(mtpOp), getMtpRespDesc(mtpRespCode)))

				#
				# note we don't check for underrruns until after veryfing result is MTP_RESP_Ok. For non-successful
				# completions we want to report that high-level error code rather than an underrun, since an underrun
				# is theoretically possible if the camera decided to stop transferrring data and send a response frame
				#
				if totalDataTransferSizeBytesExpectedAcrossAllPayloads and len(dataReceivedSoFar) < totalDataTransferSizeBytesExpectedAcrossAllPayloads:
					raise MtpProtocolException("Camera Protocol Error: {:s}: Data underrun (exp=0x{:08x}, got=0x{:08x})".format(\
						getMtpOpDesc(mtpOp), totalDataTransferSizeBytesExpectedAcrossAllPayloads, len(dataReceivedSoFar[8:])))											
					
				return MtpTcpCmdResult(mtpRespCode, mtpResponseParameter, dataReceivedSoFar)
				
			else:
				if isDebugLog():
					applog_d("Unrecognized payload ID 0x{:x}. Data received:".format(payloadId))
					applog_d(strutil.hexdump(data))				
				raise MtpProtocolException("Camera Networking Error: {:s}: Unrecognized payload ID (0x{:08x})".format(getMtpOpDesc(mtpOp), payloadId))

		except (socket.error) as e:
				# we received at least some data payload data before the error
				if g_PartialRxDataPayloadData:
					data = g_PartialRxDataPayloadData
					if isDebugLog():
						applog_d("execMtpOp: {:s} - Partial payload after error (0x{:08x} bytes):".format(getMtpOpDesc(mtpOp), len(data)))
						applog_d(strutil.hexdump(data[:min(len(data),1024)]))
					(rxTransactionId,) = struct.unpack('<I', data[4:8])
					if rxTransactionId != txTransactionId:
						raise MtpProtocolException("Camera Networking Error: {:s}: Incorrect transaction ID for data payload (exp={:08x}, got={:08x})".format(\
							getMtpOpDesc(mtpOp), txTransactionId, rxTransactionId))								
					dataReceivedSoFar += data[8:]
					bytesReceivedLastPayload = len(data[8:])
					lastPayloadExpectedSize = g_PartialRxDataPayloadData_SizeIndicated - 8
				else:
					bytesReceivedLastPayload = 0
					lastPayloadExpectedSize = 0
				
				raise MtpOpExecFailureException(MTP_RESP_COMMUNICATION_ERROR, \
					"{:s}: Socket error, partial data received - 0x{:x} of 0x{:x} bytes for specific payload, 0x{:x} of 0x{:x} of total data bytes expected. Error: {:s}".\
						format(getMtpOpDesc(mtpOp), bytesReceivedLastPayload, lastPayloadExpectedSize, len(dataReceivedSoFar), totalDataTransferSizeBytesExpectedAcrossAllPayloads, str(e)),
						dataReceivedSoFar, totalDataTransferSizeBytesExpectedAcrossAllPayloads)										

		except KeyboardInterrupt as e: # <ctrl-c> pressed			
			gTransferInterruptedBySIGINT = True
			applog_d("gTransferInterruptedBySIGINT set")
			raise
						
			
#
# sends host introduction to camera (not sure what the spec calls this since it's not publicly documented.
# this is the first operation performed after opening a TCP/IP socket with the camera. the camera returns
# the session identifier that we're to use as the session ID when performing a later MTP_OP_OpenSession
#
def sendInitCmdReq(s, guidHighLowTuple, hostNameStr, hostVerInt):
	applog_d("sendInitCmdReq(): Sending MTP_TCPIP_REQ_INIT_CMD_REQ")
	(guidHigh, guidLow) = guidHighLowTuple
	cmdtype=struct.pack('<I', MTP_TCPIP_REQ_INIT_CMD_REQ)
	guid = struct.pack('<QQ', guidHigh, guidLow) 
	hostNameUtf16ByteArray = strutil.stringToUtf16ByteArray(hostNameStr, True)
	try:
		rxdata = txrxdata(s, cmdtype + guid + hostNameUtf16ByteArray + struct.pack('<I', hostVerInt))
		if isDebugLog():
			applog_d("sendInitCmdReq() response:")
			applog_d(strutil.hexdump(rxdata))
		(wordResponse,) = struct.unpack('<I',rxdata[:4])
		if wordResponse == 0x2 and len(rxdata) >= 8:	# make sure first 32-bit word is equal to a value of 0x2 ("ACK") and has 4-byte session ID after
			return rxdata[4:]
		else:
			raise MtpProtocolException(\
				"\nThe camera is rejecting the unique identifier (GUID) that airnef is\n"\
				"presenting. Some cameras including most Canon's associate a given Wifi\n"\
				"configuration to a particular remote application's GUID. If you have used a\n"\
				"remote application other than airnef with this camera (or a different\n"\
				"version of airnef) then you may need to re-create the WiFi configuration\n"\
				"on the camera to allow it to be associated with airnef's GUID.")
	except socket.error as error:
		#
		# in my testing I found situations where my J4 enter a state where it would accept the TCP/IP
		# connection but then not respond to any MTP discovery/command requests. the only way to
		# recover from this condition was to cycle the WiFi enable on the camera or cycle its power
		#
		applog_e("\nCamera is accepting connections but failing to negotiate a session. You may\nneed to turn the camera's WiFi off and of or cycle the camera's power to\nrecover. You can leave airnefcmd running while doing this.")
		sys.exit(errno.ETIMEDOUT)

#
# analog of sendInitCmdReq() but for the TCP/IP sockets used for events and
# no session identifier is returned
#
def sendInitEvents(s, sessionId):
	applog_d("sendInitEvents(): Sending MTP_TCPIP_REQ_INIT_EVENTS")
	cmdtype = struct.pack('<II', MTP_TCPIP_REQ_INIT_EVENTS, sessionId)
	try:
		rxdata = txrxdata(s, cmdtype)
		if isDebugLog():
			applog_d("sendInitEvents() response:")
			applog_d(strutil.hexdump(rxdata))
		(wordResponse,) = struct.unpack('<I',rxdata[:4])
		if wordResponse != 0x4:	# make sure first 32-bit word is equal to a value of 0x4 ("ACK")
			raise MtpProtocolException("sendInitEvents(): Bad response/ACK - expected 0x04, got 0x{:x}".format(wordResponse))
	except socket.error as error:
		raise
		
#
# sends a probe request. this should be done on the events socket
#		
def sendProbeRequest(s):
	applog_d("sendProbeRequest(): Sending probe request")
	cmdtype = struct.pack('<I', MTP_TCPIP_REQ_PROBE)
	try:
		rxdata = txrxdata(s, cmdtype)
		if isDebugLog():
			applog_d("sendProbeRequest() response:")
			applog_d(strutil.hexdump(rxdata))
		(wordResponse,) = struct.unpack('<I',rxdata[:4])
		if wordResponse != 0xe:	# make sure first 32-bit word is equal to a value of 0xe ("probe response")
			raise MtpProtocolException("sendProbeRequest(): Bad response/ACK - expected 0x0e, got 0x{:x}".format(wordResponse))
	except socket.error as error:
		raise		

		
#
# opens TCP/IP socket to camera. this is the first step in communication
#		
def openConnection(ipAddrStr, verbose, connectionTimeoutSecs=SOCKET_TIMEOUT_CONNECT_SECS_DEFAULT, readWriteTimeoutSecs=SOCKET_TIMEOUT_READS_WRITES_DEFAULT):
	port = 15740
	applog_d("openConnection(): Attempting connection to {:s}:{:d}".format(ipAddrStr, port))
	s = None
	consoleWriteLine("Attempting to establish camera connection at {:s}:{:d} ".format(ipAddrStr, port))
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(connectionTimeoutSecs)
		s.connect((ipAddrStr,port))
	except (socket.timeout, socket.error) as error:
		consoleClearLine()
		if s:
			s.close()
		connectErrMsg = ">> Connection Failed <<\n\n"
		if type(error) == socket.timeout:
			connectErrMsg += \
				"There was no response at {:s}. Please confirm that your camera's\n"	\
				"Wifi is enabled and that you have specified the correct IP address."	\
				.format(ipAddrStr)
		else:
			if error.errno == errno.ECONNREFUSED:
				connectErrMsg += \
					"A device at {:s} responded but the connection was refused.\n"					\
					"This is likely because you are connected to a normal Wifi network instead\n" 	\
					"of your camera's network. Please confirm that your camera's Wifi is enabled\n"	\
					"and that your computer is connected to its network."							\
					.format(ipAddrStr)
			else:
				connectErrMsg += "Could not open socket: {:s}".format(str(error))
		raise MtpConnectionFailureException(connectErrMsg)
	# connection successful
	consoleClearLine()
	if (verbose):
		applog_i("Connection established to {:s}:{:d}".format(ipAddrStr, port))
	s.settimeout(readWriteTimeoutSecs)						# set per-call timeout on socket, most useful for our future recv() calls
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)	# for performance
	return s
