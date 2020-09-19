#!/usr/bin/env python
# Copyright (c) Marius Gheorghescu. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
import sys
import time
import serial
import logging
import collections
import matplotlib.pyplot as plt
import mplcursors
import matplotlib.animation as animation
from matplotlib.dates import MinuteLocator, SecondLocator, DateFormatter
from matplotlib.widgets import Button
from datetime import datetime, timedelta
from threading import Thread
from os import path

version = '1.0.0'

class CRPlot:
    def __init__(self, sample_buffer = 100):
        self.port = '/dev/ttyACM0'
        self.baud = 9600
        self.thread = None
        self.stream_data = True
        self.pause_chart = False
        self.sample_count = 0
        self.animation_index = 0;
        self.max_samples = sample_buffer
        self.data = collections.deque(maxlen=sample_buffer)
        self.timestamps = collections.deque(maxlen=sample_buffer)
        self.dataStartTS = None
        self.serialConnection = None
        self.framerate = 30;

    def serialStart(self, port = 'COM3', speed = 115200):
        self.port = port
        self.baud = speed
        logging.info("Trying to connect to port='{}' baud='{}'".format(port, speed))
        try:
            self.serialConnection = serial.Serial(self.port, self.baud, timeout=5)
            logging.info("Connected to {} at baud {}".format(port, speed))
        except serial.SerialException as e:
            logging.error("Error connecting to serial port: {}".format(e))
            return False;
        except:
            logging.error("Error connecting to serial port, unexpected exception:{}".format(sys.exc_info()))
            return False;

        if self.thread == None:
            self.thread = Thread(target=self.serialStream)
            self.thread.start()

            print('Initializing data capture:', end='')
            wait_timeout = 100;
            while wait_timeout > 0 and self.sample_count == 0:
                print('.', end='', flush=True)
                time.sleep(0.01)
                wait_timeout -= 1

            if (self.sample_count == 0):
                logging.error("Error: No data samples received. Aborting")
                return False

            print("OK\n")
            return True


    def pauseRefresh(self, state):
        logging.debug("pause {}".format(state))
        self.pause_chart = not self.pause_chart
        if self.pause_chart:
            self.bpause.label = 'Resume'
        else:
            self.bpause.label = 'Pause'

    def saveAnimation(self, state):
        logging.debug("save {}".format(state))
        filename = None;

        while True:
            filename = 'current' + str(self.animation_index) + '.gif'
            self.animation_index += 1
            if not path.exists(filename):
                break;

        logging.info("Animation saved to '{}'".format(filename))
        self.anim.save(filename, writer='imagemagick', fps=self.framerate)

    def chartSetup(self, refresh_interval=100):
        plt.style.use('dark_background')
        fig = plt.figure(num="Current Viewer")
        fig.autofmt_xdate()
        self.ax = plt.axes()
        ax = self.ax;

        ax.set_title('Current Ranger')

        ax.set_ylabel("Current draw")
        ax.set_yscale("log", nonposy='clip')
        ax.set_ylim(1e-9, 1e1)
        plt.yticks([1.0e-9, 1.0e-8, 1.0e-7, 1.0e-6, 1.0e-5, 1.0e-4, 1.0e-3, 1.0e-2, 1.0e-1, 1.0], ['1nA', '10nA', '100nA', '1\u00B5A', '10\u00B5A', '100\u00B5A', '1mA', '10mA', '100mA', '1A'], rotation=0)
        ax.grid(axis="y", which="both", color="yellow", alpha=.3, linewidth=.5)

        ax.set_xlabel("Time")
        plt.xticks(rotation=30)
        ax.set_xlim(datetime.now(), datetime.now() + timedelta(seconds=10))
        ax.grid(axis="x", color="green", alpha=.3, linewidth=2, linestyle=":")
        ax.xaxis.set_major_locator(SecondLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
        ax.xaxis.set_minor_formatter(DateFormatter('%H:%M:%S.%f'))

        lines = ax.plot([], [], label="Current")[0]

        lastText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
        self.anim = animation.FuncAnimation(fig, self.getSerialData, fargs=(lines, plt.legend(), lastText), interval=refresh_interval)

        plt.legend(loc="upper right")

        apause = plt.axes([0.91, 0.15, 0.08, 0.07])
        self.bpause = Button(apause, label='Pause', color='0.2', hovercolor='0.1')
        self.bpause.on_clicked(self.pauseRefresh)
        self.bpause.label.set_color('yellow')

        aanimation = plt.axes([0.91, 0.25, 0.08, 0.07])
        bsave = Button(aanimation,  'GIF', color='0.2', hovercolor='0.1')
        bsave.on_clicked(self.saveAnimation)
        bsave.label.set_color('yellow')

        crs = mplcursors.cursor(ax, hover=True)
        @crs.connect("add")
        def _(sel):
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="yellow", alpha=.4)
            sel.annotation.set_text(self.textAmp(sel.target[1]))

        self.framerate = 1000/refresh_interval
        plt.gcf().autofmt_xdate()
        plt.show()


    def serialStream(self):

        # set data streaming mode on CR (assuming it was off)
        self.serialConnection.write(b'u')

        self.serialConnection.reset_input_buffer()
        self.sample_count = 0
        line_count = 0;
        error_count = 0;
        self.dataStartTS = datetime.now()

        logging.info("Starting USB streaming loop");

        while (self.stream_data):
            try:

                # get the timestamp before the data string, likely to align better with the actual reading
                ts = datetime.now()
                line = self.serialConnection.readline().decode("utf-8")

                if (line.startswith("USB_LOGGING")):
                    if (line.startswith("USB_LOGGING_DISABLED")):
                        # must have been left open by a different process/instance
                        logging.info("Logging was disabled. Re-enabling")
                        self.serialConnection.write(b'u')
                        self.serialConnection.flush()
                    continue

                try:
                    data = float(line)
                    self.sample_count += 1

                    if (data >= 0.0):
                        self.data.append(data)
                        self.timestamps.append(ts)

                        if (self.sample_count % 1000 == 0):
                            logging.debug("{}: '{}' -> {}".format(ts.strftime("%H:%M:%S.%f"), line.rstrip(), data))
                            dt = datetime.now() - self.dataStartTS;
                            logging.debug("Received {} samples in {:.0f}ms  ({:.2f} samples/second)".format(self.sample_count, 1000*dt.total_seconds(), self.sample_count/dt.total_seconds()))
                    else:
                        # this happens too often (negative values)
                        self.data.append(1.0e-9)
                        self.timestamps.append(ts)
                        logging.warning("Unexpected value='{}'".format(line))

                except KeyboardInterrupt:
                    logging.info('Terminated by user')
                    self.stream_data = False
                    break

                except:
                    logging.error("Invalid data format: '{}': {}".format(line, sys.exc_info()))
                    error_count+=1;
                    if (line_count > 1000) and (error_count/line_count > 0.5):
                        logging.error("Error rate is too high ({} errors out of {} lines)".format(error_count, line_count))
                        break
                    pass

            except:
                logging.error('Serial read error: {}'.format(sys.exc_info()))
                error_count+=1;
                if (line_count > 1000) and (error_count/line_count > 0.5):
                    logging.error("Error rate is too high ({} errors out of {} lines)".format(error_count, line_count))
                    break

        # stop streaming so the device shuts down if in auto mode
        logging.info('Telling CR to stop USB streaming');
        self.serialConnection.write(b'u')
        logging.info('Serial streaming terminated');

    def textAmp(self, amp):
        if (abs(amp) > 1.0):
            return "{:.3f} A".format(amp)
        if (abs(amp) > 0.001):
            return "{:.2f} mA".format(amp*1000)
        if (abs(amp) > 0.000001):
            return "{:.1f} \u00B5A".format(amp*1000*1000)
        return "{:.1f} nA".format(amp*1000*1000*1000)


    def getSerialData(self, frame, lines, legend, lastText):
        if (self.pause_chart or len(self.data) < 2):
            return
        dt = self.timestamps[-1] - self.timestamps[0];
        self.ax.set_xlim(self.timestamps[0], self.timestamps[-1])
        lastText.set_text('{:.1f} SPS'.format(len(self.data)/dt.total_seconds()) )
        logging.debug("Drawing chart: range {}@{} .. {}@{}".format(self.data[0], self.timestamps[0], self.data[-1], self.timestamps[-1]))
        lines.set_data(self.timestamps, self.data)
        self.ax.legend(labels=['Last: {}\nAvg: {}'.format( self.textAmp(self.data[-1]), self.textAmp(sum(self.data)/len(self.data)))])

    def close(self):
        self.stream_data = False

        if self.thread != None:
            self.thread.join()

        if self.serialConnection != None:
            self.serialConnection.close()

        logging.info("Connection closed.")


def main():

    logging.basicConfig(filename='current_viewer.log',format='%(levelname)s:%(asctime)s:%(threadName)s:%(message)s', level=logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(levelname)s:%(message)s'))
    logging.getLogger('').addHandler(console)

    print("CurrentViewer v" + version)

    if(len(sys.argv) != 2):
        print('\nUsage:\n\tpython current_viewer.py <COM_port>')
        exit(1)

    port = sys.argv[1]

    csp = CRPlot(10000)

    if (csp.serialStart(port)):
        logging.debug("Starting live chart...")
        csp.chartSetup(refresh_interval=100)

    csp.close()


if __name__ == '__main__':
  main()
