#!/usr/bin/env python3

from PIL import Image
from pprint import pformat
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
$ fswebcam --device /dev/video0 --no-timestamp --no-title --no-subtitle --no-banner --no-info -s brightness=120% -r 352x240 --png 1 /tmp/rubiks_scan.png

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


def extract_rgb_pixels(size):
    dimensions = "%dx%dx%d" % (size, size, size)
    colors = {}
    center_pixels = get_center_pixel_coordinates(dimensions)
    squares_per_side = math.pow(size, 2)

    square_indexes = list(range(1, squares_per_side+1))
    square_indexes_rotated = rotate_2d_array(square_indexes)

    for (side_index, side) in enumerate('U', 'L', 'F', 'R', 'B', 'D'):
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

        '''
        The L, F, R, and B sides are simple, for the U and D sides the cube in
        the png is rotated by 90 degrees so we need to rotate our array of
        square indexes by 90 degrees to compensate
        '''
        if side == 'U' or side == 'D':
            my_indexes = square_indexes_rotated
        else:
            my_indexes = square_indexes

        filename = "/tmp/rubiks-side-%s.png" % side
        im = Image.open(filename)
        pix = im.load()

        for index in my_indexes:
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

    if len(sys.argv) < 2 or not sys.argv[1].isdigit() or int(sys.argv[1]) < 2:
        print("ERROR: Run via 'extract_rgb_pixels.py 3' where 3 means a 3x3x3 cube, 2 means 2x2x2, etc")
        sys.exit(1)

    size = int(sys.argv[1])

    print(json.dumps(extract_rgb_pixels(size)))
