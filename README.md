# pi-hole-button
![button green](/images/05_button_green.jpeg)
I built a Red Button to disable my pi-hole!
This was inspired by Christopher Moravec see his original [repo](https://github.com/morehavoc/pi-hole-button) and [youtube video](https://www.youtube.com/embed/h51sABc1pn0).
The button design with the Raspberry Pi Pico W in the base was inspire by Dmytro Panin [BOB](https://github.com/dr-mod/bob)

As I didn't like to purchased a new micro controller or a of the shelf button I designed, inspired by BOB, my own button case.

I also change a bit the code from Christopher Moravec to suite my needs as I have only one led and did like the idea to have some things hardcoded so I moved them to the settings.py

Hardware you need:
* [Raspberry Pi Pico W](https://www.raspberrypi.com/products/raspberry-pi-pico/)
* [(Cherry) MX Switch](https://www.cherrymx.de/en/cherry-mx/mx-original/mx-red.html)
* [3 * WS2812 LEDs](https://amzn.eu/d/g3ZF5xG)
* 2 M3 x 10mm screws

To get this working:
1. I solder the WS2812 LED strip to the Raspberry Pi Pico W VBU, GND, GP28 and the MX switch to GND and GP6 like this: 
![soldering](/images/02_soldering.jpeg)
1. More details about the assembly you see in the [images folder](/images/)
2. Flash your Raspberry Pi PIco W with CircuitPython [download](https://circuitpython.org/board/raspberry_pi_pico_w/)
3. Copy `main.py`, `setings.py`, and `settings.toml` onto your Raspberry Pi Pico W
4. Install CircuitPython packages. I use [circup](https://github.com/adafruit/circup) for this: `circup install --auto`
5. Update `settings.py` with your pi-hole's API key, pi-hols hostname/IP and Pins on your Raspberry Pi Pico W.
6. Update `settings.toml` with your wifi information.

Some useful links:
* [Pi-Hole Website](https://pi-hole.net/)
* [AdaFruit Article on Async in Python](https://learn.adafruit.com/cooperative-multitasking-in-circuitpython-with-asyncio/overview)
