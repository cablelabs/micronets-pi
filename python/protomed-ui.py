import sys, time, argparse, logging, atexit, os
from subprocess import call
from utils.syslogger import SysLogger
from onboard import *
import threading
from threading import Timer
from Tkinter import *
from lib.wpa_supplicant import *
import PIL.Image
import PIL.ImageTk

window = Tk()
window.title("Protomed Simulator")


window.geometry("400x560")
window.resizable(0,0)

font1=("DejaVuSansMono-Bold", 20, 'bold')
font2=("DejaVuSansMono", 16, 'bold')

# Header
header = Label(window, text="Micronets", fg="white", bg="blue")
header.place(x=20, y=20, width=360, height=40)
header.config(font=font1)

# Header Icon
linkedIcon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', 'linked.png'))
im = PIL.Image.open(linkedIcon_path)
im = im.resize((24,24),PIL.Image.ANTIALIAS)
icon = PIL.ImageTk.PhotoImage(im)
linkedIcon = Label(window, image=icon)
linkedIcon.place(x=340, y=29, width=24, height=24)
linkedIcon['bg'] = header['bg']

# Progress window
messages = Text(window, wrap=WORD, background="white", borderwidth=2, relief="solid")
messages.place(x=20, y=60, width=360, height=280)

# Footer
footer = Label(window, text="IP: 10.252.232.112", fg="white", bg="green")
footer.place(x=20, y=340, width=360, height=40)
footer.config(font=font1)

# Footer Icon
wifiIcon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', '58-wifi.png'))
im2 = PIL.Image.open(wifiIcon_path)
im2 = im2.resize((24,24),PIL.Image.ANTIALIAS)
icon2 = PIL.ImageTk.PhotoImage(im2)
wifiIcon = Label(window, image=icon2)
wifiIcon.place(x=340, y=349, width=24, height=24)
wifiIcon['bg'] = footer['bg']

# Demented python scoping.
context = {'restoring':False, 'onboarding':False, 'showSSID':True}

def status_message(message):
    add_message(message)

def clear_messages():
    messages.delete('1.0', END)

def add_message(message):
    messages.insert(END, message + '\n')

def set_state():
    #if wpa_subscriber_exists():
    #    ledOnboard.on()
    #else:
    #    ledOnboard.off()
    return


def restore_defaults():
    print "restore defaults"
    clear_messages()
    add_message("Restore Defaults")

    #ledOnboard.blink(.05, 10, restore_complete)
    restoring = True
    resetDevice()

def restore_complete():
    print "end restore"
    display.add_message("Restore Complete")
    restoring = False
    set_state()

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
    #ledOnboard.blink(.1)
    context['onboarding'] = True
    onboard_button.config(text='Cancel')

    # Read clear private key switch
    #newKey = buttonMode.is_set()
    #print "newKey: {}".format(newKey)
    newKey = False
    thr = threading.Thread(target=onboardDevice, args=(newKey, end_onboard, status_message,)).start()

def onboard():
    print "onboard clicked"
    if context['onboarding']:
        clear_messages()
        add_message("Canceling..")
 
        thr = threading.Thread(target=cancelOnboard, args=(status_message,)).start()

    else: 
        begin_onboard()
        context['onboarding'] = True

def showLinked():
	linkedIcon.place(x=340, y=29, width=24, height=24)

def hideLinked():
	linkedIcon.place(x=-40, y=29, width=24, height=24)

def showWifi():
	wifiIcon.place(x=340, y=349, width=24, height=24)

def hideWifi():
	wifiIcon.place(x=-40, y=349, width=24, height=24)

def reset():
    print "wifi credentials reset"
    clear_messages()
    add_message("Restore Defaults")

    #ledOnboard.blink(.05, 10, restore_complete)
    #restoring = True
    resetDevice()
    add_message("Restore Complete")


def cycle():
    add_message("Cycling Wifi..")
    restartWifi()

def exit_app():
    print "exit"
    exit()

def get_ipaddress():
    fields = os.popen("ifconfig wlan0 | grep 'inet '").read().strip().split(" ")
    ipaddress = "NO IP ADDRESS"
    if len(fields) >= 2:
        ipaddress = fields[1]
    return ipaddress

def get_ssid():
    ssid = os.popen("iwconfig wlan0 | grep 'ESSID'| awk '{print $4}' | awk -F\\\" '{print $2}'").read().strip()
    return ssid

def render_banner():
    title = "Micronets"
    color = "blue"

    #self.linkedIcon = Image.open(self.linkedIcon_path).convert("RGBA")

    if wpa_subscriber_exists():
		wifiIcon_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'images', 'linked.png'))
		im = PIL.Image.open(wifiIcon_path)
		icon = PIL.ImageTk.PhotoImage(im)
		header.config(image=icon)



onboard_button = Button(window, text="Onboard", command=onboard)
onboard_button.place(x=20, y=400, width=170, height=60)
onboard_button.config(font=font2)

reset_button = Button(window, text="Reset", command=reset)
reset_button.place(x=210, y=400, width=170, height=60)
reset_button.config(font=font2)

cycle_button = Button(window, text="Cycle", command=cycle)
cycle_button.place(x=20, y=480, width=170, height=60)
cycle_button.config(font=font2)

exit_button = Button(window, text="Exit", command=exit_app)
exit_button.place(x=210, y=480, width=170, height=60)
exit_button.config(font=font2)

footer.config(text='')
hideLinked()
hideWifi()

def updateTimer():
    ssid = get_ssid()
    if (context['showSSID']):
        footer.config(text=ssid)
    else:
        footer.config(text=get_ipaddress())

    if (ssid == None or ssid == ""):
        hideWifi()
    else:
        showWifi()

    if wpa_subscriber_exists():
        showLinked()
    else:
        hideLinked()

    context['showSSID'] = not context['showSSID']
    window.after(4000,updateTimer)

updateTimer()


window.mainloop()