# ProtoDPP Gen 2 Device
This version of the device is not specific to DPP or the Medical Device use case. It supports both demos, selectable on the configuration screen.

## Hardware Overview
The device uses the following components:
- [Raspberry Pi 3B](https://www.adafruit.com/product/3055)
- [PiTFT Plus 320x480 screen](https://www.adafruit.com/product/1983)
- [Alfa AWUS036NHA USB Wifi adapter](https://www.amazon.com/gp/product/B004Y6MIXS/ref=ppx_yo_dt_b_asin_title_o09_s00?ie=UTF8&psc=1)
- [16GB MicroSD card](https://www.amazon.com/gp/product/B003WIRFDM/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1)
- [Adafruit clear/colored Raspberry Pi case](https://www.adafruit.com/product/2252)
- [PiTFT faceplate and buttons](https://www.adafruit.com/product/2807)
- [2.5mm x 15mm Nylon Standoff](https://www.amazon.com/gp/product/B014J1ZLD6/ref=ppx_yo_dt_b_asin_title_o07_s01?ie=UTF8&psc=1)
- [M2 x 6mm self tapping screws](https://www.amazon.com/gp/product/B0775ZKB2H/ref=ppx_yo_dt_b_asin_title_o05_s00?ie=UTF8&psc=1)
- [M3 x 10mm self tapping screws](https://www.amazon.com/gp/product/B07BTNDC6W/ref=ppx_yo_dt_b_asin_title_o09_s00?ie=UTF8&psc=1)
- 3D Printed Parts (see STL files in `/model` folder)

## Hardware Assembly
Sorry, no pictures or diagrams. It will make sense as you go. High level instructions:
- Attach printed base to bottom of the case. This is so we can attach the wifi circuit board and screw on the base cover.
- Hack the USB cable so it fits inside. This is tedius. We are trying to make the cable very small and remove all unnecessary bulk.
- Create an RF shield to minimize interference from/to the wifi adapter
- Wire the USB cable directly to the Pi circuit board
- Attach the wifi adapter to the bottom of the case
- Assemble Pi, Case, Base Cover and screen, and give the top right corner of the screen support when pressing buttons.
- Snap on the Faceplate

Detailed instructions:
- Print (1) each of the STL files in the `model` folder.
- Use 5 minute epoxy to glue the Pi Base part to the bottom of the Pi case.
- Open Alfa adapter plastic case and remove circuit card.
- Modify the Alfa USB cable:
  - Remove all but 5" of cable with the Mini USB end.
  - Remove the jacket
  - Use an Xacto knife to surgically remove the plastic/metal housing of the Mini connector
  - Expose the conductor in the black wire using wire strippers, somewhere near the middle of the wire.
  - Wrap the cable using a thin strip of aluminum foil, touching the exposed conductor
  - Use heat shrink tubing to cover the aluminum foil.
  - (You have just re-shielded the cable)
- Take a piece of cardstock, cut to fit the inside bottom of the Pi case
  - Use aluminum foil tape to cover one side of the cardstock
  - (first insert the stripped end of a 2" wire between, so we can ground it later)
  - Solder the other end of the wire to a ground lug on the bottom of the Pi
- Solder the 4 USB wires to the bottom of the Pi (pick one of the USB ports)
  - Looking from the bottom of the Pi (USB connectors facing UP)
  - the wires will be Red, White, Green, Black - Left to Right
- Push the USB cable through the case, and the cardstock shield against the bottom of the case, aluminum side down (otherwise you will short out the Pi)
- Fasten the Alfa circuit board to the Pi Base using the (2) 2mm screws. Use the two holes closest to the USB connector.
- Carefully snap the Pi into the case
- Use a nylon standoff (threaded part cut off) and a nylon screw to provide support for the PiTFT screen. Use the hole above the top button. This is so when you push a button, the screen doesn't bend down.
- Press the PiTFT onto the Pi header.
- Add the faceplate buttons and snap the faceplate onto the case.
- Insert the USB plug to block the port that we soldered to.
- Insert the loaded SD card and power on

## Software Install
Use Apple-Pi Baker or other imaging tool to install the the [latest image](https://www.dropbox.com/sh/owq71q8ekyw6c2h/AAD61YqGNJ5nnmwlOQFPYC1Ra?dl=0)

To update the application software, use the `/install/upload` script, which will rsync the files to the specified host device.

## Configuration
After imaging the SD card, connect an ethernet cable and ssh in, using the ethernet IP address shown on the display. Credentials are `micronets/micronets`

- Edit `etc/hosts` and `etc/hostname` to change the host name.
- Edit `boot/config.txt` to change the resolution of the screen. This is useful if you wish to VNC in or connect an HDMI display to the Pi. When finished, change back to 320x240 for optimal display resolution for the PiTFT.
- Edit `etc/micronets/config/config.json` and add new `p256` and `key` attributes
  - `p256` is the private key hex string passed to `dpp_bootstrap_gen`
  - `key` is the public key returned from `dpp_bootstrap_gen`

## Operation
The four hardware buttons correspond to the four soft buttons on the right side of the screen.
- (1) Onboard/Cancel. Initiates the onboard process.
- (2) Cycle. Restarts Wifi to pick up new network Credentials
- (3) Config. Configuration screen
  - Mode: DPP or Clinic
  - Reset: Restore to default wifi network(s)
  - Reboot: Reboot system
  - Done: Exit Configuration
- (4) Shutdown. Click to restart python application, hold for shutdown.

## Nota Bene
- Use the screen configuration script `~/adafruit-pitft.sh` to change device parameters. This will overwrite your `/boot/config.txt` :(
  - Device type (resistive/capacitive/resolution)
  - 90 degrees rotation
  - NO to console output
  - YES to hdmi mirror mode
- Python application uses version 2.7
- Alfa adapter is recognized - no driver install required.
- The screen-off service only works with the resistive model to blank screen on shutdown
- Check out [sshfs](https://osxfuse.github.io/) to remotely mount your Pi filesystem. Great for using your favorite editor on your Mac.
- VNC also works great - set the Pi resolution to 1280x1024 (see above)
- In the installed SD card image, the onboard Wifi driver is disabled, so that the Alfa will be `wlan0`
- The application requires sudo privileges for certain operations. See the `sudoers` file for details.
- The autostart file for the application is located in ~/.config/autostart
- The application restart function in the app is effected by restarting the lightdm service.
- You can run the DPP demo without the iPhone (configurator agent) by clicking the QRCode. (must have a network connection). This simulates the scanning/forwarding of the QRCode by the configurator agent
