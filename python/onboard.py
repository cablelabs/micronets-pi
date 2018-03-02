#!/usr/bin/env python
import json
import requests
from pprint import pprint
from OpenSSL import crypto, SSL
import os
import base64

from utils.eccKeys import *
from utils.wpa-supplicant import *

# Advertise our device
data = open('data/device.json').read()
headers = {'content-type': 'application/json'}
response = requests.post('https://alpineseniorcare.com/micronets/device/advertise', data = data, headers = headers)

device = json.loads(data)
csrt = response.json()

print 'CSRT keyType {0}'.format(csrt['csrTemplate']['keyType'])

# TODO: keyType and keyBits should be separated in CSRT, and CSRT should include C, ST, L, O, OU, etc
keySpec = csrt['csrTemplate']['keyType'].split(":")

# TODO: Check for key reset in CSRT. If set, delete our private key, will test for and generate later
# This is a switch that we can set on the server via REST command

# Default to RSA, allow DSA. TODO: Need library that supports ECC
#keyType = crypto.TYPE_DSA if keySpec[0] == "DSA" else crypto.TYPE_RSA
#keyBits = kepSpec[0]

#Country = "US"
#State = "Colorado"

keyPath = './ssh'
if not os.path.exists(keyPath):
    os.makedirs(keyPath)

# Generate key pair
private_key = generateKey("wifiKey", keyPath)
public_key = private_key.public_key()

# TODO: Generate device_id using sha256 of public key and store it in ../config/device.meta

# Generate a CSR
csr = generateCSR(private_key, "wifiCSR", keyPath)

# Create the submit message
reqBody = {'UID': device['UID']}
with open(keyPath+'/'+'wifiCSR.pem', "rb") as csr_file:
    reqBody['csr'] = base64.b64encode(csr_file.read())
data = json.dumps(reqBody)
#print json_data

headers = {'content-type': 'application/json','authorization': csrt['token']}
response = requests.post('https://alpineseniorcare.com/micronets/device/cert', data = data, headers = headers)

print response.json()

reqBody = {'UID': device['UID']}
data = json.dumps(reqBody)
#print json_data

response = requests.post('https://alpineseniorcare.com/micronets/device/pair-complete', data = data, headers = headers)
