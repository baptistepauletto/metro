# CircuitPython Code for Matrix Portal

This folder contains the code to run on your Adafruit Matrix Portal hardware.

## Files

- `code.py` - Main program for the Matrix Portal
- `secrets.py` - WiFi credentials (edit this file)

## Installation Steps

### 1. Install CircuitPython

1. Download CircuitPython for Matrix Portal M4 from [circuitpython.org](https://circuitpython.org/board/matrixportal_m4/)
2. Connect Matrix Portal via USB
3. Double-click the reset button to enter bootloader mode
4. Copy the `.uf2` file to the `MATRIXBOOT` drive
5. The board will reboot as `CIRCUITPY`

### 2. Install Required Libraries

Download the [CircuitPython Library Bundle](https://circuitpython.org/libraries) matching your CircuitPython version.

Copy these folders to `CIRCUITPY/lib/`:
- `adafruit_matrixportal/`
- `adafruit_display_text/`
- `adafruit_bitmap_font/`
- `adafruit_requests.mpy`
- `adafruit_esp32spi/`
- `neopixel.mpy`

### 3. Copy Project Files

1. Copy `code.py` to `CIRCUITPY/`
2. Copy `secrets.py` to `CIRCUITPY/` and edit with your WiFi credentials
3. Copy `schedule.json` (generated from build_schedule.py) to `CIRCUITPY/`

### 4. Configure

Edit `secrets.py` with your WiFi details:
```python
secrets = {
    'ssid': 'YourWiFiName',
    'password': 'YourWiFiPassword',
    'timezone': "America/Montreal",
}
```

### 5. Test

1. The board should connect to WiFi automatically
2. Check the serial console for debug output
3. The display should show the countdown to the next metro

## Troubleshooting

### No WiFi Connection
- Check `secrets.py` credentials
- Ensure 2.4GHz WiFi (Matrix Portal doesn't support 5GHz)
- Check serial console for error messages

### Display Not Working
- Ensure 64x32 matrix is properly connected
- Check power supply (5V 4A recommended)
- Verify brightness setting in code.py

### Schedule Not Loading
- Ensure `schedule.json` is in the root of CIRCUITPY
- Check file is valid JSON (test with build_schedule.py first)
- Check serial console for errors

## Serial Console

To see debug output:
- **Windows:** Use Mu Editor or PuTTY
- **Mac/Linux:** `screen /dev/tty.usbmodem* 115200`

## Power

The Matrix Portal needs adequate power:
- Use 5V 4A power supply for the matrix
- USB power for the Matrix Portal itself
- Connect matrix power to the terminal block on Matrix Portal
