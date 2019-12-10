import sys, time, argparse, atexit, os
import logging
import datetime
import subprocess
from utils.syslogger import SysLogger
from onboard import *
import threading
from threading import Timer
from Tkinter import *
from lib.wpa_supplicant import *
import PIL.Image
import PIL.ImageTk
#import PIL.ImageGrab
import pyscreenshot as ImageGrab
from dpp_proxy import *
from proto_config import Config

'''
TODO:
 - interface is currently hard coded to wlan0
 - need wpa_adapter implemented to receive DPP state notifications - auth begin, auth complete, config begin, config complete, STA associated.
 - display above state changes in progress window
 - finish/test clinic mode
 - fix header/footer icon
 - keys should be moved out of config.json - someplace like 
'''

# Logfile is /tmp/protodpp.log
logger = SysLogger().logger()

# Config file
config = Config()

# This is just so onboard.py has an object with add_message.
class DisplayWrapper(object):

    def __init__(self):
        pass

    def add_message(self, message):
        add_message(message)

display = DisplayWrapper()

import qrcode
import json

import RPi.GPIO as GPIO

#time.sleep(2.0)

class Placement:
  def __init__(self, x, y, width, height):
    self.x = x
    self.y = y
    self.width = width
    self.height = height

placements = {}

window = Tk()
window.title("ProtoDPP")

DISP_SSID = 0
DISP_WIFI_IP = 1
DISP_ETHERNET_IP = 2

full_w = 320
full_h = 240
main_w = 280
main_h = 160
banner_h = 40
icon_l = 282
icon_t = banner_h + 2
iconframe_size = 40
icon_size = 36
do_shutdown = False
shutting_down = False
shutdown_timer = None
last_message_time = 0.0
mode_icon = None
mode_label = None
reset_label = None
settings = None
settings_visible = False
onboard_button = None
refresh_button = None
settings_button = None
shutdown_button = None
qrcode_frame = None
qrcode_image = None
#config = {}
onboard_active = False
qrcode_data = None
demo_mode = False
demo_status = None
demo_ssid = None
demo_wifi_ip = None
connected_frame = None
not_connected_frame = None
frame_count = 0
splash_image = None
fireworks_image = None

countdown = 0
canExit = False

animation_frames = None

chan_freqs = {1:2412, 2:2417, 3:2422, 4:2427, 5:2432, 6:2437, 7:2442, 8:2447, 9:2452, 10:2457, 11:2462, 12:2467, 13:2472, 14:2484}

# New fireworks splash for comcast, displayed after connect.
demo_frame = None
splash_frame = None
splash_active = False

############################################################################
# list of BCM channels from RPO.GPIO (printed on the Adafruit PCB next to each button)
channel_list = [17, 22, 23, 27]
backlightOn = True

# initialize GPIO library
GPIO.setmode(GPIO.BCM)
GPIO.setup(channel_list, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.OUT)
backlight = GPIO.PWM(18, 1000)
backlight.start(100)

def place_widget(widget, x, y, width, height, show=True):
    placements[widget] = Placement(x, y, width, height)
    if show:
        show_widget(widget)

def show_widget(widget):
    p = placements[widget]
    widget.place(x=p.x, y=p.y, width=p.width, height=p.height)

def hide_widget(widget):
    widget.place_forget()

def add_button(index, imagename, callback, callback2=None):
    top = icon_t + (index * iconframe_size)
    image = None
    icon = None
    if imagename != None:
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', imagename))
        img = PIL.Image.open(icon_path)
        img = img.resize((icon_size,icon_size),PIL.Image.ANTIALIAS)
        icon = PIL.ImageTk.PhotoImage(img)
        button = Label(window, image=icon)
    else:
        button = Label(window)

    button.bind("<Button-1>",callback)
    if callback2 != None:
        button.bind("<ButtonRelease-1>",callback2)
    place_widget(button, icon_l, top, icon_size, icon_size)
    button['bg'] = window['bg']
    button.saveicon = icon   # otherwise it disappears
    return button

def add_icon(parent, imagename, x, y, width, height, show=True):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', imagename))
    img = PIL.Image.open(path)
    img = img.resize((width, height),PIL.Image.ANTIALIAS)
    icon = PIL.ImageTk.PhotoImage(img)
    iconFrame = Label(window, image=icon)
    #iconFrame.place(x=x, y=y, width=width, height=height)
    place_widget(iconFrame, x, y, width, height, show)
    iconFrame['bg'] = parent['bg']
    iconFrame.saveicon = icon   # otherwise it disappears
    return iconFrame

