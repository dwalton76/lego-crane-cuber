#!/usr/bin/env python3

from PIL import Image
from pprint import pformat
import logging
import json
import os
import sys


def print_calibrate_howto():
    print("""
We need to know which pixel are the center pixels for each of the 9 squares.
This data will be stored in camera.json which should look like the following.

robot@ev3dev[lego-crane-cuber]# cat camera.json
{"3x3x3" : [{"x" : 104, "y" : 63 },
            {"x" : 157, "y" : 63 },
            {"x" : 215, "y" : 63 },
            {"x" : 100, "y" : 117 },
            {"x" : 157, "y" : 117 },
            {"x" : 212, "y" : 117 },
            {"x" : 101, "y" : 174 },
            {"x" : 157, "y" : 174 },
            {"x" : 216, "y" : 174 }]
}
robot@ev3dev[lego-crane-cuber]#

So how to find the (x,y) for each square? On your EV3 run:
$ fswebcam --device /dev/video0 --no-timestamp --no-title --no-subtitle --no-banner --no-info -s brightness=120% -r 352x240 --png 1 /tmp/rubiks_scan.png

scp this file to your laptop and view it via "edisplay rubiks_scan.png".
edisplay will display the (x, y) coordinates as you move the mouse in the image.
Use this to find the (x, y) coordinate for each square and record it in camera.json
""")


def get_center_pixel_coordinates(key):
    center_pixels = []
    calibrate_filename = 'camera.json'

    if not os.path.exists(calibrate_filename):
        print_calibrate_howto()
        raise Exception("No camera.json file")

    with open(calibrate_filename, 'r') as fh:
        data = json.load(fh)

        if key in data:
            squares = data[key]

            for square in squares:
                center_pixels.append((square.get('x'), square.get('y')))
        else:
            print_calibrate_howto()
            raise Exception("Cube %s is not in %s" % (key, calibrate_filename))

    log.info("center_pixels\n%s" % pformat(center_pixels))
    return center_pixels


def extract_rgb_pixels_2x2x2():
    """
    The squares are numbered like so:

           01 02
           03 04
    05 06  09 10  13 14  17 18
    07 08  11 12  15 16  19 20
           21 22
           23 24
    """
    colors = {}
    center_pixels = get_center_pixel_coordinates('3x3x3')

    for side in ('U', 'L', 'F', 'R', 'B', 'D'):
        if side == 'U':
            init_square_index = 1
        elif side == 'L':
            init_square_index = 5
        elif side == 'F':
            init_square_index = 9
        elif side == 'R':
            init_square_index = 13
        elif side == 'B':
            init_square_index = 17
        elif side == 'D':
            init_square_index = 21
        else:
            raise Exception("Invalid face %s" % side)

        filename = "/tmp/rubiks-side-%s.png" % side
        im = Image.open(filename)
        pix = im.load()

        for index in range(4):
            if side == 'U' or side == 'D':
                if index == 0:
                    square_index = init_square_index + 2
                elif index == 1:
                    square_index = init_square_index
                elif index == 2:
                    square_index = init_square_index + 3
                elif index == 3:
                    square_index = init_square_index + 1
            else:
                square_index = init_square_index + index

            (x, y) = center_pixels[index]
            (red, green, blue) = pix[x, y]
            log.info("square %d, (%s, %s), RGB (%d, %d, %d)" % (square_index, x, y, red, green, blue))

            # colors is a dict where the square number (as an int) will be
            # the key and a RGB tuple the value
            colors[square_index] = (red, green, blue)

    return colors


def extract_rgb_pixels_3x3x3():
    """
    The squares are numbered like so:

              01 02 03
              04 05 06
              07 08 09
    10 11 12  19 20 21  28 29 30  37 38 39
    13 14 15  22 23 24  31 32 33  40 41 42
    16 17 18  25 26 27  34 35 36  43 44 45
              46 47 48
              49 50 51
              52 53 54
    """
    colors = {}
    center_pixels = get_center_pixel_coordinates('3x3x3')

    for side in ('U', 'L', 'F', 'R', 'B', 'D'):

        if side == 'U':
            init_square_index = 1
        elif side == 'L':
            init_square_index = 10
        elif side == 'F':
            init_square_index = 19
        elif side == 'R':
            init_square_index = 28
        elif side == 'B':
            init_square_index = 37
        elif side == 'D':
            init_square_index = 46
        else:
            raise Exception("Invalid face %s" % side)

        filename  = "/tmp/rubiks-side-%s.png" % side
        im = Image.open(filename)
        pix = im.load()

        for index in range(9):
            if side == 'U' or side == 'D':
                if index == 0:
                    square_index = init_square_index + 6
                elif index == 1:
                    square_index = init_square_index + 3
                elif index == 2:
                    square_index = init_square_index
                elif index == 3:
                    square_index = init_square_index + 7
                elif index == 4:
                    square_index = init_square_index + 4
                elif index == 5:
                    square_index = init_square_index + 1
                elif index == 6:
                    square_index = init_square_index + 8
                elif index == 7:
                    square_index = init_square_index + 5
                elif index == 8:
                    square_index = init_square_index + 2
            else:
                square_index = init_square_index + index

            (x, y) = center_pixels[index]
            (red, green, blue) = pix[x, y]
            log.info("square %d, (%s, %s), RGB (%d, %d, %d)" % (square_index, x, y, red, green, blue))

            # colors is a dict where the square number (as an int) will be
            # the key and a RGB tuple the value
            colors[square_index] = (red, green, blue)

    return colors


if __name__ == '__main__':
    # logging.basicConfig(filename='rubiks.log',
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
    log = logging.getLogger(__name__)

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

    if sys.argv[1] == '2x2x2':
        print(json.dumps(extract_rgb_pixels_2x2x2()))

    elif sys.argv[1] == '3x3x3':
        print(json.dumps(extract_rgb_pixels_3x3x3()))

    else:
        raise Exception("Only 2x2x2 and 3x3x3 are supported")
