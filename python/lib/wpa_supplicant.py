#!/usr/bin/env python
# This module is used to configure wpa_supplicant. 

import os
import glob
import sys
import subprocess
from pathlib import Path

__all__ = ["wpa_reset", "wpa_add_subscriber", "wpa_subscriber_exists", "has_network"]

# exposed methods
def wpa_reset(all=False):
	# remove our credentials and configuration
	rm_silent('/etc/micronets/networks/subscriber/network.config')
	rm_silent('/etc/micronets/networks/subscriber/ca.pem')
	rm_silent('/etc/micronets/networks/subscriber/wifi_key')
	rm_silent('/etc/micronets/networks/subscriber/wifi.crt')

	# create initial wpa_supplicant.conf
	f = open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w')
	f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
	f.write("update_config=1\n")
	# Note: 'pmf=2' REQUIRES 'ieee80211w=1' for network {} stanzas
	f.write("pmf=2\n")
	f.write("dpp_config_processing=2\n")
	f.write('\n')

	f.close();

	# add default networks
	all = True
	if not all:
		add_network('hotspot', -1)
		add_network('default', -2)


def wpa_subscriber_exists():
	certFile = Path("/etc/micronets/networks/subscriber/wifi.crt")
	return certFile.is_file()
	
def wpa_add_subscriber(ssid, ca_cert, wifi_cert, wifi_key, passphrase, identity):

	# Start with default configuration
	wpa_reset()

	# Generate subscriber's network configuration file
	with open('/etc/micronets/networks/subscriber/network.config', 'w') as f:
		f.write('ssid="' + ssid + '"\n')
		f.write('scan_ssid=1\n')
		f.write('key_mgmt=WPA-EAP\n')
		f.write('group=CCMP TKIP\n')
		f.write('eap=TLS\n')
		f.write('identity="' + identity + '"\n')
		f.write('ca_cert="/etc/micronets/networks/subscriber/ca.pem"\n')
		f.write('client_cert="/etc/micronets/networks/subscriber/wifi.crt"\n')
		f.write('private_key="/etc/micronets/networks/subscriber/wifi.crt"\n')
		f.write('private_key_passwd="' + passphrase + '"\n')

		f.close()

	# Save keys and certs
	with open('/etc/micronets/networks/subscriber/ca.pem', 'wb') as f:
	    f.write(ca_cert)
	with open('/etc/micronets/networks/subscriber/wifi.crt', 'wb') as f:
	    f.write(wifi_cert)
	with open('/etc/micronets/networks/subscriber/wifi_key', 'wb') as f:
	    f.write(wifi_key)

	# add subscriber network
	add_network('subscriber', 10)


def rm_silent(filename):
	try:
	    os.remove(filename)
	except OSError:
		#print 'failed to remove file: {}'.format(filename)
		pass

def add_network(network, priority):

	infile = '/etc/micronets/networks/'+network+'/network.config'
	outfile = '/etc/wpa_supplicant/wpa_supplicant.conf'

	with open(outfile, 'a') as fout, open(infile, 'r') as fin:
		fout.write('')
		fout.write('network={\n')
		fout.write('    priority={}\n'.format(priority))

		for line in fin:
			fout.write('    {}'.format(line))

		fout.write('}\n')

# used only to see if a STA has been configured, for display purposes. Probably a better way.
def has_network():
	infile = '/etc/wpa_supplicant/wpa_supplicant.conf'

	with open(infile, 'r') as fin:
		for line in fin:
			line = line.replace(" ","")
			if "network=" in line:
				return True

	return False

if __name__ == '__main__':

	if len(sys.argv) > 1 and sys.argv[1] == 'reset':
		print "reset"
		wpa_reset()
	else:
		print "add"
		wpa_add_subscriber("Grandma's WiFi", "ca certificate", "wifi certificate", "wifi key", "micronets")

	print "\n"
	print "wpa_supplicant.conf:\n"
	with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'r') as fin:
		#for line in fin:
		#	sys.stdout.write(line)
		print fin.read()

	print "/networks/subscriber:\n"
	print os.listdir('/etc/micronets/networks/subscriber')



# TODO Need to restart after adding subscriber or resetting to defaults so it will connect to the new network (for demo)

#sudo systemctl daemon-reload
#sudo systemctl restart dhcpcd

# Or maybe just power cycle.


