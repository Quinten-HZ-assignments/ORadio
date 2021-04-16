#!/usr/bin/python

# Dail version Feb 26
# stripped version to reduce complexity
import csv
import subprocess
from datetime import datetime
from time import sleep
import os.path
from os import path
import requests
from gpiozero import DigitalInputDevice
from gpiozero import LED
from gpiozero import MCP3008
from statemachine import StateMachine, State

# client = MPDClient()
# client.timeout = 10
# client.idletimeout = None

PotVol = MCP3008(channel=0, clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=12)
led_green = LED(6)  # led colors reversed in this version
led_red = LED(13)  # On/off   ledred  on GPIO 26

Switch_sel1 = DigitalInputDevice(pin=4, pull_up=True, active_state=None, bounce_time=None, pin_factory=None)
Switch_sel2 = DigitalInputDevice(pin=27, pull_up=True, active_state=None, bounce_time=None, pin_factory=None)
Switch_sel3 = DigitalInputDevice(pin=22, pull_up=True, active_state=None, bounce_time=None, pin_factory=None)
Switch_sel4 = DigitalInputDevice(pin=5, pull_up=True, active_state=None, bounce_time=None, pin_factory=None)
Switch_onoff = DigitalInputDevice(pin=25, pull_up=True, active_state=None, bounce_time=None, pin_factory=None)

class Interaction:
    def __init__(self, time, button, device_state, volume_dial_position=None):
        self.time = time
        self.button = button
        self.volume_dial_position = volume_dial_position
        self.device_state = device_state

    @property
    def id(self):
        return self.time

    @property
    def name(self):
        return self.button

    @property
    def volume_dial(self):
        return self.volume_dial_position

    @property
    def state(self):
        return self.device_state


device_state = False

CurveExp = 1.2  # Volume curve exponent
VolumeMax = 50  # MDP maximum volume was 60, for Hifiberry up to 50
VolumeSetRaw_prev = -10.0  # startpoint range 0 - 1023

VolumeStart = 3  # Volume at 0 volume dial setting, not 0 as that may think radio is not on
VolumeSetRaw = [i for i in range(0, 1024)]
for i in VolumeSetRaw:
    VolumeSetRaw[i] = int(round(VolumeStart + ((VolumeMax - VolumeStart) * pow((i / 1023.0), CurveExp))))
#       print('i=',i,VolumeSetRaw[i])
# SelectMem = 1  # 1,2,3 is value of last  selected  channel
mpcError = False  # track mpc errors
offlineFlag = False  # when offline true, to trace offline mode


# Switch_onFlag = False # when Switched on via Switch_on is used  is set

# -----------State machine -----------------------------

