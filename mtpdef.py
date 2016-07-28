#!/usr/bin/env python

#
#############################################################################
#
# mtpdef - Media Transfer Protocol definitions
# Copyright (C) 2015, testcams.com
#
# This module is licensed under GPL v3: http://www.gnu.org/licenses/gpl-3.0.html
#
#############################################################################
#

from __future__ import print_function
from __future__ import division
from collections import namedtuple

#
# MTP Operation Codes
#
MTP_OP_GetDeviceInfo 			= 0x1001
MTP_OP_OpenSession 				= 0x1002
MTP_OP_CloseSession				= 0x1003
MTP_OP_GetStorageIDs			= 0x1004
MTP_OP_GetStorageInfo			= 0x1005
MTP_OP_GetNumObjects			= 0x1006
MTP_OP_GetObjectHandles			= 0x1007
MTP_OP_GetObjectInfo			= 0x1008
MTP_OP_GetObject				= 0x1009
MTP_OP_GetThumb					= 0x100a
MTP_OP_DeleteObject				= 0x100b
MTP_OP_SendObjectInfo			= 0x100c
MTP_OP_SendObject				= 0x100d
MTP_OP_InitiateCapture			= 0x100e
MTP_OP_FormatStore				= 0x100f
MTP_OP_PowerDown				= 0x1013 # from Microsoft MTP Enhanced document, not sure any devices support it
MTP_OP_GetDevicePropDesc		= 0x1014
MTP_OP_GetDevicePropValue		= 0x1015
MTP_OP_SetDevicePropValue		= 0x1016
MTP_OP_GetPartialObject			= 0x101b
MTP_OP_InitiateCaptureRecInSdram =0x90c0
MTP_OP_AfDrive					= 0x90c1
MTP_OP_ChangeCameraMode			= 0x90c2
MTP_OP_DeleteImagesInSdram		= 0x90c3
MTP_OP_GetLargeThumb			= 0x90c4
MTP_OP_NkonGetEvent				= 0x90c7
MTP_OP_DeviceReady				= 0x90c8
MTP_OP_SetPreWbData				= 0x90c9
MTP_OP_GetVendorPropCodes		= 0x90ca
MTP_OP_AfAndCaptureRecInSdram 	= 0x90cb
MTP_OP_GetPicCtrlData			= 0x90cc
MTP_OP_SetPicCtrlData			= 0x90cd
MTP_OP_DeleteCustomPicCtrl		= 0x90ce
MTP_OP_GetPicCtrlCapability		= 0x90cf
MTP_OP_StartLiveView			= 0x9201
MTP_OP_EndLiveView				= 0x9202
MTP_OP_GetLiveViewImage			= 0x9203
MTP_OP_MfDrive					= 0x9204
MTP_OP_ChangeAfArea				= 0x9205
MTP_OP_AfDriveCancel			= 0x9206
MTP_OP_InitiateCatureRecInMedia = 0x9207
MTP_OP_GetVendorStorageIDs		= 0x9209
MTP_OP_StartMovieRecInCard		= 0x920a
MTP_OP_EndMovieRec				= 0x920b
MTP_OP_TerminateCapture			= 0x920c
MTP_OP_GetPartialOjectHighSpeed = 0x9400
MTP_OP_StartSpotWb				= 0x9402
MTP_OP_EndSpotWb				= 0x9403
MTP_OP_ChangeSpotWbArea			= 0x9404
MTP_OP_MeasureSpotWb			= 0x9405
MTP_OP_EndSpotWbResultDisp  	= 0x9406
MTP_OP_SetTransferListLock  	= 0x9407
MTP_OP_GetTransferList			= 0x9408
MTP_OP_NotifyFileAcquisitionStart =0x9409
MTP_OP_NotifyFileAcquisitionEnd = 0x940a
MTP_OP_GetSpecificSizeObject	= 0x940b
MTP_OP_CancelImagesInSdram		= 0x940c
MTP_OP_GetPicCtrlDataEx			= 0x940d
MTP_OP_SetPicCtrlDataEx			= 0x940e
MTP_OP_DeleteMovieCustomPicCtrl = 0x940f
MTP_OP_GetMoviePicCtrlCapability= 0x9410
MTP_OP_GetObjectProprsSupported = 0x9801
MTP_OP_GetObjectPropDesc		= 0x9802
MTP_OP_GetObjectPropValue		= 0x9803
MTP_OP_GetObjectPropList		= 0x9805
# Canon-unique codes
MTP_OP_Canon_GetDevicePropValue = 0x9127
MTP_OP_Canon_SetDevicePropValue = 0x9110
# Sony-unique codes
MTP_OP_Sony_Set_Request			= 0x9280	# unclear exactly what these are but they appear to be wrappers for Sony-unique commands contained within
MTP_OP_Sony_Get_Request			= 0x9281	# evey 'set' request must be followed by a 'get' request, otherwise camera returns busy for subsequent set requests

MtpOpDescDictionary = {\
	MTP_OP_GetDeviceInfo 			: 'MTP_OP_GetDeviceInfo',
	MTP_OP_OpenSession 				: 'MTP_OP_OpenSession',
	MTP_OP_CloseSession				: 'MTP_OP_CloseSession',
	MTP_OP_GetStorageIDs			: 'MTP_OP_GetStorageIDs',
	MTP_OP_GetStorageInfo			: 'MTP_OP_GetStorageInfo',
	MTP_OP_GetNumObjects			: 'MTP_OP_GetNumObjects',
	MTP_OP_GetObjectHandles			: 'MTP_OP_GetObjectHandles',
	MTP_OP_GetObjectInfo			: 'MTP_OP_GetObjectInfo',
	MTP_OP_GetObject				: 'MTP_OP_GetObject',
	MTP_OP_GetThumb					: 'MTP_OP_GetThumb',
	MTP_OP_DeleteObject				: 'MTP_OP_DeleteObject',
	MTP_OP_SendObjectInfo			: 'MTP_OP_SendObjectInfo',
	MTP_OP_SendObject				: 'MTP_OP_SendObjectv',
	MTP_OP_InitiateCapture			: 'MTP_OP_InitiateCapture',
	MTP_OP_FormatStore				: 'MTP_OP_FormatStore',
	MTP_OP_PowerDown				: 'MTP_OP_PowerDown',
	MTP_OP_GetDevicePropDesc		: 'MTP_OP_GetDevicePropDesc',
	MTP_OP_GetDevicePropValue		: 'MTP_OP_GetDevicePropValue',
	MTP_OP_SetDevicePropValue		: 'MTP_OP_SetDevicePropValue',
	MTP_OP_GetPartialObject			: 'MTP_OP_GetPartialObject',
	MTP_OP_InitiateCaptureRecInSdram : 'MTP_OP_InitiateCaptureRecInSdram',
	MTP_OP_AfDrive					: 'MTP_OP_AfDrive',
	MTP_OP_ChangeCameraMode			: 'MTP_OP_ChangeCameraMode',
	MTP_OP_DeleteImagesInSdram		: 'MTP_OP_DeleteImagesInSdram',
	MTP_OP_GetLargeThumb			: 'MTP_OP_GetLargeThumb',
	MTP_OP_NkonGetEvent				: 'MTP_OP_NkonGetEvent',
	MTP_OP_DeviceReady				: 'MTP_OP_DeviceReady',
	MTP_OP_SetPreWbData				: 'MTP_OP_SetPreWbData',
	MTP_OP_GetVendorPropCodes		: 'MTP_OP_GetVendorPropCodes',
	MTP_OP_AfAndCaptureRecInSdram 	: 'MTP_OP_AfAndCaptureRecInSdram',
	MTP_OP_GetPicCtrlData			: 'MTP_OP_GetPicCtrlData',
	MTP_OP_SetPicCtrlData			: 'MTP_OP_SetPicCtrlData',
	MTP_OP_DeleteCustomPicCtrl		: 'MTP_OP_DeleteCustomPicCtrl',
	MTP_OP_GetPicCtrlCapability		: 'MTP_OP_GetPicCtrlCapability',
	MTP_OP_StartLiveView			: 'MTP_OP_StartLiveView',
	MTP_OP_EndLiveView				: 'MTP_OP_EndLiveView',
	MTP_OP_GetLiveViewImage			: 'MTP_OP_GetLiveViewImage',
	MTP_OP_MfDrive					: 'MTP_OP_MfDrive',
	MTP_OP_ChangeAfArea				: 'MTP_OP_ChangeAfArea',
	MTP_OP_AfDriveCancel			: 'MTP_OP_AfDriveCancel',
	MTP_OP_InitiateCatureRecInMedia : 'MTP_OP_InitiateCatureRecInMedia',
	MTP_OP_GetVendorStorageIDs		: 'MTP_OP_GetVendorStorageIDs',
	MTP_OP_StartMovieRecInCard		: 'MTP_OP_StartMovieRecInCard',
	MTP_OP_EndMovieRec				: 'MTP_OP_EndMovieRec',
	MTP_OP_TerminateCapture			: 'MTP_OP_TerminateCapture',
	MTP_OP_GetPartialOjectHighSpeed : 'MTP_OP_GetPartialOjectHighSpeed',
	MTP_OP_StartSpotWb				: 'MTP_OP_StartSpotWb',
	MTP_OP_EndSpotWb				: 'MTP_OP_EndSpotWb',
	MTP_OP_ChangeSpotWbArea			: 'MTP_OP_ChangeSpotWbArea',
	MTP_OP_MeasureSpotWb			: 'MTP_OP_MeasureSpotWb',
	MTP_OP_EndSpotWbResultDisp  	: 'MTP_OP_EndSpotWbResultDisp',
	MTP_OP_SetTransferListLock  	: 'MTP_OP_SetTransferListLock',
	MTP_OP_GetTransferList			: 'MTP_OP_GetTransferList',
	MTP_OP_NotifyFileAcquisitionStart : 'MTP_OP_NotifyFileAcquisitionStart',
	MTP_OP_NotifyFileAcquisitionEnd : 'MTP_OP_NotifyFileAcquisitionEnd',
	MTP_OP_GetSpecificSizeObject	: 'MTP_OP_GetSpecificSizeObject',
	MTP_OP_CancelImagesInSdram		: 'MTP_OP_CancelImagesInSdram',
	MTP_OP_GetPicCtrlDataEx			: 'MTP_OP_GetPicCtrlDataEx',
	MTP_OP_SetPicCtrlDataEx			: 'MTP_OP_SetPicCtrlDataEx',
	MTP_OP_DeleteMovieCustomPicCtrl : 'MTP_OP_DeleteMovieCustomPicCtrl',
	MTP_OP_GetMoviePicCtrlCapability: 'MTP_OP_GetMoviePicCtrlCapability',
	MTP_OP_GetObjectProprsSupported : 'MTP_OP_GetObjectProprsSupported',
	MTP_OP_GetObjectPropDesc		: 'MTP_OP_GetObjectPropDesc',
	MTP_OP_GetObjectPropValue		: 'MTP_OP_GetObjectPropValue',
	MTP_OP_GetObjectPropList		: 'MTP_OP_GetObjectPropList',
	MTP_OP_Canon_SetDevicePropValue : 'MTP_OP_Canon_SetDevicePropValue',
	MTP_OP_Canon_GetDevicePropValue : 'MTP_OP_Canon_GetDevicePropValue',
	MTP_OP_Sony_Set_Request			: 'MTP_OP_Sony_Set_Request',	
	MTP_OP_Sony_Get_Request			: 'MTP_OP_Sony_Get_Request'
}
def getMtpOpDesc(mtpOp):
	if mtpOp in MtpOpDescDictionary:
		return "{:s}".format(MtpOpDescDictionary[mtpOp])
	else:
		return "Unknown Op Code (0x{:04x})".format(mtpOp)