# TODO: use this to "restart" application (DPP/clinic switch)
# sudo systemctl restart lightdm

w, h = window.winfo_screenwidth(), window.winfo_screenheight()
# use the next line if you also want to get rid of the titlebar

# if we are running with an external hdmi monitor (i.e. full screen resolution), offset the application window
# so we can see the title bar.

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

logger.info("Screen: "+str(screen_width) + " x " + str(screen_height))

main_x = 0
main_y = 0

if screen_width >= 640 and screen_height >= 480:

    # External monitor/VNC
    main_x = 40
    main_y = 40
else:
    window.config(cursor="none")
    window.overrideredirect(1)


window.geometry("320x240+" + str(main_x) + "+" +str(main_y))

font1=("HelveticaNeue-Light", 20, 'normal')
font2=("HelveticaNeue-Light", 16, 'normal')
font3=("HelveticaNeue-Light", 12, 'normal')
font4=("HelveticaNeue-Light", 18, 'normal')

#Take a screenshot of application window
def take_screenshot(null_arg=0):

    # Screenshots directory
    screenshots_folder = '/etc/micronets/screenshots'
    if not os.path.exists(screenshots_folder):
        os.makedirs(screenshots_folder)

    # Filename
    filename = str(datetime.datetime.now()).split('.')[0].replace(':','.')+".jpg"
    filepath = screenshots_folder + "/" + filename

    screenshot = ImageGrab.grab(bbox=(main_x, main_y, main_x+320, main_y+240))
    screenshot.save(filepath)


# event handler to toggle the TFT backlight
def toggle_backlight(channel):
    global backlightOn
    if backlightOn:
        backlightOn = False
        backlight.start(0)
    else:
        backlightOn = True
        backlight.start(100)

# Header
if not config.get('comcast', False):
    header = Label(window, text="MICRONETS", fg="white", bg="DodgerBlue4")
    header.config(font=font1)
else:
    header = Label(window, text="  EASY CONNECT DEMO", fg="white", bg="DodgerBlue4")
    header.config(font=font2)

place_widget(header, 0, 0, full_w, banner_h)
header.bind("<Button-1>",toggle_backlight)

# Header Icon
linkedIcon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', 'linked.png'))
im = PIL.Image.open(linkedIcon_path)
im = im.resize((24,24),PIL.Image.ANTIALIAS)
icon = PIL.ImageTk.PhotoImage(im)
linkedIcon = Label(window, image=icon)
linkedIcon.place(x=icon_l, y=29, width=24, height=24)
linkedIcon['bg'] = header['bg']

# Progress window
messageFrame = Frame(window, background="white", borderwidth=2, relief="solid")
messageFrame.place(x=0, y=banner_h, width=main_w, height=main_h)

messages = Text(window, wrap=WORD, background="white", borderwidth=0, relief="solid")
messages.place(x=0, y=banner_h, width=main_w, height=main_h)

def toggle_settings(null_arg=0):

    # cancel any animation in progress
    cancel_animation()
    
    global settings_visible
    if settings_visible:
        settings.place_forget()
        show_widget(onboard_button)
        show_widget(refresh_button)
        show_widget(settings_button)
        if demo_mode:
            display_demo_status()
    else:
        hide_demo_status()
        settings.place(x=0, y=banner_h, width=main_w, height=main_h)
        hide_widget(onboard_button)
        hide_widget(refresh_button)
        hide_widget(settings_button)

    settings_visible = not settings_visible

# Settings window
settings = Frame(window, background="light goldenrod yellow", borderwidth=1, relief="solid")
place_widget(settings,0, banner_h, main_w, main_h, False)

# qrcode window
qrcode_frame = Frame(window, background="white", borderwidth=0, relief="solid")
place_widget(qrcode_frame,0, 0, main_w, full_h, False)

# fireworks window
demo_frame = Frame(window, background="white", borderwidth=0, relief="solid")
place_widget(demo_frame,0, banner_h, main_w, main_h, False)

# splash window
splash_frame = Frame(window, background="black", borderwidth=0, relief="solid")
place_widget(splash_frame,0, banner_h, main_w, main_h, True)

