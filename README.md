# CurrentViewer

CurrentViewer interactive data plot for [LowPowerLab CurrentRanger](https://github.com/LowPowerLab/CurrentRanger). It was designed to make it easier to capture and share power state profiles for IoT devices that swing between multiple power states (deep sleep, low power, full power).

![Screenshot](./images/example1.gif)

Example above is CurrentViewer in action (exported from the app itself).

Note: CurrentViewer is not a replacement for an osciloscope, as the readings are done via the internal ADC in SAMD21 [Microchip's ARM® Cortex®-M0+](https://www.microchip.com/wwwproducts/en/ATsamd21g18) which has its limitations. But it might be more convenient way to use CurrentRanger. Sometimes the noise (Vpp) can be comparable with entry level oscilloscopes, but the measurements can be off: CurrentRanger has to be properly calibrated in order for the measurements to match what multimeter or oscilloscope displays.

#
## Features:
- Runs on Windows and Linux (MacOS coming soon)
- It displays:
    - __SPS__ (Samples per Second) - how fast CurrentRanger sends samples over USB
    - __Last__ measurement (noisy) - most recent reading
    - __Average__ of the view (slow). The window buffer is currently set to last 10K measurements - this is easy to extend if needed
    - Point __annotations__ (hover the mouse over a certain sample)
- __Logaritmic plot__: makes it easy to read any swings from 1 nanoamp to 1 amp. Works with CurrentRanger in AUTORANGE as well as manual mode.
- Should be able to display as fast as the instrument can measure and send data over USB-Serial: currently this is around __750-800 samples/second__ without the CR OLED module (and 650 samples/second with OLED on).
- Automatically __turns on streaming on CurrentRanger__ (and if you use the new firmware feature with SMART AutoOff now the instrument will stay on as long as CurrentViewer is connected to it).
- It can save the chart **animations as .GIF** - for a convenient way to publish measurements on the web. Look for *current0.gif, current1.gif, etc* in the current folder
- **[Pause]** streaming if you want to zoom/pan into the data. The data is still being captured behind, when you resume you see an instant refresh.

#
## Installation

First clone the repo locally

```
git clone https://github.com/MGX3D/CurrentViewer
```

Recommended environment is Python3 (tested with 3.6+) with matplotlib/mplcursors/pyserial installed. To install all the requirements automatically:

```
pip install -r requirements.txt
```
or
```
pip3 install -r requirements.txt
```

#
## Running

First you need to identify the COM port CurrentRanger is plugged into (eg COM3 or /dev/ttyACM0). CurrentViewer was only tested with direct USB connection (might work with BlueTooth already - but needs validation). 

On Windows:
```
python current_viewer.py -p COM9
```

On Linux:
```
python current_viewer.py -p /dev/ttyACM0
```

If everything is working well you should see an image like this below (otherwise the current_viewer.log will have more information). There is also a console window (and a log: current_viewer.log) that displays more info.

![Screenshot](./images/screenshot1.png)


#
## Command line options

A number of options can be passed in command line to control export data to CSV/JSON, to control the charting speed and behavior, etc

```
CurrentViewer v1.0.1
usage: current_viewer.py -p <port> [OPTION]

CurrentRanger R3 Viewer

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -p PORT, --port PORT  Set the serial port (backed by USB or BlueTooth) to
                        connect to (example: /dev/ttyACM0 or COM3)
  -s <n>, --baud <n>    Set the serial baud rate (default: 115200)
  -o <file>, --out <file>
                        Save the output samples to <file> in the format set by
                        --format
  --format <fmt>        Set the output format to one of: CSV, JSON
  --gui                 Display the GUI / Interactive chart (default: ON)
  -g, --no-gui          Do not display the GUI / Interactive Chart. Useful for
                        automation
  -b <samples>, --buffer <samples>
                        Set the chart buffer size (window size) in # of
                        samples (default: 100000)
  -m <samples>, --max-chart <samples>
                        Set the chart max # samples displayed (default: 2048)
  -r <ms>, --refresh <ms>
                        Set the live chart refresh interval in milliseconds
                        (default: 66)
  -v, --verbose         Increase logging verbosity (can be specified multiple
                        times)
  -c, --console         Show the debug messages on the console
  -n, --no-log          Disable debug logging (enabled by default)
  -l LOG_FILE, --log-file LOG_FILE
                        Set the debug log file name
                        (default:current_viewer.log)
```

## Examples:

### Export data only, no GUI:

```
python current_viewer.py -p COM9 -g --out data.csv
```

This is useful for automation scenarios, where data needs to be logged for long periods of time and the charting is not needed.


### Disable file logging and GUI, log verbose to console instead:
```
python current_viewer.py -p COM9 -g -n -c -vvv
```

The file log (current_viewer.log) are now automatically rotated so they don't use the entire disk space, but can still be noisy (eg protocol) and generate lots of writes. In some cases (for example SD cards with limited write cycles) this might be undesirable, so now it's possible to disable disk logging completely. 


### Low CPU GUI: daw 100 samples only (default: 2048), 1 refresh/second (default 15)
```
python current_viewer.py -p COM9 -m 100 -r 1000
```

The charting library is CPU intensive, so setting a slower refresh (1fps instead of 15fps) or drawing fewer samples (100 instead of 2048) can reduce this. The other parameter that can affect performance (memory consumption) is -b/--buffer, this is the in-memory buffer, this represents the maximum view of the chart (-m is the # of data points in that range). For example if your CR is sending 600 samples/second at 100K sample buffer you get a history of roughly 3 minutes. Note that this setting does not affect the logging to CSV/JSON: exported data is saved to file directly from the acquisition loop so in theory should work for hours or days.

#
## Data Export

There are currently two data formats that CurrentViewer can save: CSV and JSON. See options --out and --format

### Example CSV:

```
Timestamp, Amps
2020-11-09 11:21:08.510715,-0.00081
2020-11-09 11:21:08.526342,-0.0004
2020-11-09 11:21:08.526342,-0.00081
2020-11-09 11:21:08.526342,-0.0004
2020-11-09 11:21:08.526342,-0.00121
2020-11-09 11:21:08.526342,-0.00121
2020-11-09 11:21:08.526342,-0.00121
2020-11-09 11:21:08.526342,-0.00121
2020-11-09 11:21:08.526342,-0.00121
2020-11-09 11:21:08.526342,-0.00081
2020-11-09 11:21:08.526342,-0.00121
2020-11-09 11:21:08.541963,-0.00121
2020-11-09 11:21:08.541963,-0.00121
2020-11-09 11:21:08.541963,-0.00081
2020-11-09 11:21:08.541963,-0.00121
2020-11-09 11:21:08.541963,-0.00081
2020-11-09 11:21:08.541963,-0.00081
```


### Example JSON

```
{
"data":[
{"time":"2020-11-09 11:51:08.439275","amps":"4.07e-08"},
{"time":"2020-11-09 11:51:08.439275","amps":"7.938e-08"},
{"time":"2020-11-09 11:51:08.439275","amps":"1.652e-08"},
{"time":"2020-11-09 11:51:08.439275","amps":"2.01e-09"},
{"time":"2020-11-09 11:51:08.439275","amps":"-2.74e-08"},
{"time":"2020-11-09 11:51:08.439275","amps":"-2.78e-08"},
{"time":"2020-11-09 11:51:08.439275","amps":"-2.74e-08"},
{"time":"2020-11-09 11:51:08.439275","amps":"-1.692e-08"},
{"time":"2020-11-09 11:51:08.454900","amps":"-4.03e-09"},
{"time":"2020-11-09 11:51:08.454900","amps":"3.949e-08"},
{"time":"2020-11-09 11:51:08.454900","amps":"5.883e-08"},
{"time":"2020-11-09 11:51:08.454900","amps":"6.125e-08"},
{"time":"2020-11-09 11:51:08.454900","amps":"1.168e-08"},
{"time":"2020-11-09 11:51:08.454900","amps":"4e-10"},
{"time":"2020-11-09 11:51:08.454900","amps":"-2.78e-08"},
{"time":"2020-11-09 11:51:08.466614","amps":"-2.78e-08"},
{"time":"2020-11-09 11:51:08.467614","amps":"-2.78e-08"}
]
}
```

#
## Known limitations

- Some runtime errors on MacOS / Python 3.8.5. 
- Not tested with the BlueTooth add-on yet
- Cannot always put the device in a predictable USB streaming mode (check the troubleshooting steps below)
- Negative data (or noisy data) - this is what's coming from the device. As the firmware improves (Felix has some ideas) this will improve as well.
- Cannot zoom X axis (time) while the data is streaming - limitation in matplotlib, best to use [pause], zoom in, then resume

#
## Troubleshooting

**Note:** Do not direct support requests to LowPowerLab, this is not an official tool, it's provided AS-IS. This is a side-project for me (and first time dealing with matplotlib in particular, so I will try to address issues as time (and skill) allows :) 

- ### Python dependencies
    This was tested with Python 3.6 (on Windows) and 3.8.5 (in Linux). Currently not working on MacOS 10.15 (although it should - but no time to debug).
    The dependencies that are critical and might break in the future are:
    - matplotlib (tested with 3.1.1)
    - mplcursors (tested with 0.3)

- ### Serial port errors
    Make sure you can connect to the COM port (using Arduino, Putty, etc) and you see the CurrentRanger menu (type '?'). Then enable USB streaming (command 'u') and check if the data is actually coming in the expected exponent format (see below)

- ### Data Errors
    CurrentViewer expects only measurements in the exponent format ('-0.81e-3') streamed over USB. if you have other things enabled (such as Touch debugging) you might see a lot of errors or inconsistent data. CurrentViewer measures the error rate and if above a certain threshold will stop. 

    I typically test with my branch of the firmware (https://github.com/MGX3D/CurrentRanger) as I only have one CurrentRanger but I try to not rely on features that are not available in the official firmware.

- ### Other issues?
    Check current_viewer.log (and its rotate log current_viewer.log.1) and look for hints. If no luck, open an issue on github and attach the log(s). Do describe your hardware setup as well, and perhaps check how the device behaves with other tools (Arduino, Putty, etc)

#
## Contributions

Contributions are welcome (note the MIT license), best to fork the project and submit a PR when done. Try to keep the changes small so they are easier to merge.