#
# not in the spec, but here are constants for the possible
# data directions of MTP commands, plus a dictonary for a
# quick lookup for the data direction for each OP
#		
MTP_DATA_DIRECTION_NONE				= 0
MTP_DATA_DIRECTION_CAMERA_TO_HOST	= 1
MTP_DATA_DIRECTION_HOST_TO_CAMERA	= 2
		
MtpOpDataDirections = {\
	MTP_OP_GetDeviceInfo 			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_OpenSession 				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_CloseSession				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetStorageIDs			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetStorageInfo			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetNumObjects			: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetObjectHandles			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetObjectInfo			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetObject				: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetThumb					: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_DeleteObject				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_SendObjectInfo			: MTP_DATA_DIRECTION_HOST_TO_CAMERA,
	MTP_OP_SendObject				: MTP_DATA_DIRECTION_HOST_TO_CAMERA,
	MTP_OP_InitiateCapture			: MTP_DATA_DIRECTION_NONE,
	MTP_OP_FormatStore				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_PowerDown				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetDevicePropDesc		: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetDevicePropValue		: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_SetDevicePropValue		: MTP_DATA_DIRECTION_HOST_TO_CAMERA,
	MTP_OP_GetPartialObject			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_InitiateCaptureRecInSdram : MTP_DATA_DIRECTION_NONE,
	MTP_OP_AfDrive					: MTP_DATA_DIRECTION_NONE,
	MTP_OP_ChangeCameraMode			: MTP_DATA_DIRECTION_NONE,
	MTP_OP_DeleteImagesInSdram		: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetLargeThumb			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_NkonGetEvent				: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_DeviceReady				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_SetPreWbData				: MTP_DATA_DIRECTION_HOST_TO_CAMERA,
	MTP_OP_GetVendorPropCodes		: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_AfAndCaptureRecInSdram 	: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetPicCtrlData			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_SetPicCtrlData			: MTP_DATA_DIRECTION_HOST_TO_CAMERA,
	MTP_OP_DeleteCustomPicCtrl		: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetPicCtrlCapability		: MTP_DATA_DIRECTION_NONE,
	MTP_OP_StartLiveView			: MTP_DATA_DIRECTION_NONE,
	MTP_OP_EndLiveView				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetLiveViewImage			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_MfDrive					: MTP_DATA_DIRECTION_NONE,
	MTP_OP_ChangeAfArea				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_AfDriveCancel			: MTP_DATA_DIRECTION_NONE,
	MTP_OP_InitiateCatureRecInMedia : MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetVendorStorageIDs		: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_StartMovieRecInCard		: MTP_DATA_DIRECTION_NONE,
	MTP_OP_EndMovieRec				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_TerminateCapture			: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetPartialOjectHighSpeed : MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_StartSpotWb				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_EndSpotWb				: MTP_DATA_DIRECTION_NONE,
	MTP_OP_ChangeSpotWbArea			: MTP_DATA_DIRECTION_NONE,
	MTP_OP_MeasureSpotWb			: MTP_DATA_DIRECTION_NONE,
	MTP_OP_EndSpotWbResultDisp  	: MTP_DATA_DIRECTION_NONE,
	MTP_OP_SetTransferListLock  	: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetTransferList			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_NotifyFileAcquisitionStart : MTP_DATA_DIRECTION_NONE,
	MTP_OP_NotifyFileAcquisitionEnd : MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetSpecificSizeObject	: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_CancelImagesInSdram		: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetPicCtrlDataEx			: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_SetPicCtrlDataEx			: MTP_DATA_DIRECTION_HOST_TO_CAMERA,
	MTP_OP_DeleteMovieCustomPicCtrl : MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetMoviePicCtrlCapability: MTP_DATA_DIRECTION_NONE,
	MTP_OP_GetObjectProprsSupported : MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetObjectPropDesc		: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetObjectPropValue		: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_GetObjectPropList		: MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_Canon_SetDevicePropValue : MTP_DATA_DIRECTION_HOST_TO_CAMERA,
	MTP_OP_Canon_GetDevicePropValue : MTP_DATA_DIRECTION_CAMERA_TO_HOST,
	MTP_OP_Sony_Set_Request			: MTP_DATA_DIRECTION_HOST_TO_CAMERA,
	MTP_OP_Sony_Get_Request			: MTP_DATA_DIRECTION_CAMERA_TO_HOST
}
def getMtpOpDataDirection(mtpOp):
	if mtpOp in MtpOpDataDirections:
		return MtpOpDataDirections[mtpOp]
	else:
		raise AssertionError("getMtpOpDataDirection called with an op 0x{:x} that is not in MtpOpDataDirections!".format(mtpOp))


#
# MTP Response Codes
#
MTP_RESP_Ok										= 0x2001
MTP_RESP_GeneralError							= 0x2002
MTP_RESP_SessionNotOpen							= 0x2003
MTP_RESP_InvalidTransactionId					= 0x2004
MTP_RESP_OperationNotSupported					= 0x2005
MTP_RESP_ParameterNotSupported					= 0x2006
MTP_RESP_IncompleteTransfer						= 0x2007
MTP_RESP_InvalidStorageID						= 0x2008
MTP_RESP_InvalidObjectHandle					= 0x2009
MTP_RESP_DevicePropNotSupported					= 0x200a
MTP_RESP_InvalidObjectFormatCode				= 0x200b
MTP_RESP_StoreFull								= 0x200c
MTP_RESP_ObjectWriteProtect						= 0x200d
MTP_RESP_StoreReadOnly							= 0x200e
MTP_RESP_AccessDenied							= 0x200f
MTP_RESP_NoThumbnailPresent						= 0x2010
MTP_RESP_PartialDeletion						= 0x2012
MTP_RESP_StoreNotAvailable						= 0x2013
MTP_RESP_SpecificiationByFormatUnsupported		= 0x2014
MTP_RESP_NoValidObjectInfo						= 0x2015
MTP_RESP_DeviceBusy								= 0x2019
MTP_RESP_InvalidParentObject					= 0x201a
MTP_RESP_InvalidDevicePropFormat				= 0x201b
MTP_RESP_InvalidDevicePropValue					= 0x201c
MTP_RESP_InvalidParameter						= 0x201d
MTP_RESP_SessionAlreadyOpen						= 0x201e
MTP_RESP_SpecificationOfDestinationUnsupported	= 0x2020
MTP_RESP_HardwareError							= 0xa001
MTP_RESP_OutOfFocus								= 0xa002
MTP_RESP_ChangeCameraModeFailed					= 0xa003
MTP_RESP_InvalidStatus							= 0xa004
MTP_RESP_WbPresentError							= 0xa006
MTP_RESP_DustReferenceError						= 0xa007
MTP_RESP_ShutterSpeedBulb						= 0xa008
MTP_RESP_MirrorUpSequence						= 0xa009
MTP_RESP_CameraModeNotAdjustFnumber				= 0xa00a
MTP_RESP_NotLiveView							= 0xa00b
MTP_RESP_MfDriveStepEnd							= 0xa00c
MTP_RESP_MfDriveStepInsufficiency				= 0xa00e
MTP_RESP_StoreError								= 0xa021
MTP_RESP_StoreUnformatted						= 0xa022
MTP_RESP_BulbReleaseBusy						= 0xa200
MTP_RESP_ShutterSpeedTime						= 0xa204
MTP_RESP_NoTransferList							= 0xa205
MTP_RESP_NoJpegPresent							= 0xa206
MTP_RESP_InvalidObjectPropCode					= 0xa801
MTP_RESP_InvalidObjectPropFormat				= 0xa802
MTP_RESP_COMMUNICATION_ERROR					= 0xfffe	# fake response I use internally to convey error in transmitting/receiving MTP request