# demo status window
demo_status = Frame(window, background="white", borderwidth=0, relief="solid")
place_widget(demo_status,0, banner_h, main_w, main_h, False)

# demo status window icons
l = (main_w - 64) / 2
#t = ((full_h - 64) / 2) - 8
t = ((full_h - 64) / 2)

connected_icon = add_icon(demo_status, 'green-check.png', l, t, 64, 64, False)
not_connected_icon = add_icon(demo_status, 'no-connection.png', l, t, 64, 64, False)

ssid_label = Label(window, text="", fg="DodgerBlue4", bg="white")
#psk_label = Label(window, text="", fg="OrangeRed2", bg="white")

place_widget(ssid_label,4, t+64+10, main_w-8, 24, False)
#place_widget(ssid_label,4, t+64+8, main_w-8, 24, False)
#place_widget(psk_label,4, t+64+30, main_w-8, 24, False)

ssid_label['bg'] = demo_status['bg']

def demo_show_messages(null_arg=0):
    hide_widget(demo_status)
    hide_widget(demo_frame)
    hide_widget(not_connected_icon)
    hide_widget(connected_icon)
    hide_widget(ssid_label)
    #hide_widget(psk_label)


demo_status.bind("<Button-1>",demo_show_messages)
connected_icon.bind("<Button-1>",demo_show_messages)
not_connected_icon.bind("<Button-1>",demo_show_messages)

# Footer
footer_t = banner_h + main_h
footer = Label(window, text="", fg="white", bg="gray20")
#footer.place(x=0, y=footer_t, width=full_w, height=banner_h)
place_widget(footer, 0, footer_t, full_w, banner_h)
#ooter.config(font=font1)
footer.config(font=font2)

# Footer Icon
wifiIcon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', '58-wifi.png'))
im2 = PIL.Image.open(wifiIcon_path)
im2 = im2.resize((24,24),PIL.Image.ANTIALIAS)
icon2 = PIL.ImageTk.PhotoImage(im2)
wifiIcon = Label(window, image=icon2)
wifiIcon.place(x=icon_l, y=210, width=24, height=24)
wifiIcon['bg'] = footer['bg']

def get_mac():
    mac = os.popen("cat /sys/class/net/wlan0/address").read().strip()
    return mac

def destroy_qrcode():
    hide_widget(qrcode_frame)
    hide_widget(qrcode_image)
    qrcode_image.place_forget()

def hide_demo_status():
    hide_widget(demo_status)
    hide_widget(demo_frame)
    hide_widget(not_connected_icon)
    hide_widget(connected_icon)
    hide_widget(ssid_label)    

def clicked_qrcode(null_arg=0):

    logger.info("clicked qrcode")

    # hide qrcode so we can see progress messages
    destroy_qrcode()
    if demo_mode:
        demo_show_messages()

    clear_messages()
    add_message("Clicked QRCode")
    
    # ensure we are connected to a network (wifi or ethernet)
    if get_wifi_ipaddress() or get_ethernet_ipaddress():
        # execute proxy script (simulates iphone scanning qrcode)
        thr = threading.Thread(target=dpp_onboard_proxy, args=(config, get_mac(), qrcode_data, display,)).start()
    else:
        add_message("Network connection required")

def cancel_splash(null_arg=0):
    global frame_count
    frame_count = 0
    display_demo_status()

def cancel_fireworks(null_arg=0):
    global frame_count
    frame_count = 0

def preload_fireworks():

    global animation_frames

    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', 'fireworks320-01.gif'))

    gif = PIL.Image.open(file_path, 'r')
    animation_frames = []

    frame_interval = .05
    fireworks_duration = config.get('onboardAnimationSeconds', 5)
    frame_count = int(fireworks_duration / frame_interval)

    try:
        i = 0
        while i < frame_count:
            i += 1
            animation_frames.append(gif.copy())
            gif.seek(len(animation_frames))
    except EOFError:
        pass

