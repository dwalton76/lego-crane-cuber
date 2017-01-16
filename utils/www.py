#!/usr/bin/env python3

from copy import deepcopy
from pprint import pformat
import logging
import math
import json
import sys


def convert_key_strings_to_int(data):
    result = {}
    for (key, value) in data.items():
        if key.isdigit():
            result[int(key)] = value
        else:
            result[key] = value
    return result


def write_header(fh, size):
    """
    Write the <head> including css
    """
    side_margin = 10
    square_size = 40

    fh.write("""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
div.clear {
    clear: both;
}

div.clear_left {
    clear: left;
}

div.side {
    margin: %dpx;
    float: left;
}

""" % side_margin)

    for x in range(1, size-1):
        fh.write("div.col%d,\n" % x)

    fh.write("""div.col%d {
    float: left;
}

div.col%d {
    margin-left: %dpx;
}
div#upper,
div#down {
    margin-left: %dpx;
}
""" % (size-1,
       size,
       (size - 1) * square_size,
       (size * square_size) + ((size - 1) * side_margin)))

    fh.write("""
div.square {
    width: %dpx;
    height: %dpx;
    color: black;
    font-weight: bold;
    line-height: %dpx;
    text-align: center;
}

div.square span {
  display:        inline-block;
  vertical-align: middle;
  line-height:    normal;
}

</style>
<title>CraneCuber</title>
</head>
<body>
    """ % (square_size, square_size, square_size))


def get_important_square_indexes(size):
    squares_per_side = size * size
    min_square = 1
    max_square = squares_per_side * 6
    first_squares = []
    last_squares = []

    for index in range(1, max_square + 1):
        if (index - 1) % squares_per_side == 0:
            first_squares.append(index)
        elif index % squares_per_side == 0:
            last_squares.append(index)

    last_UBD_squares = (last_squares[0], last_squares[4], last_squares[5])
    #log.info("first    squares: %s" % pformat(first_squares))
    #log.info("last     squares: %s" % pformat(last_squares))
    #log.info("last UBD squares: %s" % pformat(last_UBD_squares))
    return (first_squares, last_squares, last_UBD_squares)


def write_cube(fh, cube, size):
    col = 1
    squares_per_side = size * size
    min_square = 1
    max_square = squares_per_side * 6

    sides = ('upper', 'left', 'front', 'right', 'back', 'down')
    side_index = -1
    (first_squares, last_squares, last_UBD_squares) = get_important_square_indexes(size)

    for index in range(1, max_square + 1):
        if index in first_squares:
            side_index += 1
            fh.write("<div class='side' id='%s'>\n" % sides[side_index])

        (red, green, blue) = cube[index]
        fh.write("    <div class='square col%d' title='(%d, %d, %d)' style='background-color: #%s%s%s;'><span>%s</span></div>\n" %
            (col, red, green, blue,
             str(hex(red))[2:].zfill(2),
             str(hex(green))[2:].zfill(2),
             str(hex(blue))[2:].zfill(2),
             str(index).zfill(2)))

        if index in last_squares:
            fh.write("</div>\n")

            if index in last_UBD_squares:
                fh.write("<div class='clear'></div>\n")

        col += 1

        if col == size + 1:
            col = 1


def write_footer(fh):
    fh.write("</body>\n")
    fh.write("</html>\n")


def rotate_2d_list(squares_list):
    """
    http://stackoverflow.com/questions/8421337/rotating-a-two-dimensional-array-in-python
    """
    result = []
    for x in zip(*squares_list[::-1]):
        result.append(x)
    return result


def rotate_clockwise(squares_list):
    return rotate_2d_list(squares_list)


def rotate_counter_clockwise(squares_list):
    squares_list = rotate_2d_list(squares_list)
    squares_list = rotate_2d_list(squares_list)
    squares_list = rotate_2d_list(squares_list)
    return squares_list


def compress_2d_list(squares_list):
    """
    Convert 2d list to a 1d list
    """
    result = []
    for row in squares_list:
        for col in row:
            result.append(col)
    return result


def build_2d_list(squares_list):
    """
    Convert 1d list to a 2d list
    squares_list is for a single side
    """
    result = []
    row = []

    squares_per_side = len(squares_list)
    size = int(math.sqrt(squares_per_side))
    #log.info("build_2d_list() squares_per_side %d, size %d" % (squares_per_side, size))

    for (square_index, x) in enumerate(squares_list):
        # log.info("square_index %d, x %s" % (square_index, pformat(x)))
        row.append(x)

        if (square_index + 1) % size == 0:
            result.append(row)
            row = []

    return result