MtpRespDescDictionary = {\
	MTP_RESP_Ok : 'MTP_RESP_Ok',
	MTP_RESP_GeneralError : 'MTP_RESP_GeneralError',
	MTP_RESP_SessionNotOpen : 'MTP_RESP_SessionNotOpen',
	MTP_RESP_InvalidTransactionId : 'MTP_RESP_InvalidTransactionId',
	MTP_RESP_OperationNotSupported : 'MTP_RESP_OperationNotSupported',
	MTP_RESP_ParameterNotSupported : 'MTP_RESP_ParameterNotSupported',
	MTP_RESP_IncompleteTransfer : 'MTP_RESP_IncompleteTransfer',
	MTP_RESP_InvalidStorageID : 'MTP_RESP_InvalidStorageID',
	MTP_RESP_InvalidObjectHandle : 'MTP_RESP_InvalidObjectHandle',
	MTP_RESP_DevicePropNotSupported : 'MTP_RESP_DevicePropNotSupported',
	MTP_RESP_InvalidObjectFormatCode : 'MTP_RESP_InvalidObjectFormatCode',
	MTP_RESP_StoreFull : 'MTP_RESP_StoreFull',
	MTP_RESP_ObjectWriteProtect : 'MTP_RESP_ObjectWriteProtect',
	MTP_RESP_StoreReadOnly : 'MTP_RESP_StoreReadOnly',
	MTP_RESP_AccessDenied : 'MTP_RESP_AccessDenied',
	MTP_RESP_NoThumbnailPresent : 'MTP_RESP_NoThumbnailPresent',
	MTP_RESP_PartialDeletion : 'MTP_RESP_PartialDeletion',
	MTP_RESP_StoreNotAvailable : 'MTP_RESP_StoreNotAvailable',
	MTP_RESP_SpecificiationByFormatUnsupported : 'MTP_RESP_SpecificiationByFormatUnsupported',
	MTP_RESP_NoValidObjectInfo : 'MTP_RESP_NoValidObjectInfo',
	MTP_RESP_DeviceBusy : 'MTP_RESP_DeviceBusy',
	MTP_RESP_InvalidParentObject : 'MTP_RESP_InvalidParentObject',
	MTP_RESP_InvalidDevicePropFormat : 'MTP_RESP_InvalidDevicePropFormat',
	MTP_RESP_InvalidDevicePropValue : 'MTP_RESP_InvalidDevicePropValue',
	MTP_RESP_InvalidParameter : 'MTP_RESP_InvalidParameter',
	MTP_RESP_SessionAlreadyOpen : 'MTP_RESP_SessionAlreadyOpen',
	MTP_RESP_SpecificationOfDestinationUnsupported : 'MTP_RESP_SpecificationOfDestinationUnsupported',
	MTP_RESP_HardwareError : 'MTP_RESP_HardwareError',
	MTP_RESP_OutOfFocus : 'MTP_RESP_OutOfFocus',
	MTP_RESP_ChangeCameraModeFailed : 'MTP_RESP_ChangeCameraModeFailed',
	MTP_RESP_InvalidStatus : 'MTP_RESP_InvalidStatus',
	MTP_RESP_WbPresentError : 'MTP_RESP_WbPresentError',
	MTP_RESP_DustReferenceError : 'MTP_RESP_DustReferenceError',
	MTP_RESP_ShutterSpeedBulb : 'MTP_RESP_ShutterSpeedBulb',
	MTP_RESP_MirrorUpSequence : 'MTP_RESP_MirrorUpSequence',
	MTP_RESP_CameraModeNotAdjustFnumber : 'MTP_RESP_CameraModeNotAdjustFnumber',
	MTP_RESP_NotLiveView : 'MTP_RESP_NotLiveView',
	MTP_RESP_MfDriveStepEnd : 'MTP_RESP_MfDriveStepEnd',
	MTP_RESP_MfDriveStepInsufficiency : 'MTP_RESP_MfDriveStepInsufficiency',
	MTP_RESP_StoreError : 'MTP_RESP_StoreError',
	MTP_RESP_StoreUnformatted : 'MTP_RESP_StoreUnformatted',
	MTP_RESP_BulbReleaseBusy : 'MTP_RESP_BulbReleaseBusy',
	MTP_RESP_ShutterSpeedTime : 'MTP_RESP_ShutterSpeedTime',
	MTP_RESP_NoTransferList : 'MTP_RESP_NoTransferList',
	MTP_RESP_NoJpegPresent : 'MTP_RESP_NoJpegPresent',
	MTP_RESP_InvalidObjectPropCode : 'MTP_RESP_InvalidObjectPropCode',
	MTP_RESP_InvalidObjectPropFormat : 'MTP_RESP_InvalidObjectPropFormat',
	MTP_RESP_COMMUNICATION_ERROR : 'MTP_RESP_COMMUNICATION_ERROR'
}
def getMtpRespDesc(mtpResponseCode):
	if mtpResponseCode in MtpRespDescDictionary:
		return "{:s}".format(MtpRespDescDictionary[mtpResponseCode])
	else:
		return "Unknown Response Code (0x{:04x})".format(mtpResponseCode)

#
# MTP object format codes
#
MTP_OBJFORMAT_NONE				= 0x0000
MTP_OBJFORMAT_NEF_WithoutMtp	= 0x3000	# Nikon raw file
MTP_OBJFORMAT_Assocation		= 0x3001
MTP_OBJFORMAT_Script			= 0x3002
MTP_OBJFORMAT_DigitalPrintOrder	= 0x3006
MTP_OBJFORMAT_WAV				= 0x3008
MTP_OBJFORMAT_NEF_WithMtp		= 0x3800
MTP_OBJFORMAT_EXIF_or_JPEG		= 0x3801
MTP_OBJFORMAT_JFIF				= 0x3808
MTP_OBJFORMAT_MOV				= 0x300d
MTP_OBJFORMAT_TIFF				= 0x380d
MTP_OBJFORMAT_CR2				= 0xb103	# Canon raw file

MtpObjFormatDescDictionary = {\
	MTP_OBJFORMAT_NONE : 'MTP_OBJFORMAT_NONE',
	MTP_OBJFORMAT_NEF_WithoutMtp : 'MTP_OBJFORMAT_NEF_WithoutMtp',
	MTP_OBJFORMAT_Assocation : 'MTP_OBJFORMAT_Assocation',	
	MTP_OBJFORMAT_Script : 'MTP_OBJFORMAT_Script',
	MTP_OBJFORMAT_DigitalPrintOrder : 'MTP_OBJFORMAT_DigitalPrintOrder',	
	MTP_OBJFORMAT_WAV : 'MTP_OBJFORMAT_WAV',
	MTP_OBJFORMAT_NEF_WithMtp : 'MTP_OBJFORMAT_NEF_WithMtp',	
	MTP_OBJFORMAT_EXIF_or_JPEG : 'MTP_OBJFORMAT_EXIF_or_JPEG',
	MTP_OBJFORMAT_JFIF : 'MTP_OBJFORMAT_JFIF',	
	MTP_OBJFORMAT_MOV : 'MTP_OBJFORMAT_MOV',
	MTP_OBJFORMAT_TIFF : 'MTP_OBJFORMAT_TIFF',
	MTP_OBJFORMAT_CR2 : 'MTP_OBJFORMAT_CR2',
}
def getMtpObjFormatDesc(mtpObjFormat):
	if mtpObjFormat in MtpObjFormatDescDictionary:
		return "{:s} (0x{:04x})".format(MtpObjFormatDescDictionary[mtpObjFormat], mtpObjFormat)
	else:
		return "Unknown ObjFormat (0x{:04x})".format(mtpObjFormat)

#
# MTP storage IDs
#
MTP_STORAGEID_MainSlotEmptyOrUnavail	= 0x00010000
MTP_STORAGEID_MainSlotPopulated			= 0x00010001
MTP_STORAGEID_SubSlotEmptyOrUnavail		= 0x00020000
MTP_STORAGEID_SubSlotPopulated			= 0x00020001

MTP_STORAGEID_PresenceBit				= 0x00000001	# bit 0 is set if slot is populated
MTP_STORAGEID_ALL_CARDS					= 0xFFFFFFFF

MtpStorageIdDescDictionary = {\
	MTP_STORAGEID_MainSlotEmptyOrUnavail : 'MTP_STORAGEID_MainSlotEmptyOrUnavail',
	MTP_STORAGEID_MainSlotPopulated : 'MTP_STORAGEID_MainSlotPopulated',
	MTP_STORAGEID_SubSlotEmptyOrUnavail : 'MTP_STORAGEID_SubSlotEmptyOrUnavail',
	MTP_STORAGEID_SubSlotPopulated : 'MTP_STORAGEID_SubSlotPopulated'
}
def getMtpStorageIdDesc(mtpStorageId):
	if mtpStorageId in MtpStorageIdDescDictionary:
		return "{:s} (0x{:04x})".format(MtpStorageIdDescDictionary[mtpStorageId], mtpStorageId)
	else:
		return "Unknown StorageId (0x{:04x})".format(mtpStorageId)
	
#
# MTP object assocation types
#
MTP_OBJASSOC_GenericFolder				= 0x0001

MtpObjAssocDescDictionary = {\
	MTP_OBJASSOC_GenericFolder : 'MTP_OBJASSOC_GenericFolder'
}	
def getObjAssocDesc(assocType):
	if assocType in MtpObjAssocDescDictionary:
		return "{:s} (0x{:04x})".format(MtpObjAssocDescDictionary[assocType], assocType)
	else:
		return "No Association or Unknown (0x{:04x})".format(assocType)

