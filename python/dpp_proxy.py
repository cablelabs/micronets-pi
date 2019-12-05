# Test script to act as configurator (instead of iphone) by tapping on QRCode instead of scanning with iphone app
# Requires ethernet connection and the following additional attributes defined in config.json:
# dppProxy: {
#	msoPortalUrl: <url>,	
#   username: <username>,
#   password: <password>,
#	deviceModelUID: <uid>	# This is used as the mud file identifier, eg: AgoNDQcDDgg
#}

import json
import requests
import os, sys, time, traceback
from subprocess import call
from utils.syslogger import SysLogger


# Logfile is /tmp/protodpp.log
logger = SysLogger().logger()


def makeURL(host, path):
	url = "{}/portal/v1/dpp/{}".format(host, path)
	return url

def exec_dpp_onboard_proxy(config, mac, dpp_uri, display):

	logger.info("exec_dpp_onboard_proxy")

	session = requests.session()

	host = config.get(['dppProxy','msoPortalUrl'])
	username = config.get(['dppProxy','username'])
	password = config.get(['dppProxy','password'])
	model_uid = config.get(['dppProxy','deviceModelUID'])
	vendor_code = config.get('vendorCode')
	pubkey = config.get('key')
	role = "sta"

	# Login
	headers = {'content-type': 'application/json'}
	url = makeURL(host, 'login')

	logger.info("Login: " + url)

	reqBody = {'username': username, 'password': password}
	data = json.dumps(reqBody)
	logger.info("Body: "+ data)
	response = session.post(url, data = data, headers = headers)

	if response.status_code != 200 and response.status_code != 201:
		display.add_message("Login failed: {}".format(response.status_code))
		logger.error("Login failed: {}".format(response.status_code))
		return

	display.add_message("Login succeeded")

	# Check Session
	url = makeURL(host, 'session')

	logger.info("Session: " + url)

	response = session.get(url)

	if response.status_code != 200:
		display.add_message("Check session failed")
		return

	display.add_message("Session established")

	# Get MUD
	#curl -L "https://registry.micronets.in/mud/v1/mud-file/DAWG/MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgACDIBBiMf4W+tukQcNKz5eObkMp3tNPFJRvBhE1sop3K0="
	url = "https://registry.micronets.in/mud/v1/mud-file/{}/{}".format(vendor_code, pubkey)

	logger.info("MUD: " + url)

	response = session.get(url)

	if response.status_code != 200:
		display.add_message("Get MUD failed")
		return

	display.add_message("MUD file retrieved")
	reply = response.json()

	mfg_name = reply["ietf-mud:mud"]["mfg-name"]
	device_model = reply["ietf-mud:mud"]["model-name"]
	device_class = reply["ietf-mud:mud"]["ietf-mud-micronets:class-name"]
	device_type = reply["ietf-mud:mud"]["ietf-mud-micronets:type-name"]
	device_name = device_model

	# Onboard
	display.add_message("Begin Onboard")

	url = makeURL(host, 'onboard')

	logger.info("Onboard: " + url)

	headers = {'content-type': 'application/json'}

	reqBody = {"bootstrap":{}, "user":{}, "device":{}}
	reqBody["bootstrap"]["uri"] = dpp_uri
	reqBody["bootstrap"]["mac"] = mac
	reqBody["bootstrap"]["pubkey"] = pubkey
	reqBody["bootstrap"]["vendor"] = vendor_code
	reqBody["user"]["deviceRole"] = role
	reqBody["user"]["deviceName"] = device_name
	reqBody["device"]["class"] = device_class
	reqBody["device"]["type"] = device_type
	reqBody["device"]["model"] = device_model
	reqBody["device"]["modelUID"] = model_uid
	reqBody["device"]["manufacturer"] = mfg_name

	data = json.dumps(reqBody)

	logger.info("Onboard message: "+data)
	response = session.post(url, data = data, headers = headers)

	if response.status_code != 200 and response.status_code != 201:
		display.add_message("Onboard failed: {}".format(response.status_code))
		return

	display.add_message("Onboard initiated")

	# wait for status to accumulate
	#time.sleep(5)
	# status seems to be broken
'''
	url = makeURL(host, 'status')
	logger.info("Status: " + url)

	response = session.get(url)

	logger.info("status: {}".format(response.status_code))
	logger.info(response.json())

	if response.status_code != 200:
		display.add_message("Status failed")
		return 

	# Logout
	url = makeURL(host, 'logout')

	logger.info("Logout: " + url)

	response = session.post(url)

	if response.status_code != 200 and response.status_code != 204:
		display.add_message("Logout failed")
		return

	display.add_message("Logout succeeded")
'''

def dpp_onboard_proxy(config, mac, uri, display):
	try:
		exec_dpp_onboard_proxy(config, mac, uri, display)
	except Exception as e:
		display.add_message("!! {}".format(e.__doc__))
		logger.error(e.__doc__)
		logger.error(e.message)
		logger.error('-'*60)
        logger.error(traceback.print_exc())
        logger.error('-'*60)
