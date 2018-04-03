#!/usr/bin/env python
import json
import requests
from pprint import pprint
from OpenSSL import crypto, SSL
import os, sys, time
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


def onboardDevice(newKey, callback, devlog):
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
	devlog("Advertise Device")

	headers = {'content-type': 'application/json'}
	response = requests.post('https://alpineseniorcare.com/micronets/device/advertise', data = data, headers = headers)

	if response.status_code == 204:
		callback("Onboard canceled")
		return
	elif response.status_code != 200:
		callback("HTTP Error: {}".format(response.status_code))
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
	
	print "submitting CSR"
	devlog("Submitting CSR")

	# Sleeps are for demo visual effect. Can be removed.
	time.sleep(2)

	headers = {'content-type': 'application/json','authorization': csrt['token']}
	response = requests.post('https://alpineseniorcare.com/micronets/device/cert', data = data, headers = headers)
	if response.status_code != 200:
		callback("HTTP Error: {}".format(response.http_status))
		return

	# Parse out reply and set up wpa configuration
	reply = response.json()
	print response.json()

	devlog ("Rcvd Credentials")
	time.sleep(2)

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
	devlog("Configuring WiFi")
	time.sleep(2)

	reqBody = {'UID': device['UID']}
	data = json.dumps(reqBody)

	response = requests.post('https://alpineseniorcare.com/micronets/device/pair-complete', data = data, headers = headers)
	if response.status_code != 200:
		callback("error: {}".format(response.http_status))
		return

	callback('Onboard Complete')

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
