import sys, time, argparse, logging, atexit, os
import subprocess
from utils.syslogger import SysLogger
from onboard import *
import threading
from threading import Timer
from Tkinter import *
from lib.wpa_supplicant import *
import PIL.Image
import PIL.ImageTk

'''
TODO:
 - interface is currently hard coded to wlan0
 - need wpa_adapter implemented to receive DPP state notifications - auth begin, auth complete, config begin, config complete, STA associated.
 - display above state changes in progress window
 - finish/test clinic mode
 - fix header/footer icons
'''

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
config = {}
onboard_active = False
default_key = "MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgACDIBBiMf4W+tukQcNKz5eObkMp3tNPFJRvBhE1sop3K0="
default_p256 = "30570201010420777fc55dc51e967c10ec051b91d860b5f1e6c934e48d5daffef98d032c64b170a00a06082a8648ce3d030107a124032200020c804188c7f85beb6e91070d2b3e5e39b90ca77b4d3c5251bc1844d6ca29dcad"
default_vendor_code = "DAWG"
default_channel = 1
default_channel_class = 81
default_mode = "dpp"
default_countdown = 30
countdown = 0
canExit = False

chan_freqs = {1:2412, 2:2417, 3:2422, 4:2427, 5:2432, 6:2437, 7:2442, 8:2447, 9:2452, 10:2457, 11:2462, 12:2467, 13:2472, 14:2484}

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

def add_icon(parent, imagename, x, y, width, height):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', imagename))
    img = PIL.Image.open(path)
    img = img.resize((width, height),PIL.Image.ANTIALIAS)
    icon = PIL.ImageTk.PhotoImage(img)
    iconFrame = Label(window, image=icon)
    #iconFrame.place(x=x, y=y, width=width, height=height)
    place_widget(iconFrame, x, y, width, height)
    iconFrame['bg'] = parent['bg']
    iconFrame.saveicon = icon   # otherwise it disappears
    return iconFrame

# TODO: use this to "restart" application (DPP/clinic switch)
# sudo systemctl restart lightdm

w, h = window.winfo_screenwidth(), window.winfo_screenheight()
# use the next line if you also want to get rid of the titlebar
window.overrideredirect(1)
#window.geometry("320x240+300+300")
window.geometry("320x240+0+0")

font1=("HelveticaNeue-Light", 20, 'normal')
font2=("HelveticaNeue-Light", 16, 'normal')
font3=("HelveticaNeue-Light", 12, 'normal')

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
header = Label(window, text="MICRONETS", fg="white", bg="DodgerBlue4")
place_widget(header, 0, 0, full_w, banner_h)
header.config(font=font1)
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
    global settings_visible
    if settings_visible:
        settings.place_forget()
        show_widget(onboard_button)
        show_widget(refresh_button)
        show_widget(settings_button)
    else:
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

# Footer
footer_t = banner_h + main_h
footer = Label(window, text="IP: 10.252.232.112", fg="white", bg="gray20")
#footer.place(x=0, y=footer_t, width=full_w, height=banner_h)
place_widget(footer, 0, footer_t, full_w, banner_h)
footer.config(font=font1)

# Footer Icon
wifiIcon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', '58-wifi.png'))
im2 = PIL.Image.open(wifiIcon_path)
im2 = im2.resize((24,24),PIL.Image.ANTIALIAS)
icon2 = PIL.ImageTk.PhotoImage(im2)
wifiIcon = Label(window, image=icon2)
wifiIcon.place(x=icon_l, y=210, width=24, height=24)
wifiIcon['bg'] = footer['bg']

def display_qrcode(data):

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


def destroy_qrcode():
    hide_widget(qrcode_frame)
    hide_widget(qrcode_image)
    qrcode_image.place_forget()
    #qrcode_image = None

# Demented python scoping.
context = {'restoring':False, 'onboarding':False, 'showSSID':True}

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

    if config['mode'] == 'dpp':
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

def config_default(key, default):
    global config
    if not config.get(key):
        config[key] = default


