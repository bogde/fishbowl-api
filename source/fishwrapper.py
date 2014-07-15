#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import struct
import hashlib
from lxml import etree

import xmlrequests
from statuscodes import getstatus


class Fishbowlapi:
	"""
	fishbowl api class
	example usage:
	foo = Fishbowlapi('admin', 'admin', 'localhost')
	"""
	def __init__(self, username, password, host, port=28192):
		# attributes
		self.host = host
		self.port = port
		self.username = username
		self.password = hashlib.md5(password).digest().encode('base64').replace('\n', "")
		self.stream = None
		self.response = None
		self.key = None
		self.status = None
		self.statuscode = None
		# connect and login
		self.login()
	# below are methods used to login/generate requests
	def connect(self):
		""" open socket stream and set timeout """
		self.stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.stream.connect((self.host, self.port))
		# timeout after 5 seconds
		self.stream.settimeout(5)
	def get_response(self):
		""" get server response """
		packed_length = self.stream.recv(4)
		length = struct.unpack('>L', packed_length)
		byte_count = 0
		msg_received = ''
		while byte_count < length[0]:
			try:
				byte = self.stream.recv(1)
				byte_count += 1
				msg_received += byte
			except socket.timeout:
				self.status = "Error: Connection Timeout"
				print self.status
				break
		return msg_received
	def updatestatus(self, statuscode, status=""):
		""" get status string from error code and update status """
		self.statuscode = statuscode
		self.status = getstatus(statuscode)
	def close(self):
		""" close connection to fishbowl api """
		self.stream.close()
	def login(self):
		"""Login method, use to login to fishbowl server
		and obtain api key """
		# create XML request
		xml = xmlrequests.Login(self.username, self.password).request
		# open socket and connect
		self.connect()
		# send request to fishbowl server
		self.stream.send(msg(xml))
		# get server response
		self.response = self.get_response()
		# parse xml, grab api key, check status
		for element in xmlparse(self.response).iter():
			if element.tag == "Key":
				self.key = element.text
			if (element.get("statusCode") is not None
					and element.tag == "LoginRs"):
				statuscode = element.get("statusCode")
				self.updatestatus(statuscode)
	# request methods available to the user after instantiation
	def add_inventory(self, partnum, qty, uomid, cost, loctagnum):
		""" Method for adding inventory to Fishbowl """
		# create XML request
		xml = xmlrequests.AddInventory(str(partnum), str(qty), str(uomid),
			                           str(cost), str(loctagnum), self.key).request
		# send request to fishbowl server
		self.stream.send(msg(xml))
		# get server response
		self.response = self.get_response()
		# parse xml, check status
		for element in xmlparse(self.response).iter():
			if element.tag == 'AddInventoryRs':
				if element.get('statusCode'):
					statuscode = element.get('statusCode')
					self.updatestatus(statuscode)

# global functions
def xmlparse(xml):
	""" global function for parsing xml """
	root = etree.fromstring(xml)
	return root

def msg(msg):
	""" calculate msg length and prepend to msg """
	msg_length = len(msg)
	# '>L' = 4 byte unsigned long, big endian format
	packed_length = struct.pack('>L', msg_length)
	msg_to_send = packed_length + msg
	return msg_to_send
