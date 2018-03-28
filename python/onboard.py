#!/usr/bin/env python
import json
import requests
from pprint import pprint
from OpenSSL import crypto, SSL
import os, sys
import base64
from uuid import getnode as get_mac

from lib.ecc_keys import *
from lib.wpa_supplicant import *

# key names/location
keyPath = '../ssh'
keyName = 'wifiKey'
csrName = 'wifiCSR'
UID = None

if not os.path.exists(keyPath):
    os.makedirs(keyPath)

def cancelOnboard():
	global UID

	headers = {'content-type': 'application/json'}
	body = {'UID': UID}
	data = json.dumps(body)
	response = requests.post('https://alpineseniorcare.com/micronets/device/cancel', data = data, headers = headers)

	print "cancel: {}".format(json.dumps(reqBody))


def onboardDevice(newKey, callback):
	global UID

	if newKey == True:
		deleteKey(keyName, keyPath)

	private_key = None

	# Generate key pair
	if not keyExists(keyName, keyPath):
		private_key = generateKey(keyName, keyPath)
	else:
		private_key = loadPrivateKey(keyName, keyPath)

	public_key = private_key.public_key()

	# Advertise our device
	#cwd = os.path.dirname(os.path.realpath(__file__))
	#print "cwd: {}".format(cwd)
	fileDir = os.path.dirname(os.path.realpath('__file__'))
	filename = os.path.join(fileDir, '../config/device.json')
	data = open(filename).read()

	# Replace UID with hash of public key
	device = json.loads(data)
	device['UID'] = publicKeyHash(public_key);
	device['MAC'] = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
	data = json.dumps(device)

	# Save in case we cancel
	UID = device['UID']

	print "advertising device:\n{}".format(data)

	headers = {'content-type': 'application/json'}
	response = requests.post('https://alpineseniorcare.com/micronets/device/advertise', data = data, headers = headers)

	if response.status_code == 204:
		callback("canceled")
		return
	elif response.status_code != 200:
		callback("error: {}".format(response.status_code))
		return


	csrt = response.json()
	# TODO: keyType and keyBits should be separated in CSRT, and CSRT should include C, ST, L, O, OU, etc
	# Update: not even using keytype at the moment. Defaulting to ECC
	# keySpec = csrt['csrTemplate']['keyType'].split(":")

	print "received csrt: {}".format(response)
	print "token: {}".format(csrt['token'])

	# Generate a CSR
	csr = generateCSR(private_key, csrName, keyPath)

	# Create the submit message
	reqBody = {'UID': device['UID']}
	with open(keyPath+'/'+'wifiCSR.pem', "rb") as csr_file:
	    reqBody['csr'] = base64.b64encode(csr_file.read())
	data = json.dumps(reqBody)
	
	print "/cert body: "+data

	print "submitting CSR"

	headers = {'content-type': 'application/json','authorization': csrt['token']}
	response = requests.post('https://alpineseniorcare.com/micronets/device/cert', data = data, headers = headers)
	if response.status_code != 200:
		callback("error: {}".format(response.http_status))
		return

	# Parse out reply and set up wpa configuration
	reply = response.json()
	print response.json()

	ssid = reply['subscriber']['ssid']
	wifi_cert64 = reply['wifiCert']
	ca_cert64 = reply['caCert']

	wifi_cert = base64.b64decode(wifi_cert64);
	ca_cert = base64.b64decode(ca_cert64);

	print "ssid: {}".format(ssid)
	print "wifi_cert: {}".format(wifi_cert)
	print "ca_cert: {}".format(ca_cert)

	print "configuring wpa_supplicant"
	wpa_add_subscriber(ssid, ca_cert, wifi_cert, privateKeyPEM(private_key), 'micronets')

	reqBody = {'UID': device['UID']}
	data = json.dumps(reqBody)

	response = requests.post('https://alpineseniorcare.com/micronets/device/pair-complete', data = data, headers = headers)
	if response.status_code != 200:
		callback("error: {}".format(response.http_status))
		return

	callback('complete')

# Remove private key
def removeKey():
	deleteKey(keyName, keyPath)

# Remove subscriber config
def resetDevice():
	wpa_reset()

if __name__ == '__main__':

	if len(sys.argv) > 1 and sys.argv[1] == 'reset':
		print "reset"
		# TODO: Send message to registration server
		wpa_reset()
	else:
		print "onboarding"
		onboardDevice(len(sys.argv) > 1 and sys.argv[1] == 'newkey')
