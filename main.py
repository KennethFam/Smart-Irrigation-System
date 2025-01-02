from time import sleep
import network
from machine import PWM, ADC, Pin
from picobricks import WS2812, MotorDriver
from machine import I2C
from picobricks import SSD1306_I2C
import math
import machine
import time
from utime import sleep
import utime
import urequests

THINGSPEAK_WRITE_API_KEY = 'G9K7XA33TJS92EFR' # abdul
HTTP_HEADERS = {'Content-Type': 'application/json'}

i2c = I2C(0, scl=Pin(5), sda=Pin(4))
oled = SSD1306_I2C(128, 64, i2c)
adc_28 = machine.ADC(28)
potentiometer = ADC(Pin(26))

ssid = "SJSU_guest"
password = ""

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

DRY_SOIL = 38000
WET_SOIL = 22000

oled.text("Power On", 30, 0)
oled.text("Waiting for ", 20, 30)
oled.text("Connection", 23, 40)
oled.show()
time.sleep(2)
oled.fill(0)

def read_percentage():
    raw_value = potentiometer.read_u16()
    percentage = int((raw_value / 65535) * 100)
    percentage = max(0, min(100, percentage))  #limit percentage from 0-100
    return percentage

#wait for connect/fail
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

#handle connection error
if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('Connected')

ws2812 = WS2812((1), brightness=0.5)
while True:
    oled.fill(0)
    oled.text("{}".format("Soil Moisture "), 10, 0)
    oled.text("{}".format("Value:"), 45, 10)

    soil_val = adc_28.read_u16()
    #calculate soil moisture percentage using minimum value (WET_SOIL) and max value (DRY_SOIL)
    store_percent = int((1 - (soil_val - WET_SOIL) / (DRY_SOIL - WET_SOIL)) * 100)
    store_percent = max(0, min(100, store_percent))  

    percentage = read_percentage()
    #calculate target value based on percentage
    target = WET_SOIL + ((1 - (percentage / 100)) * (DRY_SOIL - WET_SOIL))

    print(f"Soil Value: {soil_val}, Store Percent: {store_percent}, Target: {target}")

    oled.text("{}".format(f"{soil_val} ({store_percent}%)"), 25, 25)
    oled.text("{}".format(f"Target Value:"), 15, 40)
    oled.text("{}".format(f"{int(target)} ({percentage}%)"), 20, 55)
    oled.show()

    dht_readings = {'field2': store_percent}
    request = urequests.post(
        'http://api.thingspeak.com/update?api_key=' + THINGSPEAK_WRITE_API_KEY, 
        json=dht_readings, 
        headers=HTTP_HEADERS
    )
    request.close()

    if soil_val > target:
        ws2812.pixels_fill(((255), (0), (0)))
        ws2812.pixels_show()
    elif soil_val <= target:
        ws2812.pixels_fill(((0), (255), (0)))
        ws2812.pixels_show()

    time.sleep(0.01)