def get_face_min_max_squares(cube, face):
    if face == 'U':
        face_number = 0
    elif face == 'L':
        face_number = 1
    elif face == 'F':
        face_number = 2
    elif face == 'R':
        face_number = 3
    elif face == 'B':
        face_number = 4
    elif face == 'D':
        face_number = 5

    squares_per_side = len(cube.keys()) / 6
    size = int(math.sqrt(squares_per_side))
    min_square = int((face_number * squares_per_side ) + 1)
    max_square = int(min_square + squares_per_side - 1)
    # log.info("side %s, size %d, squares_per_side %d, min/max square %d/%d" % (face, size, squares_per_side, min_square, max_square))

    return (min_square, max_square)


def get_face_as_2d_list(cube, face):
    result = []
    (min_square, max_square) = get_face_min_max_squares(cube, face)

    for square_index in range(min_square, max_square + 1):
        result.append(cube[square_index])

    # log.info("get_face_as_2d_list() side %s, 1d list\n%s\n" % (face, pformat(result)))
    result = build_2d_list(result)

    # log.info("get_face_as_2d_list() side %s, 2d list\n%s\n" % (face, pformat(result)))
    return result


def run_action(cube, action):
    """
    cube is a dictionary where the key is the square_index and the
    value is that square's RGB as a tuple
    """
    result = deepcopy(cube)
    # log.info("run_action %s on cube\n%s\n" % (action, pformat(cube)))

    squares_per_side = int(len(cube.keys()) / 6)
    size = int(math.sqrt(squares_per_side))

    if action.endswith("'") or action.endswith("`"):
        reverse = True
        action = action[0:-1]
    else:
        reverse = False

    if 'w' in action:
        rows_to_rotate = 2
        action = action.replace('w', '')
    else:
        rows_to_rotate = 1

    if '2' in action:
        quarter_turns = 2
        action = action.replace('2', '')
    else:
        quarter_turns = 1

    side_name = action
    if side_name not in ('U', 'L', 'F', 'R', 'B', 'D'):
        raise Exception("Invalid side name %s" % side_name)

    (min_square, max_square) = get_face_min_max_squares(cube, side_name)

    # rotate the face...this is the same for all sides
    for turn in range(quarter_turns):
        face = get_face_as_2d_list(cube, side_name)

        if reverse:
            face = rotate_counter_clockwise(face)
        else:
            face = rotate_clockwise(face)

        face = compress_2d_list(face)

        for (index, rgb) in enumerate(face):
            square_index = min_square + index
            result[square_index] = rgb
        cube = deepcopy(result)

    if side_name == "U":

        for turn in range(quarter_turns):

            # rotate the connecting row(s) of the surrounding sides
            for row in range(rows_to_rotate):
                left_first_square = squares_per_side + 1 + (row * size)
                front_first_square = (squares_per_side * 2) + 1 + (row * size)
                right_first_square = (squares_per_side * 3) + 1 + (row * size)
                back_first_square = (squares_per_side * 4) + 1 + (row * size)

                if reverse:
                    for square_index in range(left_first_square, left_first_square + size):
                        result[square_index] = cube[square_index + (3 * squares_per_side)]

                    for square_index in range(front_first_square, front_first_square + size):
                        result[square_index] = cube[square_index - squares_per_side]

                    for square_index in range(right_first_square, right_first_square + size):
                        result[square_index] = cube[square_index - squares_per_side]

                    for square_index in range(back_first_square, back_first_square + size):
                        result[square_index] = cube[square_index - squares_per_side]

                else:
                    for square_index in range(left_first_square, left_first_square + size):
                        result[square_index] = cube[square_index + squares_per_side]

                    for square_index in range(front_first_square, front_first_square + size):
                        result[square_index] = cube[square_index + squares_per_side]

                    for square_index in range(right_first_square, right_first_square + size):
                        result[square_index] = cube[square_index + squares_per_side]

                    for square_index in range(back_first_square, back_first_square + size):
                        result[square_index] = cube[square_index - (3 * squares_per_side)]

            cube = deepcopy(result)

    elif side_name == "F":

        for turn in range(quarter_turns):

            # rotate the connecting row(s) of the surrounding sides
            for row in range(rows_to_rotate):
                top_first_square = (squares_per_side - size) + 1 - (row * size)
                left_first_square = squares_per_side + 4 - row
                left_last_square = left_first_square + ((size - 1) * size)
                down_first_square = (squares_per_side * 5) + 1 + (row * size)
                right_first_square = (squares_per_side * 3) + 1 + row
                right_last_square = right_first_square + ((size - 1) * size)

                log.info("top first %d" % top_first_square)
                log.info("left first %d, last %d" % (left_first_square, left_last_square))
                log.info("down first %d" % down_first_square)
                log.info("right first %d, last %d" % (right_first_square, right_last_square))

                top_squares = []
                for square_index in range(top_first_square, top_first_square + size):
                    top_squares.append(cube[square_index])

                left_squares = []
                for square_index in range(left_first_square, left_last_square + 1, size):
                    left_squares.append(cube[square_index])

                down_squares = []
                for square_index in range(down_first_square, down_first_square + size):
                    down_squares.append(cube[square_index])

                right_squares = []
                for square_index in range(right_first_square, right_last_square + 1, size):
                    right_squares.append(cube[square_index])

                if reverse:
                    right_squares = list(reversed(right_squares))
                    for (index, square_index) in enumerate(range(top_first_square, top_first_square + size)):
                        result[square_index] = right_squares[index]

                    for (index, square_index) in enumerate(range(left_first_square, left_last_square + 1, size)):
                        result[square_index] = top_squares[index]

                    left_squares = list(reversed(left_squares))
                    for (index, square_index) in enumerate(range(down_first_square, down_first_square + size)):
                        result[square_index] = left_squares[index]

                    for (index, square_index) in enumerate(range(right_first_square, right_last_square + 1, size)):
                        result[square_index] = down_squares[index]

                else:
                    left_squares = list(reversed(left_squares))
                    for (index, square_index) in enumerate(range(top_first_square, top_first_square + size)):
                        result[square_index] = left_squares[index]

                    for (index, square_index) in enumerate(range(left_first_square, left_last_square + 1, size)):
                        result[square_index] = down_squares[index]

                    right_squares = list(reversed(right_squares))
                    for (index, square_index) in enumerate(range(down_first_square, down_first_square + size)):
                        result[square_index] = right_squares[index]

                    for (index, square_index) in enumerate(range(right_first_square, right_last_square + 1, size)):
                        result[square_index] = top_squares[index]

            cube = deepcopy(result)

    elif side_name == "D":

        # dwalton here now
        for turn in range(quarter_turns):

            # rotate the connecting row(s) of the surrounding sides
            for row in range(rows_to_rotate):
                left_first_square = (squares_per_side * 2) - size + 1 - (row * size)
                front_first_square = (squares_per_side * 3) - size + 1 - (row * size)
                right_first_square = (squares_per_side * 4) - size + 1 - (row * size)
                back_first_square = (squares_per_side * 5) - size + 1 - (row * size)

                if reverse:
                    for square_index in range(left_first_square, left_first_square + size):
                        result[square_index] = cube[square_index + squares_per_side]

                    for square_index in range(front_first_square, front_first_square + size):
                        result[square_index] = cube[square_index + squares_per_side]

                    for square_index in range(right_first_square, right_first_square + size):
                        result[square_index] = cube[square_index + squares_per_side]

                    for square_index in range(back_first_square, back_first_square + size):
                        result[square_index] = cube[square_index - (3 * squares_per_side)]

                else:
                    for square_index in range(left_first_square, left_first_square + size):
                        result[square_index] = cube[square_index + (3 * squares_per_side)]

                    for square_index in range(front_first_square, front_first_square + size):
                        result[square_index] = cube[square_index - squares_per_side]

                    for square_index in range(right_first_square, right_first_square + size):
                        result[square_index] = cube[square_index - squares_per_side]

                    for square_index in range(back_first_square, back_first_square + size):
                        result[square_index] = cube[square_index - squares_per_side]

            cube = deepcopy(result)

    else:
        raise Exception("Unsupported action %s" % action)

    return result


