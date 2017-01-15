#!/usr/bin/env python2

from copy import deepcopy
from pprint import pformat
import argparse
import cv2
import logging
import json
import logging
import math
import numpy as np
import os
import sys

def get_candidate_neighbors(target_tuple, candidates, img_width, img_height):
    row_neighbors = 0
    col_neighbors = 0

    width_wiggle = int(img_width * 0.05)
    height_wiggle = int(img_height * 0.09)

    (_, _, _, _, target_cX, target_cY) = target_tuple

    for x in candidates:
        if x == target_tuple:
            continue
        (index, area, currentContour, approx, cX, cY) = x

        if abs(cX - target_cX) <= width_wiggle:
            col_neighbors += 1

        if abs(cY - target_cY) <= height_wiggle:
            row_neighbors += 1

    return (row_neighbors, col_neighbors)


def sort_by_row_col(candidates):
    result = []
    num_squares = len(candidates)
    squares_per_row = int(math.sqrt(num_squares))

    for row_index in xrange(squares_per_row):

        # We want the squares_per_row that are closest to the top
        tmp = []
        for (index, area, currentContour, approx, cX, cY) in candidates:
            tmp.append((cY, cX))
        top_row = sorted(tmp)[:squares_per_row]

        # Now that we have those, sort them from left to right
        top_row_left_right = []
        for (cY, cX) in top_row:
            top_row_left_right.append((cX, cY))
        top_row_left_right = sorted(top_row_left_right)


        log.info("row %d: %s" % (row_index, pformat(top_row_left_right)))
        candidates_to_remove = []
        for (target_cX, target_cY) in top_row_left_right:
            for (index, area, currentContour, approx, cX, cY) in candidates:
                if cX == target_cX and cY == target_cY:
                    result.append((index, area, currentContour, approx, cX, cY))
                    candidates_to_remove.append((index, area, currentContour, approx, cX, cY))
                    break

        for x in candidates_to_remove:
            candidates.remove(x)

    return result

def is_square(integer):
    root = math.sqrt(integer)

    if int(root + 0.5) ** 2 == integer:
        return True
    else:
        return False


def get_rubiks_squares(filename):
    debug = False

    image = cv2.imread(filename)
    (img_height, img_width) = image.shape[:2]

    # convert the image to grayscale
    # in the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    #if debug:
    #    cv2.imshow("gray", gray)
    #    cv2.waitKey(0)


    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    #if debug:
    #    cv2.imshow("blurred", blurred)
    #    cv2.waitKey(0)


    # Threshold settings from here:
    # http://opencvpython.blogspot.com/2012/06/sudoku-solver-part-2.html
    thresh = cv2.adaptiveThreshold(blurred, 255, 1, 1, 11, 2)

    #if debug:
    #    cv2.imshow("thresh", thresh)
    #    cv2.waitKey(0)


    # Use a very high h value so that we really blur the image to remove
    # all spots that might be in the rubiks squares...we want the rubiks
    # squares to be solid black
    denoised = cv2.fastNlMeansDenoising(thresh, h=120)

    if debug:
        cv2.imshow("denoised", denoised)
        cv2.waitKey(0)

    # Now invert the image so that the rubiks squares are white but most
    # of the rest of the image is black
    thresh2 = cv2.threshold(denoised, 10, 255, cv2.THRESH_BINARY_INV)[1]

    if debug:
        cv2.imshow("inverted", thresh2)
        cv2.waitKey(0)

    (contours, hierarchy) = cv2.findContours(thresh2.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    hierarchy = hierarchy[0] # get the actual inner list of hierarchy descriptions

    # http://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
    # http://stackoverflow.com/questions/11782147/python-opencv-contour-tree-hierarchy
    #
    # For each contour, find the bounding rectangle and draw it
    index = 0
    for component in zip(contours, hierarchy):
        currentContour = component[0]
        currentHierarchy = component[1]

        # currentHierarchy[2] of -1 means this contour has no children so we know
        # this is the "inside" contour for a square...some squares get two contours
        # due to the black border around the edge of the square
        if True or currentHierarchy[2] == -1:

            # approximate the contour
            peri = cv2.arcLength(currentContour, True)
            approx = cv2.approxPolyDP(currentContour, 0.1 * peri, True)
            area = cv2.contourArea(currentContour)

            if area > 100 and len(approx) >= 3:

                # compute the center of the contour
                M = cv2.moments(currentContour)
                if M["m00"]:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])

                    log.info("(%d, %d), area %d, corners %d" % (cX, cY, area, len(approx)))
                    candidates.append((index, area, currentContour, approx, cX, cY))
        index += 1

    # Remove contours that are off by themselves
    while True:
        candidates_to_remove = []

        for x in candidates:
            (row_neighbors, col_neighbors) = get_candidate_neighbors(x, candidates, img_width, img_height)
            if row_neighbors <= 1 or col_neighbors <= 1:
                candidates_to_remove.append(x)

        if candidates_to_remove:
            for x in candidates_to_remove:
                candidates.remove(x)
                # log.info("removed candidate")
        else:
            break

    num_squares = len(candidates)
    candidates = sort_by_row_col(deepcopy(candidates))
    data = []
    to_draw = []
    to_draw_approx = []

    for (index, area, contour, approx, cX, cY) in candidates:
        # We used to use the value of the center pixel
        #(blue, green, red) = map(int, image[cY, cX])
        #data.append((red, green, blue))

        # Now we use the mean value of the contour
        mask = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(mask, [contour], 0, 255, -1)
        (mean_blue, mean_green, mean_red, _)= map(int, cv2.mean(image, mask = mask))
        data.append((mean_red, mean_green, mean_blue))

        #log.info("normal BGR (%s, %s, %s), mean BGR (%s, %s, %s)" %\
        #    (blue, green, red, mean_blue, mean_green, mean_red))
        to_draw.append(contour)
        to_draw_approx.append(approx)

    if debug:
        # draw a blue line to show the contours we IDed as the squares of the cube
        cv2.drawContours(image, to_draw, -1, (255, 0, 0), 2)

        # draw a green line to show the approx for each contour
        # cv2.drawContours(image, to_draw_approx, -1, (0, 255, 0), 2)

        cv2.imshow("Rubiks Cube Squares", image)
        cv2.waitKey(0)
        # cv2.imwrite('foo.png', image)

    # Verify we found the right number of squares
    num_squares = len(candidates)
    if not is_square(num_squares):
        assert False, "Found %d squares which cannot be right" % num_squares

    return data


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


def extract_rgb_pixels(target_side):
    colors = {}
    squares_per_side = None

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

        # target_side is only True when we are debugging an image
        if target_side is not None and side != target_side:
            continue

        filename = "/tmp/rubiks-side-%s.png" % side

        if not os.path.exists(filename):
            print "ERROR: %s does not exists" % filename
            sys.exit(1)

        # data will be a list of (R, G, B) tuples, one entry for each square on a side
        data = get_rubiks_squares(filename)

        squares_per_side = len(data)
        size = int(math.sqrt(squares_per_side))
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
        my_indexes = compress_2d_array(my_indexes)
        log.info("%s my_indexes (final) %s" % (side, pformat(my_indexes)))

        for index in range(squares_per_side):
            square_index = my_indexes[index]
            (red, green, blue) = data[index]
            log.info("square %d, RGB (%d, %d, %d)" % (square_index, red, green, blue))

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

    if len(sys.argv) > 1:
        target_side = sys.argv[1]
    else:
        target_side = None

    print(json.dumps(extract_rgb_pixels(target_side)))