def animate_fireworks():

    frame_interval = .05

    global demo_ssid, demo_wifi_ip, animation_frames

    # prepare frame to receive images
    fireworks_image = Label(window, bg = 'black')
    place_widget(fireworks_image,0, banner_h, main_w, main_h)
    fireworks_image['bg'] = demo_frame['bg']
    show_widget(demo_frame)
    
    # allow canceling of the animation by touching the image
    fireworks_image.bind("<Button-1>", cancel_fireworks)

    hide_widget(splash_frame)
    # animate frames
    frame_count = len(animation_frames)
    i = 0
    while i < frame_count:
    #for frame in frames:
        frame = animation_frames[i]
        photo = PIL.ImageTk.PhotoImage(frame)
        fireworks_image.config(image=photo)
        fireworks_image.image = photo # prevent from being garbage collected while active
        time.sleep(frame_interval)
        i += 1

    # clean up
    photo = None

    hide_widget(fireworks_image)
    #hide_widget(demo_frame)

    if fireworks_image:
        fireworks_image.config(image=None)
        fireworks_image.image = None
        fireworks_image['bg'] = None


    add_connected_messages()
    display_demo_status()

def add_connected_messages():

    clear_messages()

    add_message("")
    add_message("")
    add_message("-- Connection Succeeded! --")
    add_message("")
    add_message("   SSID: "+ get_ssid())
    add_message("")
    add_message("   PASS: "+ get_ssid_psk(get_ssid()))
    add_message("")
    add_message("   ADDR: "+ get_wifi_ipaddress())

def animate_splash():

    global frame_count

    splash_active = True

    frame_interval = .05
    splash_duration = config.get('splashAnimationSeconds', 10)
    splash_minimum = 5
    frame_count = int(splash_duration / frame_interval)
    min_frame_count = int(splash_minimum / frame_interval)

    logger.info("Frame count: "+str(frame_count))


    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', 'earth5.gif'))

    gif = PIL.Image.open(file_path, 'r')
    frames = []
    try:
        while 1:
            frame = gif.copy()        
            frame = frame.resize((160, 160), PIL.Image.ANTIALIAS) #The (250, 250) is (height, width)
            frames.append(frame)
            gif.seek(len(frames))
    except EOFError:
        pass

    # prepare frame to receive images
    splash_image = Label(window, bg = 'black')
    place_widget(splash_image,0, banner_h, main_w, main_h)
    splash_image['bg'] = splash_frame['bg']
    show_widget(splash_frame)

    # allow canceling of the animation by touching the image
    splash_image.bind("<Button-1>", cancel_splash)

    # animate frames
    i = 0
    ethernet_displayed = False
    #ethernet_displayed = True

    wifi_ssid = None
    wifi_ip = None

    while i <= frame_count:
        index = i % len(frames)
        photo = PIL.ImageTk.PhotoImage(frames[index])
        splash_image.config(image=photo)
        splash_image.image = photo # prevent from being garbage collected while active
        time.sleep(frame_interval)
        i += 1
        #header.config(text=str(i))

        # display ethernet address when starting up, if connected.
        if not ethernet_displayed:
            ethernet_ip = get_ethernet_ipaddress()
            if (ethernet_ip):
                footer.config(text="ETH: "+ ethernet_ip)
                ethernet_displayed = True

        # check for wifi connected
        if not wifi_ssid:
            wifi_ssid = get_ssid()
        elif not wifi_ip:
            wifi_ip = get_wifi_ipaddress()
        else:
            # we're connected and online.
            if i > min_frame_count:
                # end animation
                frame_count = 0
                display_demo_status()
                add_connected_messages()

        if i == frame_count:
            # end of animation and not connected
            if not has_network():
                add_message("Not provisioned.")                
            elif not get_ssid():
                clear_messages()
                add_message("Not associated:")
                stanza = get_network_stanza()
                for line in stanza:
                    line = line.replace("\n", "").replace("\t","  ")
                    if len(line) > 35:
                        line = line[:35]+'...'
                    add_message(line)
            else:
                add_message("Associated: "+ get_ssid())
                if not get_wifi_ipaddress():
                    add_message("No IP address")
            display_demo_status()

    # clean up
    photo = None

    hide_widget(splash_image)
    hide_widget(splash_frame)
    #hide_widget(demo_frame)
    footer.config(text="")

    if splash_image:
        splash_image.config(image=None)
        splash_image.image = None
        splash_image['bg'] = None

    logger.info("Splash done")
    display_demo_status()

def display_fireworks():
    hide_demo_status()
    add_message("start fireworks")
    thr = threading.Thread(target=animate_fireworks, args=()).start()

def display_splash():
    thr = threading.Thread(target=animate_splash, args=()).start()