def save_config():
    fileDir = os.path.dirname(os.path.realpath('__file__'))
    filename = os.path.join(fileDir, '../config/config.json')
    with open(filename, 'w') as outfile:  
        json.dump(config, outfile)

def load_config():
    global config
    fileDir = os.path.dirname(os.path.realpath('__file__'))

    try:
        filename = os.path.join(fileDir, '../config/config.json')
        fileData = open(filename).read()
        #print 'fileData: {}'.format(fileData)
        config = json.loads(fileData)

        print "config loaded OK"

    except (OSError, IOError, KeyError) as e: # FileNotFoundError does not exist on Python < 3.3
        pass
    
    # config defaults
    config_default('mode', 'dpp')
    config_default('key', default_key)
    config_default('p256', default_p256)
    config_default('vendorCode', default_vendor_code)
    config_default('channel', default_channel)
    config_default('channelClass', default_channel_class)
    config_default('countdown', default_countdown)

    # save defaults
    save_config()

def toggle_mode():
    global config
    if config['mode'] == 'dpp':
        config['mode'] = 'clinic'
    else:
        config['mode'] = 'dpp'

    update_mode()
    save_config()

def restore_defaults(null_arg=0):
    print "reset device.."
    clear_messages()
    add_message("reset device..")
    resetDevice(config['mode'] == 'dpp')

def get_ipaddress():
    fields = os.popen("ifconfig wlan0 | grep 'inet '").read().strip().split(" ")
    #fields = os.popen("ifconfig eth0 | grep 'inet '").read().strip().split(" ")
    ipaddress = "NO IP ADDRESS"
    if len(fields) >= 2:
        ipaddress = fields[1]
    return ipaddress

def get_ssid():
    ssid = os.popen("iwconfig wlan0 | grep 'ESSID'| awk '{print $4}' | awk -F\\\" '{print $2}'").read().strip()
    return ssid

def get_mac():
    mac = os.popen("cat /sys/class/net/wlan0/address").read().strip()
    return mac

def generate_dpp_uri():

    print "** generate_dpp_uri **"

    mac = os.popen("cat /sys/class/net/wlan0/address").read().strip()
    cmd = "sudo wpa_cli dpp_bootstrap_gen type=qrcode mac={} chan={}/{} key={} info={}".format(
        get_mac(),
        config['channelClass'],
        config['channel'],
        config['p256'],
        config['vendorCode'])

    print "cmd: " + cmd
    
    result = os.popen(cmd).read().strip()
    print result

    id = result.split('\n')[1]

    cmd = "sudo wpa_cli dpp_bootstrap_get_uri {}".format(id)
    result = os.popen(cmd).read().strip()

    uri = result.split('\n')[1]
    print "uri: " + uri

    return uri

def dpp_listen():
    print "** dpp_listen **"
    cmd = "sudo wpa_cli dpp_listen {}".format(chan_freqs[config['channel']])
    result = os.popen(cmd).read().strip()
    print result


def dpp_stop_listen():
    print "** dpp_stop_listen **"
    result = os.popen(cmd).read().strip()
    print result

def end_onboard(status):
    print "end onboard: {}".format(status)
    add_message(status)
    context['onboarding'] = False
    onboard_button.config(text='Onboard')

    set_state()

def begin_onboard():
    print "begin onboard"
    clear_messages()
    add_message("Begin Onboard")
    context['onboarding'] = True
    onboard_button.config(text='Cancel')
    newKey = False
    thr = threading.Thread(target=onboardDevice, args=(newKey, end_onboard, status_message,)).start()

def onboard_countdown():
    global countdown

    countdown = countdown -1
    if countdown == 0:
        cancel_onboard()
    else:
        countdown_button.config(text=countdown)
        countdown_timer = threading.Timer(1.0, onboard_countdown)
        countdown_timer.start()

