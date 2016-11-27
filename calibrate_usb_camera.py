#!/usr/bin/env python3

import logging
import os
import subprocess

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
log = logging.getLogger(__name__)

# Color the errors and warnings in red
logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

png_filename = '/tmp/rubiks_scan.png'
calibrate_filename = '/tmp/MINDCUB3R-usb-camera.json'

if os.path.exists(png_filename):
    os.unlink(png_filename)

# To capture a single png from the webcam
log.info("Capturing a frame from webcam /dev/video0")
subprocess.call(['fswebcam',
                 '--device', '/dev/video0',
                 '--no-timestamp',
                 '--no-title',
                 '--no-subtitle',
                 '--no-banner',
                 '--no-info',
                 '-r', '352x240',
                 # '--rotate', '270',
                 '--png', '1',
                 png_filename])

# This will print a list of RGB tuples (one tuple for each of the 9 squares) in json format
log.info("Analyzing frame to find the rubiks cube")
output = subprocess.check_output(['cubefinder.py',
                                  '-f',
                                  png_filename])

log.info("Saving results to %s" % calibrate_filename)
with open(calibrate_filename, 'wb') as fh:
    for line in output.splitlines():
        fh.write(line)