#
# MTP Event Codes
#
MTP_EVENT_CancelTransaction				= 0x4001
MTP_EVENT_ObjectAdded					= 0x4002
MTP_EVENT_ObjectRemoved					= 0x4003
MTP_EVENT_StoreAdded					= 0x4004
MTP_EVENT_StoreRemoved					= 0x4005
MTP_EVENT_DevicePropChanged				= 0x4006
MTP_EVENT_ObjectInfoChanged				= 0x4007
MTP_EVENT_DeviceInfoChanged				= 0x4008
MTP_EVENT_RequestObjectTransfer			= 0x4009
MTP_EVENT_StoreFull						= 0x400a
MTP_EVENT_StorageInfoChanged			= 0x400c
MTP_EVENT_CaptureComplete				= 0x400d
MTP_EVENT_ObjectAddedInSdram			= 0xc101
MTP_EVENT_CaptureCompleteRecInSdram		= 0xc102
MTP_EVENT_RecordingInterrupted			= 0xc105

MtpEventDescDictionary = {\
	MTP_EVENT_CancelTransaction : 'MTP_EVENT_CancelTransaction',
	MTP_EVENT_ObjectAdded : 'MTP_EVENT_ObjectAdded',
	MTP_EVENT_ObjectRemoved : '	MTP_EVENT_ObjectRemoved',
	MTP_EVENT_StoreAdded : 'MTP_EVENT_StoreAdded',	
	MTP_EVENT_StoreRemoved : 'MTP_EVENT_StoreRemoved',
	MTP_EVENT_DevicePropChanged : 'MTP_EVENT_DevicePropChanged',
	MTP_EVENT_ObjectInfoChanged : 'MTP_EVENT_ObjectInfoChanged',
	MTP_EVENT_DeviceInfoChanged : 'MTP_EVENT_DeviceInfoChanged',
	MTP_EVENT_RequestObjectTransfer : 'MTP_EVENT_RequestObjectTransfer',
	MTP_EVENT_StoreFull : 'MTP_EVENT_StoreFull',
	MTP_EVENT_StorageInfoChanged : 'MTP_EVENT_StorageInfoChanged',
	MTP_EVENT_CaptureComplete : 'MTP_EVENT_CaptureComplete',
	MTP_EVENT_ObjectAddedInSdram : 'MTP_EVENT_ObjectAddedInSdram',
	MTP_EVENT_CaptureCompleteRecInSdram : 'MTP_EVENT_CaptureCompleteRecInSdram',
	MTP_EVENT_RecordingInterrupted : 'MTP_EVENT_RecordingInterrupted'
}
def getMtpEventDesc(mtpEventCode):
	if mtpEventCode in MtpEventDescDictionary:
		return "{:s}".format(MtpEventDescDictionary[mtpEventCode])
	else:
		return "Unknown Event Code (0x{:04x})".format(mtpEventCode)