def display_qrcode(data):

    hide_widget(demo_status)
    hide_widget(not_connected_icon)
    hide_widget(connected_icon)


    # show parent
    show_widget(qrcode_frame)
    global qrcode_image

    #icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', 'dpp.png'))
    #image = PIL.Image.open(icon_path)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    image = image.resize((240,240),PIL.Image.ANTIALIAS)

    photo = PIL.ImageTk.PhotoImage(image)
    qrcode_image = Label(window, image=photo)
    place_widget(qrcode_image,20, 0, 240, full_h)

    qrcode_image['bg'] = qrcode_frame['bg']
    qrcode_image.saveicon = qrcode_image   # otherwise it disappears
    qrcode_image.savephoto = photo

    # add click handler to run onboard script(testing)
    qrcode_image.bind("<Button-1>", clicked_qrcode)


# Demented python scoping.
context = {'restoring':False, 'onboarding':False, 'net_display':DISP_SSID, 'comcast': True}

def status_message(message):
    add_message(message)

def clear_messages():
    messages.delete('1.0', END)

def add_message(message):
    global last_message_time
    last_message_time = time.time()
    messages.insert(END, " " + message + '\n')


def set_state():
    #if wpa_subscriber_exists():
    #    ledOnboard.on()
    #else:
    #    ledOnboard.off()
    return

def update_mode():
    global mode_icon

    if mode_icon:
        mode_icon.place_forget()

    if config.get('mode') == 'dpp':
        mode_icon = add_icon(header, 'dpp3.png', 4, 2, 36, 36)
        mode_label.config(text="DPP")
        reset_label.config(text="Delete WiFi Keys")
        header.config(bg="DodgerBlue4")
    else:
        mode_icon = add_icon(header, 'clinic2.png', 4, 2, 36, 36)
        mode_label.config(text="Clinic")
        reset_label.config(text="Default WiFi Keys")
        header.config(bg="teal")
    mode_icon['bg'] = header['bg']
    mode_icon.bind("<Button-1>",take_screenshot)

def toggle_mode():
    global config
    if config.get('mode') == 'dpp':
        config.set('mode','clinic')
    else:
        config.set('mode','dpp')

    update_mode()
    save_config()

def restore_defaults(null_arg=0):

    # cancel any animation in progress
    cancel_animation()
    
    logging.info("reset device..")

    clear_messages()
    add_message("reset device..")
    
    resetDevice(config.get('mode') == 'dpp')

def get_wifi_ipaddress():
    fields = os.popen("ifconfig wlan0 | grep 'inet '").read().strip().split(" ")
    ipaddress = None
    if len(fields) >= 2:
        ipaddress = fields[1]

    # !! testing
    #ipaddress = "192.168.123.456"

    return ipaddress

def get_ethernet_ipaddress():
    fields = os.popen("ifconfig eth0 | grep 'inet '").read().strip().split(" ")
    ipaddress = None
    if len(fields) >= 2:
        ipaddress = fields[1]
    return ipaddress



def get_ssid():
    ssid = os.popen("iwconfig wlan0 | grep 'ESSID'| awk '{print $4}' | awk -F\\\" '{print $2}'").read().strip()

    # !! testing
    #ssid = 'grandpa-gw'

    return ssid

def generate_dpp_uri():

    logger.info("** generate_dpp_uri **")

    mac = os.popen("cat /sys/class/net/wlan0/address").read().strip()
    cmd = "sudo wpa_cli dpp_bootstrap_gen type=qrcode mac={} chan={}/{} key={} info={}".format(
        get_mac(),
        config.get('channelClass'),
        config.get('channel'),
        config.get('p256'),
        config.get('vendorCode'))

    logger.info("cmd: " + cmd)
    
    result = os.popen(cmd).read().strip()
    logger.info(result)

    id = result.split('\n')[1]

    cmd = "sudo wpa_cli dpp_bootstrap_get_uri {}".format(id)
    result = os.popen(cmd).read().strip()

    uri = result.split('\n')[1]
    logger.info("uri: " + uri)

    return uri

def dpp_listen():
    logger.info("** dpp_listen **")
    cmd = "sudo wpa_cli dpp_listen {}".format(chan_freqs[config.get('channel')])
    result = os.popen(cmd).read().strip()
    logger.info(result)


