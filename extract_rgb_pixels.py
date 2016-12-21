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


def compress_2d_array(original):
    """
    Convert 2d array to a 1d array
    """
    result = []
    for row in original:
        for col in row:
            result.append(col)
    return result


def extract_rgb_pixels(size, use_test_data):
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

        if use_test_data:
            filename = "test-data/%s/rubiks-side-%s.png" % (dimensions, side)
        else:
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
    parser.add_argument('--test', action='store_true', default=False)
    parser.add_argument('size', type=int, help='"3" for 3x3x3, "2" for 2x2x2, etc')
    args = parser.parse_args()

    if args.test:
        output = json.dumps(extract_rgb_pixels(args.size, True))

        if args.size == 2:
            if output == """{"1": [194, 181, 4], "2": [195, 189, 3], "3": [207, 203, 8], "4": [201, 196, 6], "5": [36, 130, 68], "6": [37, 118, 62], "7": [38, 128, 67], "8": [35, 124, 68], "9": [189, 60, 5], "10": [168, 49, 9], "11": [185, 58, 3], "12": [188, 51, 7], "13": [20, 66, 177], "14": [9, 52, 154], "15": [6, 61, 177], "16": [8, 51, 163], "17": [155, 6, 2], "18": [131, 6, 4], "19": [150, 7, 1], "20": [147, 6, 0], "21": [185, 204, 244], "22": [191, 210, 250], "23": [207, 222, 253], "24": [18, 23, 61]}""":
                print("PASS: 2x2x2")
            else:
                print("FAIL: 2x2x2")

        elif args.size == 3:
            if output == """{"1": [115, 115, 5], "2": [121, 124, 0], "3": [127, 127, 5], "4": [128, 127, 1], "5": [132, 130, 0], "6": [121, 123, 0], "7": [134, 137, 0], "8": [135, 135, 1], "9": [141, 135, 0], "10": [12, 110, 123], "11": [13, 101, 115], "12": [9, 86, 96], "13": [13, 109, 123], "14": [9, 105, 117], "15": [7, 96, 104], "16": [13, 108, 114], "17": [9, 98, 106], "18": [12, 101, 107], "19": [162, 61, 15], "20": [154, 54, 5], "21": [129, 42, 12], "22": [161, 61, 12], "23": [161, 60, 14], "24": [146, 44, 6], "25": [166, 60, 12], "26": [150, 48, 10], "27": [156, 52, 13], "28": [6, 54, 200], "29": [5, 53, 189], "30": [5, 42, 156], "31": [6, 54, 200], "32": [6, 47, 191], "33": [4, 44, 176], "34": [4, 52, 188], "35": [3, 47, 180], "36": [8, 45, 186], "37": [115, 5, 14], "38": [108, 4, 1], "39": [94, 3, 0], "40": [115, 5, 6], "41": [114, 6, 6], "42": [104, 4, 2], "43": [121, 2, 6], "44": [105, 5, 3], "45": [112, 4, 4], "46": [180, 200, 235], "47": [190, 211, 240], "48": [204, 219, 250], "49": [199, 218, 250], "50": [208, 221, 253], "51": [197, 214, 244], "52": [205, 226, 255], "53": [212, 227, 250], "54": [210, 225, 246]}""":
                print("PASS: 3x3x3")
            else:
                print("FAIL: 3x3x3")
    else:
        print(json.dumps(extract_rgb_pixels(args.size, False)))
