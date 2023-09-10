from machine import Pin, PWM
import time
import network
import utime
import urequests
from mfrc522 import MFRC522
#from clsCards import cardhttp
import _thread
import gc
from WIFI_CONFIG import ssid, password

# Set up the Buzzer pin as PWM
buzzer = PWM(Pin(12)) # Set the buzzer to PWM mode

# Set PWM frequency to 1000
buzzer.freq(1000)

#from store import NfcCard, cardlib


room = 'Kitchen'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
wlan.config(pm = 0xa11140)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )
    

# Make GET request

#r = urequests.get("http://192.168.68.103:5005/playroom/playpause")

#r.close()

from ota import OTAUpdater
from WIFI_CONFIG import SSID, PASSWORD

firmware_url = "https://raw.githubusercontent.com/tdp1000/PicoRFID/main/"

ota_updater = OTAUpdater(SSID, PASSWORD, firmware_url, "main.py")

ota_updater.download_and_install_update_if_available()


reader = MFRC522(spi_id=0,sck=2,miso=4,mosi=3,cs=1,rst=0)
time.sleep(1)

def main_thread():
    backstop = 0
    initialised = 0
    PreviousCard = 0
    
       
    while True:
        reader.init()
        (stat, tag_type) = reader.request(reader.REQIDL)
        #print("waiting")
        if stat == reader.OK:
            (stat, uid) = reader.SelectTagSN()
            if stat == reader.OK:
                #print("reader ok")
                card = int.from_bytes(bytes(uid),"little",False)
                #print(card)
                #print("Done")
                if card == PreviousCard:
                    #print("waiting for new card")
                    pass
                else:
                    print("getting request")
                    request = "http://192.168.68.130:5200/scan_nfc?card=" + str(card) +"&room=" + str(room)
                    print(request)
                    # Set PWM duty
                    _thread.start_new_thread(buzzer_thread,())
                    r = urequests.get(request)
                    # Duty to 0 to turn the buzzer off
                    print(r.text)
                    r.close()
                    gc.collect()
                PreviousCard = card
                utime.sleep_ms(100)
        time.sleep_ms(50)
        backstop += 1
        if backstop > 10:
            backstop = 0
            PreviousCard = 0

def buzzer_thread():
    buzzer.freq(1000)
    buzzer.duty_u16(10000)
    utime.sleep_ms(400)
    buzzer.duty_u16(0)
    return

main_thread()