def dpp_stop_listen():
    logger.info("** dpp_stop_listen **")
    cmd = "sudo wpa_cli dpp_stop_listen"
    result = os.popen(cmd).read().strip()
    logger.info(result)

def end_onboard(status):
    logger.info("end onboard: {}".format(status))
    add_message(status)
    context['onboarding'] = False
    onboard_button.config(text='Onboard')

    set_state()

def cancel_animation():
    global frame_count
    frame_count = 0

def display_demo_status():

    ssid = get_ssid()
    wifi_ip = get_wifi_ipaddress()
    is_provisioned = has_network()
    hide_widget(connected_icon)
    hide_widget(not_connected_icon)
    ssid_label.config(text="")

    footer.config(text="")

    if ssid:
        if not config.get('comcast'):
            ssid_label.config(text=ssid)
        else:
            ssid_label.config(text="CONNECTED")

        if wifi_ip:
            if not config.get('comcast'):
                footer.config(text=str(wifi_ip))
            show_widget(connected_icon)
        else:
            if not config.get('comcast'):
                footer.config(text="NO IP ADDRESS")
            show_widget(not_connected_icon)

    else:
        show_widget(not_connected_icon)
        #psk_label.config(text="")

        if is_provisioned:
            ssid_label.config(text="NOT CONNECTED")
        else:
            if config.get('comcast'):
                ssid_label.config(text="NOT CONNECTED")
            else:
                ssid_label.config(text="NOT PROVISIONED")

    show_widget(demo_frame)
    show_widget(demo_status)
    show_widget(ssid_label)
    #show_widget(psk_label)

def demo_restore_status(null_arg=0):
    if (demo_mode):
        display_demo_status()

messages.bind("<Button-1>",demo_restore_status)

def begin_onboard():
    logger.info("begin onboard")
    clear_messages()
    add_message("Begin Onboard")
    context['onboarding'] = True
    onboard_button.config(text='Cancel')
    newKey = False
    thr = threading.Thread(target=onboardDevice, args=(newKey, end_onboard, display,)).start()

def onboard_countdown():
    global countdown, demo_ssid, demo_wifi_ip, onboard_active

    countdown = countdown -1
    if countdown == 0:
        cancel_onboard()
        if demo_mode:
            destroy_qrcode()
            display_demo_status()
    else:

        if demo_mode:
            ssid = get_ssid()
            wifi_ip = get_wifi_ipaddress()

            if ssid and wifi_ip:
                # Success!
                #display_demo_status()
                hide_widget(not_connected_icon)
                hide_widget(connected_icon)
                hide_widget(ssid_label)
                show_widget(splash_frame)
                cancel_onboard()
                display_fireworks()
                return


        countdown_button.config(text=countdown)
        if onboard_active:
            countdown_timer = threading.Timer(1.0, onboard_countdown)
            countdown_timer.start()

def onboard_dpp():
    global countdown, countdown_timer, qrcode_data
    hide_widget(header)
    hide_widget(footer)
    hide_widget(mode_icon)
    hide_widget(onboard_button)
    hide_widget(refresh_button)
    hide_widget(settings_button)
    show_widget(cancel_button)
    show_widget(countdown_button)

    if demo_mode:

        # this is causing the logger to infinite loop

        '''
        try:
            cmd = "sudo wpa_cli disconnect"
            logger.info("cmd: " + cmd)
            
            result = os.popen(cmd).read().strip()
            logger.info(result)
            pass
        except Exception as e:
            #raise e
            pass
        '''
        wpa_reset(True)


    #if context['comcast']:
        # Ensure we start with 

    #data = "DPP:C:81/1;I:SUNG;M:6a:00:02:d2:e8:50;K:MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgACDIBBiMf4W+tukQcNKz5eObkMp3tNPFJRvBhE1sop3K0=;;"
    qrcode_data = generate_dpp_uri()

    display_qrcode(qrcode_data)

    dpp_listen()

    # countdown TODO
    countdown = config.get("countdown")
    countdown_button.config(text=countdown)

    countdown_timer = threading.Timer(1.0, onboard_countdown)
    countdown_timer.start()

def onboard_clinic():
    logger.info("onboard clicked")
    if context['onboarding']:
        clear_messages()
        add_message("Canceling..")
 
        thr = threading.Thread(target=cancelOnboard, args=(display,)).start()

    else: 
        begin_onboard()
        context['onboarding'] = True