class RadioStateMachine(StateMachine):
    off = State('off', initial=True)
    playPlayL1 = State('playPlayL1')
    playPlayL2 = State('playPlayL2')
    playPlayL3 = State('playPlayL3')
    playPlayL4 = State('playPlayL4')

    switchOff = off.from_(playPlayL1, playPlayL2, playPlayL3, playPlayL4) | off.to.itself()
    playL1 = playPlayL1.from_(off, playPlayL2, playPlayL3, playPlayL4) | playPlayL1.to.itself()
    playL2 = playPlayL2.from_(off, playPlayL1, playPlayL3, playPlayL4) | playPlayL2.to.itself()
    playL3 = playPlayL3.from_(off, playPlayL1, playPlayL2, playPlayL4) | playPlayL3.to.itself()
    playL4 = playPlayL4.from_(off, playPlayL1, playPlayL2, playPlayL3) | playPlayL4.to.itself()

    def on_enter_off(self):
        global PlayListStopFlag, PlayListName, offlineFlag
        parseToCsv(Interaction(datetime.now(), 'Device OFF', device_state))
        #        print('stop; off')
        led_green.off()
        #	vib_motor.blink(on_time=0.2,off_time=0.2,n=2,background=True)  #vib_motor 0.2 s on, 1 s off repeat 3, in background)
        PlayListName = 'stop'
        offlineFlag = False  # to make that the internet connection is checked
        PlayPlayList()
        subprocess.call(["mpc", "repeat", "-q", "off"])  # switch repeat off

    #	PlayListStopFlag = True

    def on_enter_playPlayL1(self):
        global PlayListStopFlag, PlayListName, offlineFlag  # print('play L1')
        parseToCsv(Interaction(datetime.now(), 'Sixties', device_state))
        led_green.on()
        #        vib_motor.blink(on_time=0.2,off_time=0.2,n=2,background=True)  #vib_motor 0.2 s on, 1 s off repeat 3, in background)
        #	Play_playlist("PlayList_1")
        #        PlayListStopName = 'PlayList_1'
        PlayListName = 'PlayList_1'
        offlineFlag = False  # to make that the internet connection is checked
        PlayPlayList()

    #        PlayListStopFlag = True

    def on_enter_playPlayL2(self):
        global PlayListStopFlag, PlayListName, offlineFlag
        parseToCsv(Interaction(datetime.now(), 'Nostalgia', device_state))
        #	print('play L2')
        led_green.on()
        #        vib_motor.blink(on_time=0.2,off_time=0.2,n=2,background=True)  #vib_motor 0.2 s on, 1 s off repeat 3, in background)
        #        Play_playlist("PlayList_2")
        PlayListName = 'PlayList_2'
        offlineFlag = False  # to make that the internet connection is checked
        PlayPlayList()

    #        PlayListStopFlag = True

    def on_enter_playPlayL3(self):
        global PlayListStopFlag, PlayListName, offlineFlag
        parseToCsv(Interaction(datetime.now(), 'Klassiek', device_state))
        #        print('play L3')
        led_green.on()
        #        vib_motor.blink(on_time=0.2,off_time=0.2,n=2,background=True)  #vib_motor 0.2 s on, 1 s off repeat 3, in background)
        #        Play_playlist("PlayList_3")
        PlayListName = 'PlayList_3'
        offlineFlag = False  # to make that the internet connection is checked
        PlayPlayList()

    #        PlayListStopFlag = True

    def on_enter_playPlayL4(self):
        global PlayListStopFlag, PlayListName, offlineFlag
        parseToCsv(Interaction(datetime.now(), 'Nederlands', device_state))
        #        print('play L4')
        led_green.on()
        #        vib_motor.blink(on_time=0.2,off_time=0.2,n=2,background=True)  #vib_motor 0.2 s on, 1 s off repeat 3, in background)
        #        Play_playlist("PlayList_4")
        PlayListName = 'PlayList_4'
        offlineFlag = False  # to make that the internet connection is checked
        PlayPlayList()


#        PlayListStopFlag = True

Radio_state = RadioStateMachine()


#

# ----------------------check internet connection --------------------------
def checkInternet():
    try:
        requests.get('https://www.google.com/', timeout=0.2).status_code
        print('connected')
        return True
    except:
        print('not connected')
        pass
        return False


# --------------------check status MPC  player--------------
def checkMPC():
    global PlayListName, mpcError
    output = subprocess.check_output(["mpc"])
    #        print ("type =", type(output), "output =", output)
    if ("ERROR" in output) and (not Radio_state.is_off):
        mpcError = True
        #               PlayListName = PlayListName + '_offline'
        print("mpc error, switch to offline", output)
        PlayPlayList()

    else:
        mpcError = False


# ------------------------Play PlayList----------------------------------
def PlayPlayList():
    global PlayListName, mpcError, offlineFlag
    #                print ("offlineFlag =" , offlineFlag)
    if ((checkInternet() == False or mpcError == True) and offlineFlag == False):  # make sure only 1 time offlin$
        PlayListName = PlayListName + '_offline'
        offlineFlag = True
    else:
        offlineFlag = False
    print("Playlist name =", PlayListName)
    subprocess.call(["mpc", "clear", "-q"])
    subprocess.call(["mpc", "load", "-q", PlayListName])
    subprocess.call(["mpc", "play", "1"])
    subprocess.call(["mpc", "repeat", "-q", "on"])
    subprocess.call(["mpc", "shuffle", "-q"])


# ----------Switch on identifing the rotory dail setting-----
prev = int


