# pi-hole-button
I built a GRB (Giant Red Button) to disable our pi-hole! You can check out my YouTube video here:

[<img src="https://img.youtube.com/vi/h51sABc1pn0/hqdefault.jpg" width="560" height="315"
/>](https://www.youtube.com/embed/h51sABc1pn0)

This repo has the source code and STL files for what I built. Here are the other parts that I purchased:

* [Adafruit QT Py S3 with 2MB PSRAM WiFi Dev Board with STEMMA QT](https://www.adafruit.com/product/5700)
* [Giant Button](https://www.amazon.com/gp/product/B00XRC9URW)

Some useful links:
* [Pi-Hole Website](https://pi-hole.net/)
* [AdaFruit Article on Async in Python](https://learn.adafruit.com/cooperative-multitasking-in-circuitpython-with-asyncio/overview)

To get this working:
1. Copy `code.py`, `setings.py`, and `settings.toml` onto your microcontroller (I'm using CircuitPython)
2. Install CircuitPython packages. I use [circup](https://github.com/adafruit/circup) for this: `circup install --auto`
2. Update `settings.py` with your pi-hole's API key.
3. Update `settings.toml` with your wifi information.
4. Update `code.py` with the correct URL to your pi hole. (Line 48 and Line 74).