def cancel_onboard(null_arg=0):
    global onboard_active

    show_widget(header)
    show_widget(footer)
    show_widget(mode_icon)
    show_widget(onboard_button)
    show_widget(refresh_button)
    show_widget(settings_button)
    hide_widget(cancel_button)
    hide_widget(countdown_button)
    if config.get('mode') == 'dpp':
        if qrcode_image:
            destroy_qrcode()
        dpp_stop_listen()
    if countdown_timer != None:
        countdown_timer.cancel()

    onboard_active = False


def onboard(null_arg=0):


    # cancel any animation in progress
    cancel_animation()
    
    global onboard_active

    if (onboard_active):
        cancel_onboard()
        if demo_mode:
            destroy_qrcode()
            display_demo_status()

    else:
        if config.get('mode') == "dpp":
            onboard_dpp()
        else:
            onboard_clinic()
        onboard_active = True

    #onboard_active = not onboard_active

def showLinked():
    linkedIcon.place(x=340, y=29, width=24, height=24)

def hideLinked():
    linkedIcon.place(x=-40, y=29, width=24, height=24)

def showWifi():
    wifiIcon.place(x=340, y=349, width=24, height=24)

def hideWifi():
    wifiIcon.place(x=-40, y=349, width=24, height=24)

def showConnected():

    pass

def hideConnected():
    pass

def showNotConnected():
    pass

def hideNotConnected():
    pass

def cycle(nullarg=0):

    # cancel any animation in progress
    cancel_animation()
    
    add_message("Cycling Wifi..")
    thr = threading.Thread(target=restartWifi).start()

def reboot(nullarg=0):
    add_message("Rebooting..")
    subprocess.call("sudo reboot now", shell=True)

    #restartWifi()

def exit_app(nullarg=0):
    logger.info("exit")
    if shutdown_timer != None:
        shutdown_timer.cancel()
    exit()

# Timer fired.
def check_shutdown():
    global shutdown_timer, shutting_down
    shutdown_timer = None

    if (do_shutdown):
        logger.info("shutting down")
        shutting_down = True
        subprocess.call("sudo shutdown -h now", shell=True)
        #subprocess.call(['poweroff'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def shutdown_pressed(nullarg=0):

    # cancel any animation in progress
    cancel_animation()

    global shutdown_timer, do_shutdown
    do_shutdown = True
    shutdown_timer = threading.Timer(3.0, check_shutdown)
    shutdown_timer.start()

def shutdown_released(nullarg=0):
    global shutdown_timer, do_shutdown, shutting_down

    do_shutdown = False
    if shutdown_timer != None:
        shutdown_timer.cancel()
    # replace with restart app after testing
    if not shutting_down:

        if canExit:
            add_message("Restarting Application..")
            #exit_app()
            logger.info("Restarting Application..")
            os.popen("sudo systemctl restart lightdm")

        # This restarts the desktop, which restarts the application.
        #add_message("Restarting Application..")
        #subprocess.call("sudo systemctl restart lightdm")
    

onboard_button = None
refresh_button = None
settings_button = None
shutdown_button = None

onboard_button = add_button(0, 'onboard2.png', onboard)
cancel_button = add_button(0, 'cancel.png', onboard)
countdown_button = add_button(0, None, onboard)
refresh_button = add_button(1, 'refresh.png', restore_defaults)
settings_button = add_button(2, 'settings2.png', toggle_settings)
shutdown_button = add_button(3, 'shutdown.png', shutdown_pressed, shutdown_released)

def shutdown_event(null_arg=0):

    # cancel any animation in progress
    cancel_animation()
    
    if GPIO.input(27):
        shutdown_released()
    else:
        shutdown_pressed()

hide_widget(cancel_button)
hide_widget(countdown_button)
countdown_button.config(font=font1)
#countdown_button.config('10')
countdown_button.config(fg="white")

# Fixed settings buttons
mode_button = Button(settings, text="Mode", command=toggle_mode)
mode_button.place(x=0, y=0, width=120, height=40)
mode_button.config(font=font2)

reset_button = Button(settings, text="Reset", command=restore_defaults)
reset_button.place(x=0, y=40, width=120, height=40)
reset_button.config(font=font2)

