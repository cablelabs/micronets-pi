# Protomed Device Installation and Configuration

This code runs on a Raspberry Pi Zero Wifi, with the following components attached:

 - TFT 128x128 display
 - Power Switch
 - Function Switch (advertise/cancel)
 - Power LED
 - Function LED (Slow blink = Onboarding in progress, Fast blink = Reset in progress, On = Onboarded, Off = Reset )
 - Reset Switch - Removes subscriber credentials and reconfigures wpa-supplicant to only connect to default network (clinic)
 - Mode Switch - Determines if a new key pair & UID be created each time device is advertised/onboarded
 - Battery - Will last around an hour I think. 
 - Charge circuit - Allows for running on power adapter and charging battery

 [User Manual](https://github.com/cablelabs/micronets-pi/wiki/ProtoMed-User-Manual)

Note: THIS APPLICATION REQUIRES PYTHON 2.7!!

 ## TODO: 
 - Implement LBO GPIO so Pi will turn off below 3.2V
 - Add low battery LED to case

## Repository Layout
 - config - Device information used to advertise device
 - install - Upload script and init.d startup script
 - networks - Wifi configuration folders/files, one set each for default (clinic) and subscriber
 - python - Source code
 	- lib - Cryptography and wpa-supplicant modules
 	- pio - I/O modules for Raspberry Pi
 	- utils - Utility code
 - ssh - placeholder for device folder to contain certs and keys

## Device File System
The install location is `/etc/micronets`

 - config - Device information used to advertise device
 - networks - Wifi configuration folders/files, one set each for default (clinic) and subscriber
 - python - Source code
 - ssh - certs and keys

The only protomed specific file that is installed outside of /etc/micronets is the startup script:

`/etc/init.d/protomed`

## System Installation
Starting from a bare Raspbian installation, here is an edited history file detailing package installation:
(It is likely that some pieces have escaped my history and therefore missing)


	sudo apt-get install vim
	sudo apt-get update
	### Add a priviledged account with sudo ()
	sudo groupadd micronets
	sudo usermod -a -G micronets <username>
	sudo usermod -a -G micronets pi
	sudo apt-get install python-dev python-pip
	sudo pip install --upgrade distribute
	sudo pip install ipython
	sudo pip install --upgrade RPi.GPIO
	### add ssh certificate for ssh login
	sudo apt-get install wpa_supplicant
	### install luma display drivers: https://luma-lcd.readthedocs.io/en/latest/
	### install protomed application (elsewhere in this document)
	sudo update-rc.d protomed defaults
	sudo reboot


## Protomed Application Installation
Once the system is setup and you have ssh working, run `./install/upload <host>`. 
This should copy the required files to `/etc/micronets`. You might have to create this folder first. 
It will also copy the startup script to `/etc/init.d`

## Operation
- You may have to edit `config/thisRegistration.json` and change the url if the server base url is not `https://demo.alpineseniorcare.com/micronets2`
- On first run, if `config/thisRegistration.json` does not exist, it is created by copying `config/registration.json`
- Navigate a browser window to `https://alpineseniorcare.com/micronets2/portal/device-list`
- Power on the device (make sure battery has a good charge)
	- Ensure red slide switch (master on/off) on side is in the on position (towards the display)
	- Momentarily press the RED button to power on the device. It will take a few minutes for the display to come on.
- Click the GREEN button. 
	- Green LED should flash slowly
	- Device should appear in browser
- If you click the GREEN button again, it will cancel the onboarding and the device will disappear from the browser.
- Otherwise, click the device in the browser
	- You will be redirected to the MSO authentication server
	- Scan the QRCode if you have the iPhone or just click on the QRCode
	- Pairing should complete and the green LED should remain lit.
- To 'un-onboard', click the black recessed reset button on the side of the device. 
	- Green LED should flash rapidly for a second, then remain off. Certs and wpa_supplicant have been reset
- The recessed black slide switch on the side of the device is the mode switch. 
	- When active, a new device key/UID is generated each time. Otherwise the key/UID is reused. 
	- TODO: Indicator on display
- Power off the unit by momentarily pressing the RED button. This does an orderly shutdown of the Raspberry Pi so that the SD card does not become corrupted.
- Lock the device off by sliding the red switch on the side down (away from the display).
- To cycle the wifi connection and restart the python script, press the green and red buttons at the same time (press green first, and release red last). This is way faster than powering off/on the device.

## Troubleshooting
Log file: `/tmp/protomed.log`

### Default Network
There should always be the following files present for the default (clinic) network in `/etc/micronets/networks/default`:
 - network.config
If the default network uses WPA Enterprise certificates, there should also be certs etc in this folder.

### Onboarded Device
An onboarded device will have a `/etc/wpa_supplicant/wpa_supplicant.conf` file that looks like this:

ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

# hot spot on mobile phone - backup clinic wifi for demos while traveling
network={
    priority=1
    ssid="micronets-hs"
    psk="secblanket"
    key_mgmt=WPA-PSK
}
# clinic wifi
network={
    priority=0
    ssid="visitors"
    psk="rockymountain"
    key_mgmt=WPA-PSK
}
# subscriber wifi
network={
    priority=10
    ssid="auntbetty-gw"
    scan_ssid=1
    key_mgmt=WPA-EAP
    group=CCMP TKIP
    eap=TLS
    identity="micronets"
    ca_cert="/etc/micronets/networks/subscriber/ca.pem"
    client_cert="/etc/micronets/networks/subscriber/wifi.crt"
    private_key="/etc/micronets/networks/subscriber/wifi.crt"
    private_key_passwd="whatever"
}

There should also be these files in `/etc/micronets/networks/subscriber`:

 - ca.pem
 - network.config
 - wifi.crt
 - wifi_key

When the device is advertised, the key and CSR files should be created here:  `/etc/micronets/ssh`:

 - wifiCSR.pem
 - wifiKey
 - wifiKey.pub

### Reset Device
A reset device will have a `/etc/wpa_supplicant/wpa_supplicant.conf` file that looks like this:

	ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
	update_config=1

	network={
	    priority=0
	    ssid="visitors"
	    psk="rockymountain"
	    key_mgmt=WPA-PSK
	}

There should be no files in `/etc/micronets/networks/subscriber`

## Standalone Testing
You can test the onboarding sequence without an actual ProtoMed device. 
- Clone an SD card from an existing device or install platform from scratch on a Raspberry Pi Zero W.
- Install latest software onto the Pi Zero from this repository. `./install/upload <host>`
- From the python folder: `sudo python onboard.py`