#
# MTP DeviceProp codes
#
MTP_DeviceProp_BatteryLevel							= 0x5001
MTP_DeviceProp_ImageSize							= 0x5003
MTP_DeviceProp_CompressionSetting					= 0x5004
MTP_DeviceProp_WhiteBalance							= 0x5005
MTP_DeviceProp_Fnumber								= 0x5007
MTP_DeviceProp_FocalLength							= 0x5008
MTP_DeviceProp_FocusMode							= 0x500A
MTP_DeviceProp_ExposureMeteringMode					= 0x500B
MTP_DeviceProp_FlashMode							= 0x500C
MTP_DeviceProp_ExposureTime							= 0x500D
MTP_DeviceProp_ExposureProgramMode					= 0x500E
MTP_DeviceProp_ExposureIndex						= 0x500F
MTP_DeviceProp_ExposureBiasCompensation				= 0x5010
MTP_DeviceProp_DateTime								= 0x5011
MTP_DeviceProp_StillCaptureMode						= 0x5013
MTP_DeviceProp_BurstNumber							= 0x5018
MTP_DeviceProp_FocusMeteringMode					= 0x501C
MTP_DeviceProp_Artist								= 0x501E
MTP_DeviceProp_Copyright							= 0x501F
MTP_DeviceProp_ResetShootingMenu					= 0xD015
MTP_DeviceProp_RawCompressionType					= 0xD016
MTP_DeviceProp_WbTuneAuto							= 0xD017
MTP_DeviceProp_WbTuneIncandescent					= 0xD018
MTP_DeviceProp_WbTuneFluorescent					= 0xD019
MTP_DeviceProp_WbTuneSunny							= 0xD01A
MTP_DeviceProp_WbTuneFlash							= 0xD01B
MTP_DeviceProp_WbTuneCloudy							= 0xD01C
MTP_DeviceProp_WbTuneShade							= 0xD01D
MTP_DeviceProp_WbColorTemp							= 0xD01E
MTP_DeviceProp_WbPresetDataNo						= 0xD01F
MTP_DeviceProp_WbPresetDataComment1					= 0xD021
MTP_DeviceProp_WbPresetDataComment2					= 0xD022
MTP_DeviceProp_WbPresetDataComment3					= 0xD023
MTP_DeviceProp_WbPresetDataComment4					= 0xD024
MTP_DeviceProp_WbPresetDataValue1					= 0xD026
MTP_DeviceProp_WbPresetDataValue2					= 0xD027
MTP_DeviceProp_WbPresetDataValue3					= 0xD028
MTP_DeviceProp_WbPresetDataValue4					= 0xD029
MTP_DeviceProp_FmmManualSetting						= 0xD02E
MTP_DeviceProp_F0ManualSetting						= 0xD02F
MTP_DeviceProp_CaptureAreaCrop						= 0xD030
MTP_DeviceProp_JpegCompressionPolicy				= 0xD031
MTP_DeviceProp_ColorSpace							= 0xD032
MTP_DeviceProp_DecreaseFlicker						= 0xD034
MTP_DeviceProp_EffectMode							= 0xD037
MTP_DeviceProp_WbPresetDataComment5					= 0xD038
MTP_DeviceProp_WbPresetDataComment6					= 0xD039
MTP_DeviceProp_WbTunePreset5						= 0xD03A
MTP_DeviceProp_WbTunePreset6						= 0xD03B
MTP_DeviceProp_WbPresetProtect5						= 0xD03C
MTP_DeviceProp_WbPresetProtect6						= 0xD03D
MTP_DeviceProp_WbPresetDataValue5					= 0xD03E
MTP_DeviceProp_WbPresetDataValue6					= 0xD03F
MTP_DeviceProp_ResetCustomSetting					= 0xD045
MTP_DeviceProp_DynamicAFonAFC						= 0xD048
MTP_DeviceProp_DynamicAFonAFS						= 0xD049
MTP_DeviceProp_FocusAreaSelect						= 0xD04F
MTP_DeviceProp_AFStillLockOn						= 0xD051
MTP_DeviceProp_EnableCopyright						= 0xD053
MTP_DeviceProp_ISOAutoControl						= 0xD054
MTP_DeviceProp_IsoStep								= 0xD055
MTP_DeviceProp_ExposureEVStep						= 0xD056
MTP_DeviceProp_CenterWeightedExRange				= 0xD059
MTP_DeviceProp_ExposureBaseCompMatrix				= 0xD05A
MTP_DeviceProp_ExposureBaseCompCenter				= 0xD05B
MTP_DeviceProp_ExposureBaseCompSpot					= 0xD05C
MTP_DeviceProp_AfAtLiveView							= 0xD05D
MTP_DeviceProp_AfModeAtLiveView						= 0xD061
MTP_DeviceProp_AngleLevel							= 0xD067
MTP_DeviceProp_CSpeedLow							= 0xD068
MTP_DeviceProp_BurstMaxNumber						= 0xD069
MTP_DeviceProp_ExposureDelay						= 0xD06A
MTP_DeviceProp_NoiseReduction						= 0xD06B
MTP_DeviceProp_NumberingMode						= 0xD06C
MTP_DeviceProp_NoiseReductionHiIso					= 0xD070
MTP_DeviceProp_ArtistV								= 0xD072
MTP_DeviceProp_CopyrightV							= 0xD073
MTP_DeviceProp_FlashSyncSpeed						= 0xD074
MTP_DeviceProp_FlashSlowSpeedLimit					= 0xD075
MTP_DeviceProp_BracketingType						= 0xD078
MTP_DeviceProp_BracketingOrder						= 0xD07A
MTP_DeviceProp_CommandDialSetting					= 0xD087
MTP_DeviceProp_EnableShutter						= 0xD08A
MTP_DeviceProp_EnableAFAreaPoint					= 0xD08D
MTP_DeviceProp_ImageSensorCleaning					= 0xD08F
MTP_DeviceProp_CommentString						= 0xD090
MTP_DeviceProp_EnableComment						= 0xD091
MTP_DeviceProp_OrientationSensorMode				= 0xD092
MTP_DeviceProp_ManualSettingLensNo					= 0xD093
MTP_DeviceProp_RetractableLensWarning				= 0xD09C
MTP_DeviceProp_MovieRecordScreenSize				= 0xD0A0
MTP_DeviceProp_MovieRecordMicrophoneLevel			= 0xD0A2
MTP_DeviceProp_MovieRecordDestination				= 0xD0A3
MTP_DeviceProp_MovieRecProhibitionCondition			= 0xD0A4
MTP_DeviceProp_MovieRecordQuality					= 0xD0A7
MTP_DeviceProp_MovieRecordMicrophoneLevelValue		= 0xD0A8
MTP_DeviceProp_MovieWindNoiseReduction				= 0xD0AA
MTP_DeviceProp_NccTemperatureOffset					= 0xD0AB
MTP_DeviceProp_MovieRecordingZone					= 0xD0AC
MTP_DeviceProp_MovieISOAutoControl					= 0xD0AD
MTP_DeviceProp_MovieISOAutoHighLimit				= 0xD0AE
MTP_DeviceProp_ExposureIndexEx						= 0xD0B4
MTP_DeviceProp_ISOControlSensitivity				= 0xD0B5
MTP_DeviceProp_EnableBracketing						= 0xD0C0
MTP_DeviceProp_AEBracketingStep						= 0xD0C1
MTP_DeviceProp_AEBracketingPattern					= 0xD0C2
MTP_DeviceProp_AEBracketingCount					= 0xD0C3
MTP_DeviceProp_WBBracketingStep						= 0xD0C4
MTP_DeviceProp_WBBracketingPattern					= 0xD0C5
MTP_DeviceProp_ADLBracketingPattern					= 0xD0C6
MTP_DeviceProp_ADLBracketingStep					= 0xD0C7
MTP_DeviceProp_LensID								= 0xD0E0
MTP_DeviceProp_LensSort								= 0xD0E1
MTP_DeviceProp_LensType								= 0xD0E2
MTP_DeviceProp_LensFocalMin							= 0xD0E3
MTP_DeviceProp_LensFocalMax							= 0xD0E4
MTP_DeviceProp_LensApatureMin						= 0xD0E5
MTP_DeviceProp_LensApatureMax						= 0xD0E6
MTP_DeviceProp_VignetteControl						= 0xD0F7
MTP_DeviceProp_AutoDistortion						= 0xD0F8
MTP_DeviceProp_SceneMode							= 0xD0F9
MTP_DeviceProp_UserMode1							= 0xD0FC
MTP_DeviceProp_UserMode2							= 0xD0FD
MTP_DeviceProp_ShutterSpeed							= 0xD100
MTP_DeviceProp_ExternalDC_IN						= 0xD101
MTP_DeviceProp_WarningStatus						= 0xD102
MTP_DeviceProp_AFLockStatus							= 0xD104
MTP_DeviceProp_AELockStatus							= 0xD105
MTP_DeviceProp_FVLockStatus							= 0xD106
MTP_DeviceProp_FocusArea							= 0xD108
MTP_DeviceProp_FlexibleProgram						= 0xD109
MTP_DeviceProp_RecordingMedia						= 0xD10B
MTP_DeviceProp_Orientation							= 0xD10E
MTP_DeviceProp_ExternalSpeedLightExist				= 0xD120
MTP_DeviceProp_ExternalSpeedLightStatus				= 0xD121
MTP_DeviceProp_ExternalSpeedLightSort				= 0xD122
MTP_DeviceProp_FlashCompensation					= 0xD124
MTP_DeviceProp_NewExternalSpeedLightMode			= 0xD125
MTP_DeviceProp_InternalFlashCompensation			= 0xD126
MTP_DeviceProp_ExternalSpeedLightMultiFlashMode		= 0xD12D
MTP_DeviceProp_HDRMode								= 0xD130
MTP_DeviceProp_HDRSmoothing							= 0xD132
MTP_DeviceProp_WbAutoType							= 0xD141
MTP_DeviceProp_Slot2ImageSaveMode					= 0xD148
MTP_DeviceProp_RawCompressionBitMode				= 0xD149
MTP_DeviceProp_Active_D_Lighting					= 0xD14E
MTP_DeviceProp_WbFluorescentType					= 0xD14F
MTP_DeviceProp_WbTuneColorTemp						= 0xD150
MTP_DeviceProp_WbTunePreset1						= 0xD152
MTP_DeviceProp_WbTunePreset2						= 0xD153
MTP_DeviceProp_WbTunePreset3						= 0xD154
MTP_DeviceProp_WbTunePreset4						= 0xD155
MTP_DeviceProp_WbPresetProtect1						= 0xD158
MTP_DeviceProp_WbPresetProtect2						= 0xD159
MTP_DeviceProp_WbPresetProtect3						= 0xD15A
MTP_DeviceProp_ActiveFolder							= 0xD15B
MTP_DeviceProp_WbPresetProtect4						= 0xD15C
MTP_DeviceProp_WhiteBalanceReset					= 0xD15D
MTP_DeviceProp_AFModeSelect							= 0xD161
MTP_DeviceProp_AFSubLight							= 0xD163
MTP_DeviceProp_ISOAutoShutterTime					= 0xD164
MTP_DeviceProp_InternalFlashMode					= 0xD167
MTP_DeviceProp_ISOAutoSetting						= 0xD16A
MTP_DeviceProp_ISOAutoHighLimit						= 0xD183
MTP_DeviceProp_MovieReleaseButton					= 0xD197
MTP_DeviceProp_LiveViewStatus						= 0xD1A2
MTP_DeviceProp_LiveViewImageZoomRatio				= 0xD1A3
MTP_DeviceProp_LiveViewProhibitionCondition			= 0xD1A4
MTP_DeviceProp_LiveViewSelector						= 0xD1A6
MTP_DeviceProp_MovieShutterSpeed					= 0xD1A8
MTP_DeviceProp_MovieFnumber							= 0xD1A9
MTP_DeviceProp_MovieExposureIndex					= 0xD1AA
MTP_DeviceProp_MovieExposureBiasCompensation		= 0xD1AB
MTP_DeviceProp_LiveViewImageSize					= 0xD1AC
MTP_DeviceProp_MovieExposureMeteringMode			= 0xD1AF
MTP_DeviceProp_ExposureDisplayStatus				= 0xD1B0
MTP_DeviceProp_ExposureIndicateStatus				= 0xD1B1
MTP_DeviceProp_InfoDisplayErrorStatus				= 0xD1B2
MTP_DeviceProp_ExposureIndicateLightup				= 0xD1B3
MTP_DeviceProp_ContinuousShootingCount				= 0xD1B4
MTP_DeviceProp_InternalFlashPopup					= 0xD1C0
MTP_DeviceProp_InternalFlashStatus					= 0xD1C1
MTP_DeviceProp_ApplicationMode						= 0xD1F0
MTP_DeviceProp_ExposureRemaining					= 0xD1F1
MTP_DeviceProp_ActiveSlot							= 0xD1F2
MTP_DeviceProp_ISOAutoShutterTimeCorrectionValue	= 0xD1F4
MTP_DeviceProp_ActivePicCtrlItem					= 0xD200
MTP_DeviceProp_ChangePicCtrlItem					= 0xD201
MTP_DeviceProp_MovieResetShootingMenu				= 0xD20E
MTP_DeviceProp_MovieCaptureAreaCrop					= 0xD20F
MTP_DeviceProp_MovieWbAutoType						= 0xD211
MTP_DeviceProp_MovieWbTuneAuto						= 0xD212
MTP_DeviceProp_MovieWbTuneIncandescent				= 0xD213
MTP_DeviceProp_MovieWbFluorescentType				= 0xD214
MTP_DeviceProp_MovieWbTuneFluorescent				= 0xD215
MTP_DeviceProp_MovieWbTuneSunny						= 0xD216
MTP_DeviceProp_MovieWbTuneCloudy					= 0xD218
MTP_DeviceProp_MovieWbTuneShade						= 0xD219
MTP_DeviceProp_MovieWbColorTemp						= 0xD21A
MTP_DeviceProp_MovieWbTuneColorTemp					= 0xD21B
MTP_DeviceProp_MovieWbPresetDataNo					= 0xD21C
MTP_DeviceProp_MovieWbPresetDataComment1			= 0xD21D
MTP_DeviceProp_MovieWbPresetDataComment2			= 0xD21E
MTP_DeviceProp_MovieWbPresetDataComment3			= 0xD21F
MTP_DeviceProp_MovieWbPresetDataComment4			= 0xD220
MTP_DeviceProp_MovieWbPresetDataComment5			= 0xD221
MTP_DeviceProp_MovieWbPresetDataComment6			= 0xD222
MTP_DeviceProp_MovieWbPresetDataValue1				= 0xD223
MTP_DeviceProp_MovieWbPresetDataValue2				= 0xD224
MTP_DeviceProp_MovieWbPresetDataValue3				= 0xD225
MTP_DeviceProp_MovieWbPresetDataValue4				= 0xD226
MTP_DeviceProp_MovieWbPresetDataValue5				= 0xD227
MTP_DeviceProp_MovieWbPresetDataValue6				= 0xD228
MTP_DeviceProp_MovieWbTunePreset1					= 0xD229
MTP_DeviceProp_MovieWbTunePreset2					= 0xD22A
MTP_DeviceProp_MovieWbTunePreset3					= 0xD22B
MTP_DeviceProp_MovieWbTunePreset4					= 0xD22C
MTP_DeviceProp_MovieWbTunePreset5					= 0xD22D
MTP_DeviceProp_MovieWbTunePreset6					= 0xD22E
MTP_DeviceProp_MovieWbPresetProtect1				= 0xD22F
MTP_DeviceProp_MovieWbPresetProtect2				= 0xD230
MTP_DeviceProp_MovieWbPresetProtect3				= 0xD231
MTP_DeviceProp_MovieWbPresetProtect4				= 0xD232
MTP_DeviceProp_MovieWbPresetProtect5				= 0xD233
MTP_DeviceProp_MovieWbPresetProtect6				= 0xD234
MTP_DeviceProp_MovieWhiteBalanceReset				= 0xD235
MTP_DeviceProp_MovieNoiseReductionHiIso				= 0xD236
MTP_DeviceProp_MovieActivePicCtrlItem				= 0xD237
MTP_DeviceProp_MovieChangePicCtrlItem				= 0xD238
MTP_DeviceProp_MovieWhiteBalance					= 0xD23A
MTP_DeviceProp_UseDeviceStageFlag					= 0xD303
MTP_DeviceProp_SessionInitiatorVersionInfo			= 0xD406
MTP_DeviceProp_PerceivedDeviceType					= 0xD407
MTP_DeviceProp_Canon_DateTimeUTC					= 0xD17C