reboot_button = Button(settings, text="Reboot", command=reboot)
reboot_button.place(x=0, y=80, width=120, height=40)
reboot_button.config(font=font2)

done_button = Button(settings, text="Done", command=toggle_settings)
done_button.place(x=0, y=120, width=120, height=40)
done_button.config(font=font2)

mode_label = Label(settings, text="DPP", fg="black", bg="light goldenrod yellow")
mode_label.place(x=120, y=0, width=160, height=39)
mode_label.config(font=font3)

reset_label = Label(settings, text="Remove Wifi Keys", fg="black", bg="light goldenrod")
reset_label.place(x=120, y=40, width=160, height=39)
reset_label.config(font=font3)

reboot_label = Label(settings, text="Reboot System", fg="black", bg="light goldenrod yellow")
reboot_label.place(x=120, y=80, width=160, height=39)
reboot_label.config(font=font3)

done_label = Label(settings, text="Exit Settings", fg="black", bg="light goldenrod")
done_label.place(x=120, y=120, width=160, height=39)
done_label.config(font=font3)

mode_icon = add_icon(header, 'dpp3.png', 4, 2, 36, 36)
mode_icon.bind("<Button-1>",take_screenshot)

#load_config()
update_mode()


if config.get('demo', True) and config.get('mode') == 'dpp':
    demo_mode = True

if demo_mode:
    logger.info("demo mode")
    show_widget(demo_frame)

    preload_fireworks()
    display_splash()

footer.config(text='')
hideLinked()
hideWifi()

# setup for screenshots
def keypress(e):
    logger.info("KeyPress: "+e.char)
    if e.char == 's':
        take_screenshot()

window.bind('<KeyPress>', keypress)

def updateTimer():

    if not demo_mode:
        ssid = get_ssid()
        wifi_ip = get_wifi_ipaddress()
        ethernet_ip = get_ethernet_ipaddress()

        if (context['net_display'] == DISP_SSID):
            footer.config(text=ssid)
            context['net_display'] = DISP_WIFI_IP
        elif (context['net_display'] == DISP_WIFI_IP):
            if (wifi_ip):
                footer.config(text=wifi_ip)
            else:
                footer.config(text="NO IP ADDRESS")
            context['net_display'] = DISP_ETHERNET_IP
        else:
            # We use a wired connection for debug/testing (and for using the configurator proxy (dpp_proxy.py))
            if (ethernet_ip):
                footer.config(text="ETH: "+ ethernet_ip)
                context['net_display'] = DISP_SSID
            else:
                # Skip ahead to SSID
                footer.config(text=ssid)
                context['net_display'] = DISP_WIFI_IP

        if (ssid == None or ssid == ""):
            hideWifi()
            #showWifi()
        else:
            showWifi()
    else:

        pass


    if wpa_subscriber_exists():
        showLinked()
    else:
        hideLinked()
        #showLinked()

    window.after(4000,updateTimer)

    if not config.get('comcast'):
        if time.time() - last_message_time > config.get('messageTimeoutSeconds'):
            clear_messages()


updateTimer()
 
# event handler to manage button presses
def buttonEvent(channel):
    startTime = time.time()
    while GPIO.input(channel) == GPIO.LOW:
        time.sleep(0.02)
    logger.info("Button #%d pressed for %f seconds." % (channel, time.time() - startTime))
    #add_message("Button {} pressed for {} seconds".format(channel, time.time() - startTime))
    add_message("button event")
 
# event handler to manage Pi shutdown
def poweroff(channel):
    startTime = time.time()
    while GPIO.input(channel) == GPIO.LOW:
        time.sleep(0.02)
    if (time.time() - startTime) > 2:
        subprocess.call(['poweroff'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  
GPIO.add_event_detect(17, GPIO.FALLING, callback=onboard, bouncetime=200)
GPIO.add_event_detect(22, GPIO.FALLING, callback=cycle, bouncetime=200)
GPIO.add_event_detect(23, GPIO.FALLING, callback=toggle_settings, bouncetime=200)
GPIO.add_event_detect(27, GPIO.BOTH, callback=shutdown_event, bouncetime=200)

# turn off cursor (ymmv, sometimes displays edit cursor)
#if not config.get('showCursor', False):
#    window.config(cursor="none")

def enableExit():
    global canExit
    canExit  = True

t = threading.Timer(3.0, enableExit)
t.start()

window.mainloop()
