#!/usr/bin/env python

#
#############################################################################
#
# dlinkedlist.py - Doubly-Linked List class
# Copyright (C) 2015, testcams.com
#
# This module is licensed under GPL v3: http://www.gnu.org/licenses/gpl-3.0.html
#
#############################################################################
#

from __future__ import print_function
from __future__ import division

class LinkedList():
	def __init__(self):
		self._head = None
		self._tail = None
		self._countObjs = 0
	def insert(self, objIns):
		objInList = self._head
		if not objInList:
			# we're the first obj in list
			self._head = objIns
			self._tail = objIns
			# already set in LinkedListObj()__init__: objIns._prev = None
			# already set in LinkedListObj()__init__: objIns._next = None
		else:			
			while objInList:
				if objIns._key < objInList._key:
					objIns._next = objInList
					objIns._prev = objInList._prev
					if objInList._prev:
						objInList._prev._next = objIns
					objInList._prev = objIns
					if objIns._prev == None:
						self._head = objIns
					elif objIns._next == None:
						self._tail = tail
					break;
				objInList = objInList._next
			if not objInList:
				# no key smaller than objIns, insert at end
				# already set in LinkedListObj()__init__: objIns._next = None
				objIns._prev = self._tail
				self._tail._next = objIns
				self._tail = objIns
		self._countObjs += 1
	def remove(self, objRem):
		if objRem == self._head:
			self._head = objRem._next
			if not self._head:
				# we are only obj in list
				self._tail = None
		else:
			objRem._prev._next = objRem._next
			if objRem._next != None:
				objRem._next._prev = objRem._prev
			else:
				# we were in the last obj position in list
				self._tail = None
		self._countObjs -= 1
	def head(self):
		return self._head
	def tail(self):		
		return self._tail
	def count(self):
		return self._countObjs
	def dump(self):
		obj = self.getHead()
		i = 0
		while obj:
			print("{:d}, {}: key={}".format(i, obj, obj._key))
			obj = obj.getNext()
			i += 1
			
class LinkedListObj():
	def __init__(self, key, linkedList=None):
		self._key = key
		self._prev = None
		self._next = None
		if linkedList:
			linkedList.insert(self)
		# else obj user will call insert() himself
	# note I named these llNext()/llPrev() instead of  next()/prev() in case inherited class wants to claim those generic method names for itself
	def llNext(self):
		return self._next
	def llPrev(self):
		return self._prev