MtpDevicePropDescDictionary = {\
	MTP_DeviceProp_BatteryLevel                                 : 'MTP_DeviceProp_BatteryLevel',
	MTP_DeviceProp_ImageSize                                    : 'MTP_DeviceProp_ImageSize',
	MTP_DeviceProp_CompressionSetting                           : 'MTP_DeviceProp_CompressionSetting',
	MTP_DeviceProp_WhiteBalance                                 : 'MTP_DeviceProp_WhiteBalance',
	MTP_DeviceProp_Fnumber                                      : 'MTP_DeviceProp_Fnumber',
	MTP_DeviceProp_FocalLength                                  : 'MTP_DeviceProp_FocalLength',
	MTP_DeviceProp_FocusMode                                    : 'MTP_DeviceProp_FocusMode',
	MTP_DeviceProp_ExposureMeteringMode                         : 'MTP_DeviceProp_ExposureMeteringMode',
	MTP_DeviceProp_FlashMode                                    : 'MTP_DeviceProp_FlashMode',
	MTP_DeviceProp_ExposureTime                                 : 'MTP_DeviceProp_ExposureTime',
	MTP_DeviceProp_ExposureProgramMode                          : 'MTP_DeviceProp_ExposureProgramMode',
	MTP_DeviceProp_ExposureIndex                                : 'MTP_DeviceProp_ExposureIndex',
	MTP_DeviceProp_ExposureBiasCompensation                     : 'MTP_DeviceProp_ExposureBiasCompensation',
	MTP_DeviceProp_DateTime                                     : 'MTP_DeviceProp_DateTime',
	MTP_DeviceProp_StillCaptureMode                             : 'MTP_DeviceProp_StillCaptureMode',
	MTP_DeviceProp_BurstNumber                                  : 'MTP_DeviceProp_BurstNumber',
	MTP_DeviceProp_FocusMeteringMode                            : 'MTP_DeviceProp_FocusMeteringMode',
	MTP_DeviceProp_Artist                                       : 'MTP_DeviceProp_Artist',
	MTP_DeviceProp_Copyright                                    : 'MTP_DeviceProp_Copyright',
	MTP_DeviceProp_ResetShootingMenu                            : 'MTP_DeviceProp_ResetShootingMenu',
	MTP_DeviceProp_RawCompressionType                           : 'MTP_DeviceProp_RawCompressionType',
	MTP_DeviceProp_WbTuneAuto                                   : 'MTP_DeviceProp_WbTuneAuto',
	MTP_DeviceProp_WbTuneIncandescent                           : 'MTP_DeviceProp_WbTuneIncandescent',
	MTP_DeviceProp_WbTuneFluorescent                            : 'MTP_DeviceProp_WbTuneFluorescent',
	MTP_DeviceProp_WbTuneSunny                                  : 'MTP_DeviceProp_WbTuneSunny',
	MTP_DeviceProp_WbTuneFlash                                  : 'MTP_DeviceProp_WbTuneFlash',
	MTP_DeviceProp_WbTuneCloudy                                 : 'MTP_DeviceProp_WbTuneCloudy',
	MTP_DeviceProp_WbTuneShade                                  : 'MTP_DeviceProp_WbTuneShade',
	MTP_DeviceProp_WbColorTemp                                  : 'MTP_DeviceProp_WbColorTemp',
	MTP_DeviceProp_WbPresetDataNo                               : 'MTP_DeviceProp_WbPresetDataNo',
	MTP_DeviceProp_WbPresetDataComment1                         : 'MTP_DeviceProp_WbPresetDataComment1',
	MTP_DeviceProp_WbPresetDataComment2                         : 'MTP_DeviceProp_WbPresetDataComment2',
	MTP_DeviceProp_WbPresetDataComment3                         : 'MTP_DeviceProp_WbPresetDataComment3',
	MTP_DeviceProp_WbPresetDataComment4                         : 'MTP_DeviceProp_WbPresetDataComment4',
	MTP_DeviceProp_WbPresetDataValue1                           : 'MTP_DeviceProp_WbPresetDataValue1',
	MTP_DeviceProp_WbPresetDataValue2                           : 'MTP_DeviceProp_WbPresetDataValue2',
	MTP_DeviceProp_WbPresetDataValue3                           : 'MTP_DeviceProp_WbPresetDataValue3',
	MTP_DeviceProp_WbPresetDataValue4                           : 'MTP_DeviceProp_WbPresetDataValue4',
	MTP_DeviceProp_FmmManualSetting                             : 'MTP_DeviceProp_FmmManualSetting',
	MTP_DeviceProp_F0ManualSetting                              : 'MTP_DeviceProp_F0ManualSetting',
	MTP_DeviceProp_CaptureAreaCrop                              : 'MTP_DeviceProp_CaptureAreaCrop',
	MTP_DeviceProp_JpegCompressionPolicy                        : 'MTP_DeviceProp_JpegCompressionPolicy',
	MTP_DeviceProp_ColorSpace                                   : 'MTP_DeviceProp_ColorSpace',
	MTP_DeviceProp_DecreaseFlicker                              : 'MTP_DeviceProp_DecreaseFlicker',
	MTP_DeviceProp_EffectMode                                   : 'MTP_DeviceProp_EffectMode',
	MTP_DeviceProp_WbPresetDataComment5                         : 'MTP_DeviceProp_WbPresetDataComment5',
	MTP_DeviceProp_WbPresetDataComment6                         : 'MTP_DeviceProp_WbPresetDataComment6',
	MTP_DeviceProp_WbTunePreset5                                : 'MTP_DeviceProp_WbTunePreset5',
	MTP_DeviceProp_WbTunePreset6                                : 'MTP_DeviceProp_WbTunePreset6',
	MTP_DeviceProp_WbPresetProtect5                             : 'MTP_DeviceProp_WbPresetProtect5',
	MTP_DeviceProp_WbPresetProtect6                             : 'MTP_DeviceProp_WbPresetProtect6',
	MTP_DeviceProp_WbPresetDataValue5                           : 'MTP_DeviceProp_WbPresetDataValue5',
	MTP_DeviceProp_WbPresetDataValue6                           : 'MTP_DeviceProp_WbPresetDataValue6',
	MTP_DeviceProp_ResetCustomSetting                           : 'MTP_DeviceProp_ResetCustomSetting',
	MTP_DeviceProp_DynamicAFonAFC                               : 'MTP_DeviceProp_DynamicAFonAFC',
	MTP_DeviceProp_DynamicAFonAFS                               : 'MTP_DeviceProp_DynamicAFonAFS',
	MTP_DeviceProp_FocusAreaSelect                              : 'MTP_DeviceProp_FocusAreaSelect',
	MTP_DeviceProp_AFStillLockOn                                : 'MTP_DeviceProp_AFStillLockOn',
	MTP_DeviceProp_EnableCopyright                              : 'MTP_DeviceProp_EnableCopyright',
	MTP_DeviceProp_ISOAutoControl                               : 'MTP_DeviceProp_ISOAutoControl',
	MTP_DeviceProp_IsoStep                                      : 'MTP_DeviceProp_IsoStep',
	MTP_DeviceProp_ExposureEVStep                               : 'MTP_DeviceProp_ExposureEVStep',
	MTP_DeviceProp_CenterWeightedExRange                        : 'MTP_DeviceProp_CenterWeightedExRange',
	MTP_DeviceProp_ExposureBaseCompMatrix                       : 'MTP_DeviceProp_ExposureBaseCompMatrix',
	MTP_DeviceProp_ExposureBaseCompCenter                       : 'MTP_DeviceProp_ExposureBaseCompCenter',
	MTP_DeviceProp_ExposureBaseCompSpot                         : 'MTP_DeviceProp_ExposureBaseCompSpot',
	MTP_DeviceProp_AfAtLiveView                                 : 'MTP_DeviceProp_AfAtLiveView',
	MTP_DeviceProp_AfModeAtLiveView                             : 'MTP_DeviceProp_AfModeAtLiveView',
	MTP_DeviceProp_AngleLevel                                   : 'MTP_DeviceProp_AngleLevel',
	MTP_DeviceProp_CSpeedLow                                    : 'MTP_DeviceProp_CSpeedLow',
	MTP_DeviceProp_BurstMaxNumber                               : 'MTP_DeviceProp_BurstMaxNumber',
	MTP_DeviceProp_ExposureDelay                                : 'MTP_DeviceProp_ExposureDelay',
	MTP_DeviceProp_NoiseReduction                               : 'MTP_DeviceProp_NoiseReduction',
	MTP_DeviceProp_NumberingMode                                : 'MTP_DeviceProp_NumberingMode',
	MTP_DeviceProp_NoiseReductionHiIso                          : 'MTP_DeviceProp_NoiseReductionHiIso',
	MTP_DeviceProp_ArtistV                                      : 'MTP_DeviceProp_ArtistV',
	MTP_DeviceProp_CopyrightV                                   : 'MTP_DeviceProp_CopyrightV',
	MTP_DeviceProp_FlashSyncSpeed                               : 'MTP_DeviceProp_FlashSyncSpeed',
	MTP_DeviceProp_FlashSlowSpeedLimit                          : 'MTP_DeviceProp_FlashSlowSpeedLimit',
	MTP_DeviceProp_BracketingType                               : 'MTP_DeviceProp_BracketingType',
	MTP_DeviceProp_BracketingOrder                              : 'MTP_DeviceProp_BracketingOrder',
	MTP_DeviceProp_CommandDialSetting                           : 'MTP_DeviceProp_CommandDialSetting',
	MTP_DeviceProp_EnableShutter                                : 'MTP_DeviceProp_EnableShutter',
	MTP_DeviceProp_EnableAFAreaPoint                            : 'MTP_DeviceProp_EnableAFAreaPoint',
	MTP_DeviceProp_ImageSensorCleaning                          : 'MTP_DeviceProp_ImageSensorCleaning',
	MTP_DeviceProp_CommentString                                : 'MTP_DeviceProp_CommentString',
	MTP_DeviceProp_EnableComment                                : 'MTP_DeviceProp_EnableComment',
	MTP_DeviceProp_OrientationSensorMode                        : 'MTP_DeviceProp_OrientationSensorMode',
	MTP_DeviceProp_ManualSettingLensNo                          : 'MTP_DeviceProp_ManualSettingLensNo',
	MTP_DeviceProp_RetractableLensWarning                       : 'MTP_DeviceProp_RetractableLensWarning',
	MTP_DeviceProp_MovieRecordScreenSize                        : 'MTP_DeviceProp_MovieRecordScreenSize',
	MTP_DeviceProp_MovieRecordMicrophoneLevel                   : 'MTP_DeviceProp_MovieRecordMicrophoneLevel',
	MTP_DeviceProp_MovieRecordDestination                       : 'MTP_DeviceProp_MovieRecordDestination',
	MTP_DeviceProp_MovieRecProhibitionCondition                 : 'MTP_DeviceProp_MovieRecProhibitionCondition',
	MTP_DeviceProp_MovieRecordQuality                           : 'MTP_DeviceProp_MovieRecordQuality',
	MTP_DeviceProp_MovieRecordMicrophoneLevelValue              : 'MTP_DeviceProp_MovieRecordMicrophoneLevelValue',
	MTP_DeviceProp_MovieWindNoiseReduction                      : 'MTP_DeviceProp_MovieWindNoiseReduction',
	MTP_DeviceProp_NccTemperatureOffset                         : 'MTP_DeviceProp_NccTemperatureOffset',
	MTP_DeviceProp_MovieRecordingZone                           : 'MTP_DeviceProp_MovieRecordingZone',
	MTP_DeviceProp_MovieISOAutoControl                          : 'MTP_DeviceProp_MovieISOAutoControl',
	MTP_DeviceProp_MovieISOAutoHighLimit                        : 'MTP_DeviceProp_MovieISOAutoHighLimit',
	MTP_DeviceProp_ExposureIndexEx                              : 'MTP_DeviceProp_ExposureIndexEx',
	MTP_DeviceProp_ISOControlSensitivity                        : 'MTP_DeviceProp_ISOControlSensitivity',
	MTP_DeviceProp_EnableBracketing                             : 'MTP_DeviceProp_EnableBracketing',
	MTP_DeviceProp_AEBracketingStep                             : 'MTP_DeviceProp_AEBracketingStep',
	MTP_DeviceProp_AEBracketingPattern                          : 'MTP_DeviceProp_AEBracketingPattern',
	MTP_DeviceProp_AEBracketingCount                            : 'MTP_DeviceProp_AEBracketingCount',
	MTP_DeviceProp_WBBracketingStep                             : 'MTP_DeviceProp_WBBracketingStep',
	MTP_DeviceProp_WBBracketingPattern                          : 'MTP_DeviceProp_WBBracketingPattern',
	MTP_DeviceProp_ADLBracketingPattern                         : 'MTP_DeviceProp_ADLBracketingPattern',
	MTP_DeviceProp_ADLBracketingStep                            : 'MTP_DeviceProp_ADLBracketingStep',
	MTP_DeviceProp_LensID                                       : 'MTP_DeviceProp_LensID',
	MTP_DeviceProp_LensSort                                     : 'MTP_DeviceProp_LensSort',
	MTP_DeviceProp_LensType                                     : 'MTP_DeviceProp_LensType',
	MTP_DeviceProp_LensFocalMin                                 : 'MTP_DeviceProp_LensFocalMin',
	MTP_DeviceProp_LensFocalMax                                 : 'MTP_DeviceProp_LensFocalMax',
	MTP_DeviceProp_LensApatureMin                               : 'MTP_DeviceProp_LensApatureMin',
	MTP_DeviceProp_LensApatureMax                               : 'MTP_DeviceProp_LensApatureMax',
	MTP_DeviceProp_VignetteControl                              : 'MTP_DeviceProp_VignetteControl',
	MTP_DeviceProp_AutoDistortion                               : 'MTP_DeviceProp_AutoDistortion',
	MTP_DeviceProp_SceneMode                                    : 'MTP_DeviceProp_SceneMode',
	MTP_DeviceProp_UserMode1                                    : 'MTP_DeviceProp_UserMode1',
	MTP_DeviceProp_UserMode2                                    : 'MTP_DeviceProp_UserMode2',
	MTP_DeviceProp_ShutterSpeed                                 : 'MTP_DeviceProp_ShutterSpeed',
	MTP_DeviceProp_ExternalDC_IN                                : 'MTP_DeviceProp_ExternalDC_IN',
	MTP_DeviceProp_WarningStatus                                : 'MTP_DeviceProp_WarningStatus',
	MTP_DeviceProp_AFLockStatus                                 : 'MTP_DeviceProp_AFLockStatus',
	MTP_DeviceProp_AELockStatus                                 : 'MTP_DeviceProp_AELockStatus',
	MTP_DeviceProp_FVLockStatus                                 : 'MTP_DeviceProp_FVLockStatus',
	MTP_DeviceProp_FocusArea                                    : 'MTP_DeviceProp_FocusArea',
	MTP_DeviceProp_FlexibleProgram                              : 'MTP_DeviceProp_FlexibleProgram',
	MTP_DeviceProp_RecordingMedia                               : 'MTP_DeviceProp_RecordingMedia',
	MTP_DeviceProp_Orientation                                  : 'MTP_DeviceProp_Orientation',
	MTP_DeviceProp_ExternalSpeedLightExist                      : 'MTP_DeviceProp_ExternalSpeedLightExist',
	MTP_DeviceProp_ExternalSpeedLightStatus                     : 'MTP_DeviceProp_ExternalSpeedLightStatus',
	MTP_DeviceProp_ExternalSpeedLightSort                       : 'MTP_DeviceProp_ExternalSpeedLightSort',
	MTP_DeviceProp_FlashCompensation                            : 'MTP_DeviceProp_FlashCompensation',
	MTP_DeviceProp_NewExternalSpeedLightMode                    : 'MTP_DeviceProp_NewExternalSpeedLightMode',
	MTP_DeviceProp_InternalFlashCompensation                    : 'MTP_DeviceProp_InternalFlashCompensation',
	MTP_DeviceProp_ExternalSpeedLightMultiFlashMode             : 'MTP_DeviceProp_ExternalSpeedLightMultiFlashMode',
	MTP_DeviceProp_HDRMode                                      : 'MTP_DeviceProp_HDRMode',
	MTP_DeviceProp_HDRSmoothing                                 : 'MTP_DeviceProp_HDRSmoothing',
	MTP_DeviceProp_WbAutoType                                   : 'MTP_DeviceProp_WbAutoType',
	MTP_DeviceProp_Slot2ImageSaveMode                           : 'MTP_DeviceProp_Slot2ImageSaveMode',
	MTP_DeviceProp_RawCompressionBitMode                        : 'MTP_DeviceProp_RawCompressionBitMode',
	MTP_DeviceProp_Active_D_Lighting                            : 'MTP_DeviceProp_Active_D_Lighting',
	MTP_DeviceProp_WbFluorescentType                            : 'MTP_DeviceProp_WbFluorescentType',
	MTP_DeviceProp_WbTuneColorTemp                              : 'MTP_DeviceProp_WbTuneColorTemp',
	MTP_DeviceProp_WbTunePreset1                                : 'MTP_DeviceProp_WbTunePreset1',
	MTP_DeviceProp_WbTunePreset2                                : 'MTP_DeviceProp_WbTunePreset2',
	MTP_DeviceProp_WbTunePreset3                                : 'MTP_DeviceProp_WbTunePreset3',
	MTP_DeviceProp_WbTunePreset4                                : 'MTP_DeviceProp_WbTunePreset4',
	MTP_DeviceProp_WbPresetProtect1                             : 'MTP_DeviceProp_WbPresetProtect1',
	MTP_DeviceProp_WbPresetProtect2                             : 'MTP_DeviceProp_WbPresetProtect2',
	MTP_DeviceProp_WbPresetProtect3                             : 'MTP_DeviceProp_WbPresetProtect3',
	MTP_DeviceProp_ActiveFolder                                 : 'MTP_DeviceProp_ActiveFolder',
	MTP_DeviceProp_WbPresetProtect4                             : 'MTP_DeviceProp_WbPresetProtect4',
	MTP_DeviceProp_WhiteBalanceReset                            : 'MTP_DeviceProp_WhiteBalanceReset',
	MTP_DeviceProp_AFModeSelect                                 : 'MTP_DeviceProp_AFModeSelect',
	MTP_DeviceProp_AFSubLight                                   : 'MTP_DeviceProp_AFSubLight',
	MTP_DeviceProp_ISOAutoShutterTime                           : 'MTP_DeviceProp_ISOAutoShutterTime',
	MTP_DeviceProp_InternalFlashMode                            : 'MTP_DeviceProp_InternalFlashMode',
	MTP_DeviceProp_ISOAutoSetting                               : 'MTP_DeviceProp_ISOAutoSetting',
	MTP_DeviceProp_ISOAutoHighLimit                             : 'MTP_DeviceProp_ISOAutoHighLimit',
	MTP_DeviceProp_MovieReleaseButton                           : 'MTP_DeviceProp_MovieReleaseButton',
	MTP_DeviceProp_LiveViewStatus                               : 'MTP_DeviceProp_LiveViewStatus',
	MTP_DeviceProp_LiveViewImageZoomRatio                       : 'MTP_DeviceProp_LiveViewImageZoomRatio',
	MTP_DeviceProp_LiveViewProhibitionCondition                 : 'MTP_DeviceProp_LiveViewProhibitionCondition',
	MTP_DeviceProp_LiveViewSelector                             : 'MTP_DeviceProp_LiveViewSelector',
	MTP_DeviceProp_MovieShutterSpeed                            : 'MTP_DeviceProp_MovieShutterSpeed',
	MTP_DeviceProp_MovieFnumber                                 : 'MTP_DeviceProp_MovieFnumber',
	MTP_DeviceProp_MovieExposureIndex                           : 'MTP_DeviceProp_MovieExposureIndex',
	MTP_DeviceProp_MovieExposureBiasCompensation                : 'MTP_DeviceProp_MovieExposureBiasCompensation',
	MTP_DeviceProp_LiveViewImageSize                            : 'MTP_DeviceProp_LiveViewImageSize',
	MTP_DeviceProp_MovieExposureMeteringMode                    : 'MTP_DeviceProp_MovieExposureMeteringMode',
	MTP_DeviceProp_ExposureDisplayStatus                        : 'MTP_DeviceProp_ExposureDisplayStatus',
	MTP_DeviceProp_ExposureIndicateStatus                       : 'MTP_DeviceProp_ExposureIndicateStatus',
	MTP_DeviceProp_InfoDisplayErrorStatus                       : 'MTP_DeviceProp_InfoDisplayErrorStatus',
	MTP_DeviceProp_ExposureIndicateLightup                      : 'MTP_DeviceProp_ExposureIndicateLightup',
	MTP_DeviceProp_ContinuousShootingCount                      : 'MTP_DeviceProp_ContinuousShootingCount',
	MTP_DeviceProp_InternalFlashPopup                           : 'MTP_DeviceProp_InternalFlashPopup',
	MTP_DeviceProp_InternalFlashStatus                          : 'MTP_DeviceProp_InternalFlashStatus',
	MTP_DeviceProp_ApplicationMode                              : 'MTP_DeviceProp_ApplicationMode',
	MTP_DeviceProp_ExposureRemaining                            : 'MTP_DeviceProp_ExposureRemaining',
	MTP_DeviceProp_ActiveSlot                                   : 'MTP_DeviceProp_ActiveSlot',
	MTP_DeviceProp_ISOAutoShutterTimeCorrectionValue            : 'MTP_DeviceProp_ISOAutoShutterTimeCorrectionValue',
	MTP_DeviceProp_ActivePicCtrlItem                            : 'MTP_DeviceProp_ActivePicCtrlItem',
	MTP_DeviceProp_ChangePicCtrlItem                            : 'MTP_DeviceProp_ChangePicCtrlItem',
	MTP_DeviceProp_MovieResetShootingMenu                       : 'MTP_DeviceProp_MovieResetShootingMenu',
	MTP_DeviceProp_MovieCaptureAreaCrop                         : 'MTP_DeviceProp_MovieCaptureAreaCrop',
	MTP_DeviceProp_MovieWbAutoType                              : 'MTP_DeviceProp_MovieWbAutoType',
	MTP_DeviceProp_MovieWbTuneAuto                              : 'MTP_DeviceProp_MovieWbTuneAuto',
	MTP_DeviceProp_MovieWbTuneIncandescent                      : 'MTP_DeviceProp_MovieWbTuneIncandescent',
	MTP_DeviceProp_MovieWbFluorescentType                       : 'MTP_DeviceProp_MovieWbFluorescentType',
	MTP_DeviceProp_MovieWbTuneFluorescent                       : 'MTP_DeviceProp_MovieWbTuneFluorescent',
	MTP_DeviceProp_MovieWbTuneSunny                             : 'MTP_DeviceProp_MovieWbTuneSunny',
	MTP_DeviceProp_MovieWbTuneCloudy                            : 'MTP_DeviceProp_MovieWbTuneCloudy',
	MTP_DeviceProp_MovieWbTuneShade                             : 'MTP_DeviceProp_MovieWbTuneShade',
	MTP_DeviceProp_MovieWbColorTemp                             : 'MTP_DeviceProp_MovieWbColorTemp',
	MTP_DeviceProp_MovieWbTuneColorTemp                         : 'MTP_DeviceProp_MovieWbTuneColorTemp',
	MTP_DeviceProp_MovieWbPresetDataNo                          : 'MTP_DeviceProp_MovieWbPresetDataNo',
	MTP_DeviceProp_MovieWbPresetDataComment1                    : 'MTP_DeviceProp_MovieWbPresetDataComment1',
	MTP_DeviceProp_MovieWbPresetDataComment2                    : 'MTP_DeviceProp_MovieWbPresetDataComment2',
	MTP_DeviceProp_MovieWbPresetDataComment3                    : 'MTP_DeviceProp_MovieWbPresetDataComment3',
	MTP_DeviceProp_MovieWbPresetDataComment4                    : 'MTP_DeviceProp_MovieWbPresetDataComment4',
	MTP_DeviceProp_MovieWbPresetDataComment5                    : 'MTP_DeviceProp_MovieWbPresetDataComment5',
	MTP_DeviceProp_MovieWbPresetDataComment6                    : 'MTP_DeviceProp_MovieWbPresetDataComment6',
	MTP_DeviceProp_MovieWbPresetDataValue1                      : 'MTP_DeviceProp_MovieWbPresetDataValue1',
	MTP_DeviceProp_MovieWbPresetDataValue2                      : 'MTP_DeviceProp_MovieWbPresetDataValue2',
	MTP_DeviceProp_MovieWbPresetDataValue3                      : 'MTP_DeviceProp_MovieWbPresetDataValue3',
	MTP_DeviceProp_MovieWbPresetDataValue4                      : 'MTP_DeviceProp_MovieWbPresetDataValue4',
	MTP_DeviceProp_MovieWbPresetDataValue5                      : 'MTP_DeviceProp_MovieWbPresetDataValue5',
	MTP_DeviceProp_MovieWbPresetDataValue6                      : 'MTP_DeviceProp_MovieWbPresetDataValue6',
	MTP_DeviceProp_MovieWbTunePreset1                           : 'MTP_DeviceProp_MovieWbTunePreset1',
	MTP_DeviceProp_MovieWbTunePreset2                           : 'MTP_DeviceProp_MovieWbTunePreset2',
	MTP_DeviceProp_MovieWbTunePreset3                           : 'MTP_DeviceProp_MovieWbTunePreset3',
	MTP_DeviceProp_MovieWbTunePreset4                           : 'MTP_DeviceProp_MovieWbTunePreset4',
	MTP_DeviceProp_MovieWbTunePreset5                           : 'MTP_DeviceProp_MovieWbTunePreset5',
	MTP_DeviceProp_MovieWbTunePreset6                           : 'MTP_DeviceProp_MovieWbTunePreset6',
	MTP_DeviceProp_MovieWbPresetProtect1                        : 'MTP_DeviceProp_MovieWbPresetProtect1',
	MTP_DeviceProp_MovieWbPresetProtect2                        : 'MTP_DeviceProp_MovieWbPresetProtect2',
	MTP_DeviceProp_MovieWbPresetProtect3                        : 'MTP_DeviceProp_MovieWbPresetProtect3',
	MTP_DeviceProp_MovieWbPresetProtect4                        : 'MTP_DeviceProp_MovieWbPresetProtect4',
	MTP_DeviceProp_MovieWbPresetProtect5                        : 'MTP_DeviceProp_MovieWbPresetProtect5',
	MTP_DeviceProp_MovieWbPresetProtect6                        : 'MTP_DeviceProp_MovieWbPresetProtect6',
	MTP_DeviceProp_MovieWhiteBalanceReset                       : 'MTP_DeviceProp_MovieWhiteBalanceReset',
	MTP_DeviceProp_MovieNoiseReductionHiIso                     : 'MTP_DeviceProp_MovieNoiseReductionHiIso',
	MTP_DeviceProp_MovieActivePicCtrlItem                       : 'MTP_DeviceProp_MovieActivePicCtrlItem',
	MTP_DeviceProp_MovieChangePicCtrlItem                       : 'MTP_DeviceProp_MovieChangePicCtrlItem',
	MTP_DeviceProp_MovieWhiteBalance                            : 'MTP_DeviceProp_MovieWhiteBalance',
	MTP_DeviceProp_UseDeviceStageFlag                           : 'MTP_DeviceProp_UseDeviceStageFlag',
	MTP_DeviceProp_SessionInitiatorVersionInfo                  : 'MTP_DeviceProp_SessionInitiatorVersionInfo',
	MTP_DeviceProp_PerceivedDeviceType                          : 'MTP_DeviceProp_PerceivedDeviceType',
	MTP_DeviceProp_Canon_DateTimeUTC							: 'MTP_DeviceProp_Canon_DateTimeUTC'
}
def getMtpDevicePropDesc(mtpDevicePropCode):
	if mtpDevicePropCode in MtpDevicePropDescDictionary:
		return "{:s}".format(MtpDevicePropDescDictionary[mtpDevicePropCode])
	else:
		return "Unknown DeviceProp Code (0x{:04x})".format(mtpDevicePropCode)
		
#
# MTP Data Structures
#
MtpDeviceInfoTuple = namedtuple('MtpDeviceInfoTuple', 'standardVersion vendorExtensionID vendorExtensionVersion, vendorExtensionDescStr \
						operationsSupportedSet eventsSupportedSet devicePropertiesSupportedSet \
						captureFormatsSupportedSet imageFormatsSupportedSet manufacturerStr \
						modelStr deviceVersionStr serialNumberStr')
MptStorageIdsTuple = namedtuple('MptStorageIdsTuple', 'storageIdsList')
MtpStorageInfoTuple = namedtuple('MtpStorageInfoTuple', 'storageType, fileSystemType, accessCapability, maxCapacityBytes \
						 freeSpaceBytes, freeSpaceInImages, storageDescription, volumeLabel')						
MtpObjectInfoTuple = namedtuple('MtpObjectInfoTuple', 'storageId objectFormat protectionStatus	\
						objectCompressedSize thumbFormat thumbCompressedSize \
						thumbPixWidth thumbPixHeight imagePixWidth imagePixHeight \
						imageBitDepth parentObject associationType \
						associationDesc sequenceNumber filename \
						captureDateStr modificationDateStr')
						