def switchOn():
    global device_state
    device_state = True
    parseToCsv(Interaction(datetime.now(), 'Device ON', device_state))
    print("-----------------------------Switch on-------------------------------",
          datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    #		print(Switch_sel1.value)
    if Switch_sel1.value > 0:
        Radio_state.playL1()
    if Switch_sel2.value > 0:
        Radio_state.playL2()
    if Switch_sel3.value > 0:
        Radio_state.playL3()
    if Switch_sel4.value > 0:
        Radio_state.playL4()


# ----------Switch off with switch-------------------------
def switchOff():
    global device_state
    device_state = False
    Radio_state.switchOff()
    print("-----------------------------Switch off-------------------------------",
          datetime.now().strftime("%d/%m/%Y %H:%M:%S"))


def parseToCsv(data):
    if not path.exists('buttonslog.csv'):
        with open('buttonslog.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(['Time', 'Button', 'volume_dial_position', 'device_state'])

    try:
        filename = 'buttonslog.csv'
        with open(filename, 'a') as f:
            writer = csv.writer(f)
            writer.writerow([data.id, data.name, data.volume_dial_position, data.state])
    except BaseException as e:
        print('BaseException:', filename)


# -----------Rotary switch operation ---------------
def PlayList1():
    #       	global  PlayListName, PlayListStopFlag
    if (not Radio_state.is_off):
        Radio_state.playL1()

    if Radio_state.is_off:
        parseToCsv(Interaction(datetime.now(), 'Sixties', device_state))


#	else:
#		PlayListName = 'Warning_1' # if off and still the switch is operated, Warning 1 will be played
#		PlayListStopFlag = True

def PlayList2():
    #        global  PlayListName, PlayListStopFlag
    if (not Radio_state.is_off):
        Radio_state.playL2()

    if Radio_state.is_off:
        parseToCsv(Interaction(datetime.now(), 'Nostalgia', device_state))

        #        else:


#                PlayListName = 'Warning_1'
#                PlayListStopFlag = True
def PlayList3():
    #        global  PlayListName, PlayListStopFlag
    if (not Radio_state.is_off):
        Radio_state.playL3()

    if Radio_state.is_off:
        parseToCsv(Interaction(datetime.now(), 'Klassiek', device_state))


#        else:
#                PlayListName = 'Warning_1'
#                PlayListStopFlag = True

def PlayList4():
    #        global  PlayListName, PlayListStopFlag
    if (not Radio_state.is_off):
        Radio_state.playL4()

    if Radio_state.is_off:
        parseToCsv(Interaction(datetime.now(), 'Nederlands', device_state))


#        else:
#                PlayListName = 'Warning_1'
#                PlayListStopFlag = True

Switch_sel1.when_activated = PlayList1
Switch_sel2.when_activated = PlayList2
Switch_sel3.when_activated = PlayList3
Switch_sel4.when_activated = PlayList4
Switch_onoff.when_activated = switchOn
Switch_onoff.when_deactivated = switchOff


# ----------Volume dail operation -----------------

def Volume_read():
    global VolumeSetRaw_prev, VolumeSetRaw

    VolumeSetRaw_last = PotVol.raw_value
    if abs(VolumeSetRaw_prev - VolumeSetRaw_last) > 2:
        #                print ("Volume change", VolumeSetRaw_last)
        VolumeSet = VolumeSetRaw[VolumeSetRaw_last]

        # --- Method 1
        subprocess.call(["/var/www/vol.sh", str(VolumeSet)])
        # ----Method 2
        #                subprocess.call(["mpc","volume","-q",str(VolumeSet)])
        # ---Method 3
        #               client.connect("localhost", 6600)
        #               client.setvol(VolumeSet)
        #               client.close()
        #               client.disconnect()
        # -----
        parseToCsv(Interaction(datetime.now(), 'Volume', device_state, VolumeSet))
        VolumeSetRaw_prev = VolumeSetRaw_last


# ---------------------delay start up + check Mpd ready + announcement ---------------------------
led_red.off()
led_green.blink(on_time=0.5, off_time=0.5, n=None, background=True)
sleep(5)  # wait until service is started

while i < 50:  # check if Mpc is up and running, sleep (5) should be enough to have no exceptions
    try:
        i += 1
        sleep(0.5)
        s = subprocess.check_output(["mpc"])
        print("attempts =", i, "Mpc output", s)
        if (s is not None): break
    except Exception as e:
        print("Exception in start up=", e)
        pass

sleep(1)  # create some margin until service is started
print("-----------------------------First power on-------------------------------",
      datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
Volume_read()  # read voluem dial setting and set volume

if Switch_onoff.value > 0:
    state = True
    switchOn()  # switch on if switch is on
else:  # Switch off, give message that radio can be switched on
    state = False
    subprocess.call(["mpc", "clear", "-q"])
    subprocess.call(["mpc", "load", "-q", "First_Switch_on"])
    subprocess.call(["mpc", "repeat", "-q", "off"])
    subprocess.call(["mpc", "play", "-q"])
    sleep(5)  # time for
    led_green.off()

# ----------------------Main loop, -------------------------------
n = 0
while True:
    try:
        Volume_read()
        if n == 500:
            n = 0
            checkMPC()  # check Mpc status every 500 cycles, just in case, switch to offline
        #               Reset_Touch()
        #               print("Phototrans =",PhotoSense.raw_value)
        else:
            # Volume_read()
            sleep(0.01)
            n = n + 1
    except  Exception  as e:
        print('Exception in main =', e)
        pass
