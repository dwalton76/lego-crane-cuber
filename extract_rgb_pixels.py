#!/usr/bin/env python3

from PIL import Image
from pprint import pformat
import argparse
import logging
import json
import math
import os
import sys


def print_calibrate_howto():
    print("""
We need to know which pixels are the center pixels for each square.
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
$ fswebcam --device /dev/video0 --no-timestamp --no-title --no-subtitle --no-banner --no-info -s brightness=120% -r 320x240 --png 1 /tmp/rubiks_scan.png

scp this file to your laptop and view it via "edisplay rubiks_scan.png".
edisplay will display the (x, y) coordinates as you move the mouse in the image.
Use this to find the (x, y) coordinate for each square and record it in camera.json
""")


def get_center_pixel_coordinates(key):
    center_pixels = []
    calibrate_filename = '/home/robot/lego-crane-cuber/camera.json'

    if not os.path.exists(calibrate_filename):
        print("ERROR: No camera.json file")
        print_calibrate_howto()
        sys.exit(1)

    with open(calibrate_filename, 'r') as fh:
        data = json.load(fh)

        if key in data:
            squares = data[key]

            for square in squares:
                center_pixels.append((square.get('x'), square.get('y')))
        else:
            print("ERROR: Cube %s is not in %s" % (key, calibrate_filename))
            print_calibrate_howto()
            sys.exit(1)

    log.info("center_pixels\n%s" % pformat(center_pixels))
    return center_pixels


def rotate_2d_array(original):
    """
    http://stackoverflow.com/questions/8421337/rotating-a-two-dimensional-array-in-python
    """
    result = []
    for x in zip(*original[::-1]):
        result.append(x)
    return result


def compress_2d_array(original):
    """
    Convert 2d array to a 1d array
    """
    result = []
    for row in original:
        for col in row:
            result.append(col)
    return result


def extract_rgb_pixels(size):
    dimensions = "%dx%dx%d" % (size, size, size)
    colors = {}
    center_pixels = get_center_pixel_coordinates(dimensions)
    squares_per_side = int(math.pow(size, 2))

    # print the cube layout to make the debugs easier to read
    if size == 2:
        log.info("""
               01 02
               03 04
        05 06  09 10  13 14  17 18
        07 08  11 12  15 16  19 20
               21 22
               23 24
        """)

    elif size == 3:
        log.info("""
           01 02 03
           04 05 06
           07 08 09
 10 11 12  19 20 21  28 29 30  37 38 39
 13 14 15  22 23 24  31 32 33  40 41 42
 16 17 18  25 26 27  34 35 36  43 44 45
           46 47 48
           49 50 51
           52 53 54
        """)

    for (side_index, side) in enumerate(('U', 'L', 'F', 'R', 'B', 'D')):
        '''
        squares are numbered like so:

               01 02
               03 04
        05 06  09 10  13 14  17 18
        07 08  11 12  15 16  19 20
               21 22
               23 24

        calculate the index of the first square for each side
        '''
        init_square_index = (side_index * squares_per_side) + 1

        square_indexes = []
        for row in range(size):
            square_indexes_for_row = []
            for col in range(size):
                square_indexes_for_row.append(init_square_index + (row * size) + col)
            square_indexes.append(square_indexes_for_row)
        log.info("%s square_indexes %s" % (side, pformat(square_indexes)))

        '''
        The L, F, R, and B sides are simple, for the U and D sides the cube in
        the png is rotated by 90 degrees so we need to rotate our array of
        square indexes by 90 degrees to compensate
        '''
        if side == 'U' or side == 'D':
            my_indexes = rotate_2d_array(square_indexes)
        else:
            my_indexes = square_indexes

        log.info("%s my_indexes %s" % (side, pformat(my_indexes)))

        filename = "/tmp/rubiks-side-%s.png" % side
        im = Image.open(filename)
        pix = im.load()

        my_indexes = compress_2d_array(my_indexes)
        log.info("%s my_indexes (final) %s" % (side, pformat(my_indexes)))

        # for index in my_indexes:
        for index in range(squares_per_side):
            square_index = my_indexes[index]

            (x, y) = center_pixels[index]
            (red, green, blue) = pix[x, y]
            log.info("square %d, pixels (%s, %s), RGB (%d, %d, %d)" %
                (square_index, x, y, red, green, blue))

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

    parser = argparse.ArgumentParser(description="Extract RGB values from rubiks cube images")
    parser.add_argument('size', type=int, help='"3" for 3x3x3, "2" for 2x2x2, etc')
    args = parser.parse_args()

    print(json.dumps(extract_rgb_pixels(args.size)))
