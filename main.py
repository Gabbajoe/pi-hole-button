import digitalio
import neopixel
import wifi
import os
import socketpool
import ssl
import adafruit_requests
import time
from adafruit_debouncer import Debouncer
import asyncio
import settings
import json
import adafruit_datetime
import rtc
import adafruit_ntp


class AsyncValue:
    """Simple class to hold an value. Use .value to to read or write."""

    def __init__(self, initial_interval):
        self.value = initial_interval


def wifi_setup():
    try:
        print("Wifi Startup")
        print(f"Set hostname to: {settings.hostname}")
        wifi.radio.hostname = settings.hostname
        print(f"My MAC address: {[hex(i) for i in wifi.radio.mac_address]}")
        print("Available WiFi networks:")
        for network in wifi.radio.start_scanning_networks():
            print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
                                                     network.rssi, network.channel))
        wifi.radio.stop_scanning_networks()
        print(f"Connecting to {os.getenv('WIFI_SSID')}")
        wifi.radio.connect(os.getenv("WIFI_SSID"), os.getenv("WIFI_PASSWORD"))
        print(f"Connected to {os.getenv('WIFI_SSID')}")
        print(f"My IP address: {wifi.radio.ipv4_address}")
        return True
    except Exception:
        print("Failed to connect to wifi")
        pixel.fill((255, 0, 0))
        return False


# async method that gets the sid for the pihole api
async def get_sid(requests):
    global sid
    expire_time = adafruit_datetime.datetime.today() - adafruit_datetime.timedelta(days=3)
    validity = 1
    while True:
        today_time = adafruit_datetime.datetime.today()
        print(f"get_sid: today_time {today_time} - expire_time {expire_time}")
        if today_time >= expire_time:
            if sid is not None:
                print("get_sid: just doing a refresh auth")
                headers_sid = {
                    "sid": sid
                }
                response = requests.get(url=f"http://{settings.pihole_hostname}/api/auth", headers=headers_sid)
                validity = response.json()["session"]["validity"]
                expire_time = adafruit_datetime.datetime.today() + adafruit_datetime.timedelta(seconds=(validity-10))
                print(f"get_sid: sid = {sid} validity = {validity} new expire_time(-10s) {expire_time}")
                print(f"gong to wait for {validity-5}s")
            else:
                print("get_sid: going to refresh sid with password")
                # first need to authenticate and get a session id
                payload = {
                    "password": f"{settings.pihole_key}"
                }
                response = requests.post(url=f"http://{settings.pihole_hostname}/api/auth", data=json.dumps(payload))
                # extract session id
                sid = response.json()["session"]["sid"]
                validity = response.json()["session"]["validity"]
                expire_time = adafruit_datetime.datetime.today() + adafruit_datetime.timedelta(seconds=(validity-10))
                print(f"get_sid: sid = {sid} validity = {validity} new expire_time(-10s) {expire_time}")
                print(f"gong to wait for {validity-5}s")
        else:
            print("get_sid: no need to refresh")
        await asyncio.sleep((validity-5))


# async method that gets the status of the pihole every interval
async def get_status(requests, interval, status):
    global sid
    while True:
        if sid is not None:
            headers_sid = {
                "sid": sid
            }
            url = f"http://{settings.pihole_hostname}/api/dns/blocking"
            response = requests.get(url, headers=headers_sid)
            s = response.json()["blocking"]
            status.value = s
            print(f"get_status: blocking {s}")
        else:
            print("get_status: sid is none")
        await asyncio.sleep(interval)


# async method that sets the neopixel to green if the status is enabled, red if it's disabled
async def set_neopixel(pixel, status):
    while True:
        if status.value == "enabled":
            pixel.fill((0, 255, 0))
        else:
            pixel.fill((255, 0, 0))
        await asyncio.sleep(0)


# async method that disables the pi-hole
async def disable_it(switch, requests, status, duration):
    global sid
    while True:
        if sid is not None:
            switch.update()
            if switch.rose:
                headers_sid = {
                    "sid": sid
                }
                payload = {
                    "blocking": False,
                    "timer": 60
                }
                url = f"http://{settings.pihole_hostname}/api/dns/blocking"
                response = requests.post(url, data=json.dumps(payload), headers=headers_sid)
                s = response.json()["blocking"]
                status.value = s
                print(f"disable_it: blocking {s}")
                # response.close()
                await asyncio.sleep(duration)
                status.value = "enabled"
                print("disable_it: enabled - disable complete")
        else:
            print("disable_it: sid is none")
        await asyncio.sleep(0)


# async method for when there is no wifi, to make the button still do something
async def button_no_wifi(switch, status, duration):
    while True:
        switch.update()
        if switch.rose:
            status.value = "disabled"
            print("disabled - disable start")
            await asyncio.sleep(duration)
            status.value = "enabled"
            print("enabled - disable complete")
        await asyncio.sleep(0)


# setup the neopixels
pixel = neopixel.NeoPixel(settings.pin_neopixel, settings.neopixel_number)
# setup the button
button = digitalio.DigitalInOut(settings.pin_button)
button.switch_to_input(pull=digitalio.Pull.UP)
switch = Debouncer(button)
sid = None
# set the pixel to blue, and try to connect to wifi
pixel.fill((0, 0, 255))
wifi_try_count = 0
has_wifi = wifi_setup()
while not has_wifi and wifi_try_count < 2:
    print("sleeping for 5, will try again")
    time.sleep(5)
    has_wifi = wifi_setup()
    wifi_try_count += 1

# here means the wifi connected, set pixel to all colors and wait a sec
if has_wifi:
    pixel.fill((255, 255, 255))
else:
    pixel.fill((255, 255, 0))

time.sleep(1)


async def main_wifi():
    global pixel, switch, sid
    # configure requests
    pool = socketpool.SocketPool(wifi.radio)
    print("setting up time via NTP")
    ntp = adafruit_ntp.NTP(pool, tz_offset=0, cache_seconds=3600)
    rtc.RTC().datetime = ntp.datetime
    requests = adafruit_requests.Session(pool, ssl.create_default_context())
    # set status
    pihole_status = AsyncValue("enabled")
    # prep tasks
    sid_task = asyncio.create_task(get_sid(requests))
    status_check_task = asyncio.create_task(get_status(requests, 5, pihole_status,))
    led_task = asyncio.create_task(set_neopixel(pixel, pihole_status))
    disable_task = asyncio.create_task(disable_it(switch, requests, pihole_status, settings.disable_duration))

    await asyncio.gather(sid_task, status_check_task, led_task, disable_task)


async def main_no_wifi():
    global pixel, switch
    # set fake status
    pihole_status = AsyncValue("enabled")

    # prep tasks
    led_task = asyncio.create_task(set_neopixel(pixel, pihole_status))
    disable_task = asyncio.create_task(button_no_wifi(switch, pihole_status, 10))

    await asyncio.gather(led_task, disable_task)


if has_wifi:
    asyncio.run(main_wifi())
else:
    asyncio.run(main_no_wifi())
