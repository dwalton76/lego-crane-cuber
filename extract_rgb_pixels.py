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
    parser.add_argument('--size', type=int, help='"3" for 3x3x3, "2" for 2x2x2, etc')
    args = parser.parse_args()

    if args.test:
        results = []
        for size in range(2, 5):
            output = json.dumps(extract_rgb_pixels(size, True))

            if size == 2:
                if output == """{"1": [194, 181, 4], "2": [195, 189, 3], "3": [207, 203, 8], "4": [201, 196, 6], "5": [36, 130, 68], "6": [37, 118, 62], "7": [38, 128, 67], "8": [35, 124, 68], "9": [189, 60, 5], "10": [168, 49, 9], "11": [185, 58, 3], "12": [188, 51, 7], "13": [20, 66, 177], "14": [9, 52, 154], "15": [6, 61, 177], "16": [8, 51, 163], "17": [155, 6, 2], "18": [131, 6, 4], "19": [150, 7, 1], "20": [147, 6, 0], "21": [185, 204, 244], "22": [191, 210, 250], "23": [207, 222, 253], "24": [18, 23, 61]}""":
                    results.append("PASS: 2x2x2")
                else:
                    results.append("FAIL: 2x2x2")

            elif size == 3:
                if output == """{"1": [115, 115, 5], "2": [121, 124, 0], "3": [127, 127, 5], "4": [128, 127, 1], "5": [132, 130, 0], "6": [121, 123, 0], "7": [134, 137, 0], "8": [135, 135, 1], "9": [141, 135, 0], "10": [12, 110, 123], "11": [13, 101, 115], "12": [9, 86, 96], "13": [13, 109, 123], "14": [9, 105, 117], "15": [7, 96, 104], "16": [13, 108, 114], "17": [9, 98, 106], "18": [12, 101, 107], "19": [162, 61, 15], "20": [154, 54, 5], "21": [129, 42, 12], "22": [161, 61, 12], "23": [161, 60, 14], "24": [146, 44, 6], "25": [166, 60, 12], "26": [150, 48, 10], "27": [156, 52, 13], "28": [6, 54, 200], "29": [5, 53, 189], "30": [5, 42, 156], "31": [6, 54, 200], "32": [6, 47, 191], "33": [4, 44, 176], "34": [4, 52, 188], "35": [3, 47, 180], "36": [8, 45, 186], "37": [115, 5, 14], "38": [108, 4, 1], "39": [94, 3, 0], "40": [115, 5, 6], "41": [114, 6, 6], "42": [104, 4, 2], "43": [121, 2, 6], "44": [105, 5, 3], "45": [112, 4, 4], "46": [180, 200, 235], "47": [190, 211, 240], "48": [204, 219, 250], "49": [199, 218, 250], "50": [208, 221, 253], "51": [197, 214, 244], "52": [205, 226, 255], "53": [212, 227, 250], "54": [210, 225, 246]}""":
                    results.append("PASS: 3x3x3")
                else:
                    results.append("FAIL: 3x3x3")

            elif size == 4:
                if output == """{"1": [150, 178, 5], "2": [162, 192, 6], "3": [171, 201, 5], "4": [191, 212, 11], "5": [166, 195, 7], "6": [185, 208, 4], "7": [185, 210, 4], "8": [183, 208, 2], "9": [180, 213, 20], "10": [197, 222, 9], "11": [195, 219, 9], "12": [187, 212, 7], "13": [198, 225, 36], "14": [202, 224, 27], "15": [197, 220, 18], "16": [201, 218, 16], "17": [49, 198, 104], "18": [39, 180, 88], "19": [31, 161, 73], "20": [27, 144, 66], "21": [43, 197, 101], "22": [36, 192, 93], "23": [33, 177, 80], "24": [34, 162, 75], "25": [40, 189, 95], "26": [31, 191, 91], "27": [30, 180, 80], "28": [27, 168, 76], "29": [42, 191, 97], "30": [32, 183, 88], "31": [30, 180, 83], "32": [35, 177, 77], "33": [240, 120, 106], "34": [229, 100, 79], "35": [216, 85, 65], "36": [199, 76, 58], "37": [239, 117, 96], "38": [241, 107, 82], "39": [235, 96, 75], "40": [218, 85, 68], "41": [237, 107, 83], "42": [240, 100, 77], "43": [232, 92, 67], "44": [224, 89, 70], "45": [241, 108, 91], "46": [237, 98, 77], "47": [235, 93, 79], "48": [238, 97, 80], "49": [4, 118, 242], "50": [6, 109, 237], "51": [10, 98, 221], "52": [8, 87, 205], "53": [3, 119, 242], "54": [2, 116, 240], "55": [11, 106, 234], "56": [8, 96, 220], "57": [2, 116, 240], "58": [4, 114, 239], "59": [4, 109, 236], "60": [10, 102, 229], "61": [3, 116, 236], "62": [5, 110, 237], "63": [4, 107, 235], "64": [4, 109, 234], "65": [128, 4, 2], "66": [112, 3, 6], "67": [99, 4, 0], "68": [85, 4, 0], "69": [129, 4, 2], "70": [128, 4, 2], "71": [113, 5, 5], "72": [103, 3, 1], "73": [124, 6, 2], "74": [120, 7, 1], "75": [116, 5, 0], "76": [111, 3, 3], "77": [130, 5, 3], "78": [120, 5, 0], "79": [113, 5, 5], "80": [119, 4, 0], "81": [165, 171, 187], "82": [182, 189, 205], "83": [188, 195, 211], "84": [205, 207, 206], "85": [184, 190, 206], "86": [199, 205, 221], "87": [202, 208, 224], "88": [199, 205, 221], "89": [200, 207, 223], "90": [210, 216, 232], "91": [208, 214, 230], "92": [201, 207, 223], "93": [214, 221, 237], "94": [215, 221, 237], "95": [210, 216, 232], "96": [212, 215, 222]}""":
                    results.append("PASS: 4x4x4")
                else:
                    results.append("FAIL: 4x4x4")

        print('\n'.join(results))

    else:
        print(json.dumps(extract_rgb_pixels(args.size, False)))
