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


# async method that gets the status of the pihole every interval
async def get_status(requests, interval, status):
    while True:
        url = f"http://{settings.pihole_hostname}/admin/api.php?status&auth={settings.pihole_key}"
        print(url)
        response = requests.get(url)
        s = response.json()["status"]
        status.value = s
        print(s)
        response.close()
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
    while True:
        switch.update()
        if switch.rose:
            url = f"http://{settings.pihole_hostname}/admin/api.php?disable={duration}&auth={settings.pihole_key}"
            print(url)
            response = requests.get(url)
            s = response.json()["status"]
            status.value = s
            print(s)
            response.close()
            await asyncio.sleep(duration)
            status.value = "enabled"
            print("enabled - disable complete")
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
    global pixel, switch
    # configure requests
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

    # set status
    pihole_status = AsyncValue("enabled")

    # prep tasks
    status_check_task = asyncio.create_task(get_status(requests, 5, pihole_status))
    led_task = asyncio.create_task(set_neopixel(pixel, pihole_status))
    disable_task = asyncio.create_task(disable_it(switch, requests, pihole_status, settings.disable_duration))

    await asyncio.gather(status_check_task, led_task, disable_task)


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