if __name__ == '__main__':
    log = logging.getLogger(__name__)

    # logging.basicConfig(filename='rubiks.log',
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
    log = logging.getLogger(__name__)

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

    with open('colors_raw.json', 'r') as fh:
        output = fh.readlines()[0]
        raw = json.loads(output)
        raw = convert_key_strings_to_int(raw)

    with open('colors_resolved.json', 'r') as fh:
        output = ''.join(fh.readlines())
        resolved = json.loads(output)

    square_count = len(raw.keys())
    size = int(math.sqrt(square_count / 6))

    with open('foo.html', 'w') as fh:
        write_header(fh, size)

        # Uncomment to display a cube containing the raw RGB values extracted from the scans
        # write_cube(fh, raw, size)

        # Build dict where the RGB values are the RGB colors of the square's finalSide
        cube = {}
        for (square_index, value) in resolved['squares'].items():
            final_side = value['finalSide']
            cube[square_index] = (
                int(resolved['sides'][final_side]['red']),
                int(resolved['sides'][final_side]['green']),
                int(resolved['sides'][final_side]['blue']),
            )
        cube = convert_key_strings_to_int(cube)

        # Display the initial cube
        write_cube(fh, cube, size)

        # Practice rotating and print the results
        cube = run_action(cube, "Dw'")
        write_cube(fh, cube, size)

        write_footer(fh)