def onboard_dpp():
    global countdown, countdown_timer
    # generate uri
    # display qrcode
    hide_widget(header)
    hide_widget(footer)
    hide_widget(mode_icon)
    hide_widget(onboard_button)
    hide_widget(refresh_button)
    hide_widget(settings_button)
    show_widget(cancel_button)
    show_widget(countdown_button)

    #data = "DPP:C:81/1;I:SUNG;M:6a:00:02:d2:e8:50;K:MDkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDIgACDIBBiMf4W+tukQcNKz5eObkMp3tNPFJRvBhE1sop3K0=;;"
    data = generate_dpp_uri()

    display_qrcode(data)

    # countdown TODO
    countdown = config["countdown"]
    countdown_button.config(text=countdown)

    countdown_timer = threading.Timer(1.0, onboard_countdown)
    countdown_timer.start()

def onboard_clinic():
    print "onboard clicked"
    if context['onboarding']:
        clear_messages()
        add_message("Canceling..")
 
        thr = threading.Thread(target=cancelOnboard, args=(status_message,)).start()

    else: 
        begin_onboard()
        context['onboarding'] = True

def cancel_onboard(null_arg=0):
    show_widget(header)
    show_widget(footer)
    show_widget(mode_icon)
    show_widget(onboard_button)
    show_widget(refresh_button)
    show_widget(settings_button)
    hide_widget(cancel_button)
    hide_widget(countdown_button)
    if config['mode'] == 'dpp':
        destroy_qrcode()
    if countdown_timer != None:
        countdown_timer.cancel()


def onboard(null_arg=0):
    global onboard_active

    if (onboard_active):
        cancel_onboard()
    else:
        if config['mode'] == "dpp":
            onboard_dpp()
        else:
            onboard_clinic()
    onboard_active = not onboard_active

def showLinked():
    linkedIcon.place(x=340, y=29, width=24, height=24)

def hideLinked():
    linkedIcon.place(x=-40, y=29, width=24, height=24)

def showWifi():
    wifiIcon.place(x=340, y=349, width=24, height=24)

def hideWifi():
    wifiIcon.place(x=-40, y=349, width=24, height=24)

def cycle(nullarg=0):
    add_message("Cycling Wifi..")
    thr = threading.Thread(target=restartWifi).start()

def reboot(nullarg=0):
    add_message("Rebooting..")
    subprocess.call("sudo reboot now", shell=True)

    #restartWifi()

def exit_app(nullarg=0):
    print "exit"
    exit()

# Timer fired.
def check_shutdown():
    global shutdown_timer, shutting_down
    shutdown_timer = None

    if (do_shutdown):
        print "shutting down"
        shutting_down = True
        subprocess.call("sudo shutdown -h now", shell=True)
        #subprocess.call(['poweroff'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def shutdown_pressed(nullarg=0):
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
            #subprocess.call("sudo systemctl restart lightdm")

            print os.popen("sudo systemctl restart lightdm")

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

load_config()
update_mode()

footer.config(text='')
#hideLinked()
#hideWifi()

def updateTimer():
    ssid = get_ssid()
    if (context['showSSID']):
        footer.config(text=ssid)
    else:
        footer.config(text=get_ipaddress())

    if (ssid == None or ssid == ""):
        hideWifi()
        showWifi()
    else:
        showWifi()

    if wpa_subscriber_exists():
        showLinked()
    else:
        hideLinked()
        showLinked()

    context['showSSID'] = not context['showSSID']
    window.after(4000,updateTimer)

    if time.time() - last_message_time > 30:
        clear_messages()


updateTimer()
 
# event handler to manage button presses
def buttonEvent(channel):
    startTime = time.time()
    while GPIO.input(channel) == GPIO.LOW:
        time.sleep(0.02)
    print "Button #%d pressed for %f seconds." % (channel, time.time() - startTime)
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

 
#try:
#    GPIO.wait_for_edge(17, GPIO.FALLING)
#    print "Exit button pressed."
# 
#except:
#    pass

# save screen, turn off backlight for now..
#toggle_backlight(0)
 
# exit gracefully
#backlight.stop()
#GPIO.cleanup()

# turn off cursor
window.config(cursor="none")

def enableExit():
    global canExit
    canExit  = True

t = threading.Timer(3.0, enableExit)
t.start()

window.mainloop()
