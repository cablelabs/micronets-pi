#!/usr/bin/env python
import json
import requests
from pprint import pprint
from OpenSSL import crypto, SSL
import os, sys, time, traceback
from subprocess import call

import base64
from uuid import getnode as get_mac

from lib.ecc_keys import *
from lib.wpa_supplicant import *

import pprint

# key names/location
keyPath = '../ssl'
keyName = 'wifiKey'
csrName = 'wifiCSR'
deviceID = None

if not os.path.exists(keyPath):
    os.makedirs(keyPath)

# Ensure we have a symlink to device metadata
fileDir = os.path.dirname(os.path.realpath('__file__'))
deviceConfig = os.path.join(fileDir, '../config/thisDevice')

if not os.path.exists(deviceConfig):
	# default to device 0. 
	# to change selected device, manually replace symbolic link.
	defaultDevice = os.path.join(fileDir, '../config/devices/device-0.json')
	call("ln -s " + defaultDevice + " " + deviceConfig, shell=True)

# Ensure we have a registration server configuration, copy if needed.
fileDir = os.path.dirname(os.path.realpath('__file__'))
registrationConfig = os.path.join(fileDir, '../config/thisRegistration.json')

if not os.path.exists(registrationConfig):
	# default to device 0. 
	# to change selected device, manually replace symbolic link.
	defaultRegistration = os.path.join(fileDir, '../config/registration.json')
	call("cp " + defaultRegistration + " " + registrationConfig, shell=True)

def makeURL(path):

	try:
		registrationConfig = os.path.join(fileDir, '../config/thisRegistration.json')
		fileData = open(registrationConfig).read()
		print 'fileData: {}'.format(fileData)
		registration = json.loads(fileData)
		pprint.pprint(registration)
		host = registration['url']

	except (OSError, IOError) as e: # FileNotFoundError does not exist on Python < 3.3
		host = "https://alpineseniorcare.com/micronets"

	url = "{}/{}".format(host, path)
	return url

def cancelOnboard(devlog):
	try:
		execCancelOnboard(devlog)
	except Exception as e:
		devlog("!! {}".format(e.__doc__))
		print e.__doc__
		print e.message
		print '-'*60
        traceback.print_exc(file=sys.stdout)
        print '-'*60


def execCancelOnboard(devlog):
	global deviceID

	headers = {'content-type': 'application/json'}
	body = {'deviceID': deviceID}
	data = json.dumps(body)
	url = makeURL('device/cancel')
	response = requests.post(url, data = data, headers = headers)

def onboardDevice(newKey, display, devlog):
	try:
		execOnboardDevice(newKey, display, devlog)
	except Exception as e:
		display.add_message(e.__doc__)
		devlog("!! {}".format(e.__doc__))
		print e.__doc__
		print e.message
		print '-'*60
        traceback.print_exc(file=sys.stdout)
        print '-'*60

def execOnboardDevice(newKey, display, devlog):
	global deviceID

	if newKey == True:
		deleteKey(keyName, keyPath)
		print "generating new key pair"
		devlog("Generate Keys")


	private_key = None

	# Generate key pair
	if not keyExists(keyName, keyPath):
		private_key = generateKey(keyName, keyPath)
	else:
		private_key = loadPrivateKey(keyName, keyPath)

	public_key = private_key.public_key()

	# Advertise our device
	fileDir = os.path.dirname(os.path.realpath('__file__'))
	filename = deviceConfig
	data = open(filename).read()

	# Replace UID with hash of public key
	device = json.loads(data)
	device['deviceID'] = publicKeyHash(public_key);
	device['macAddress'] = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
	device['serial'] = device['vendor'][:1] + device['model'][:1] + '-' + device['deviceID'][-8:].upper()
	data = json.dumps(device)

	# Save in case we cancel
	deviceID = device['deviceID']

	print "advertising device:\n{}".format(data)
	devlog("Advertise Device")

	headers = {'content-type': 'application/json'}
	url = makeURL('device/advertise')
	response = requests.post(url, data = data, headers = headers)

	if response.status_code == 204:
		display.add_message("Onboard canceled")
		return
	elif response.status_code != 200:
		display.add_message("HTTP Error: {}".format(response.status_code))
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
	reqBody = {'deviceID': device['deviceID']}
	with open(keyPath+'/'+'wifiCSR.pem', "rb") as csr_file:
	    reqBody['csr'] = base64.b64encode(csr_file.read())
	data = json.dumps(reqBody)
	
	print "submitting CSR"
	devlog("Submitting CSR")

	# Sleeps are for demo visual effect. Can be removed.
	time.sleep(2)

	headers = {'content-type': 'application/json','authorization': csrt['token']}
	url = makeURL('device/cert')
	response = requests.post(url, data = data, headers = headers)
	if response.status_code != 200:
		display.add_message("HTTP Error: {}".format(response.http_status))
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

	if hasattr(reply, 'passphrase'):
		passphrase = reply['passphrase']
	else:
		passphrase = "whatever"

	print "configuring wpa_supplicant"
	wpa_add_subscriber(ssid, ca_cert, wifi_cert, wifi_cert, passphrase, 'micronets')
	devlog("Configuring WiFi")
	time.sleep(2)

	reqBody = {'deviceID': device['deviceID']}
	data = json.dumps(reqBody)
	url = makeURL('device/pair-complete')
	response = requests.post(url, data = data, headers = headers)
	if response.status_code != 200:
		display.add_message("error: {}".format(response.http_status))
		return

	display.add_message('Onboard Complete')
	restartWifi()

# Remove private key
def removeKey():
	deleteKey(keyName, keyPath)

def restartWifi():
	call("sudo ifconfig wlan0 down; sudo systemctl daemon-reload; sudo systemctl restart dhcpcd; sudo ifconfig wlan0 up", shell=True)

# Remove subscriber config
def resetDevice():
	wpa_reset()
	restartWifi()


def localDevlog(msg):
	print "message: {}".format(msg)

def localEndOnboard(msg):
	print "End Onboard: {}".format(msg)

if __name__ == '__main__':

	if len(sys.argv) > 1 and sys.argv[1] == 'reset':
		print "reset"
		resetDevice()
	else:
		print "Onboarding"
		newKey = len(sys.argv) > 1 and sys.argv[1] == 'newkey'
		onboardDevice(newKey, localEndOnboard, localDevlog)
