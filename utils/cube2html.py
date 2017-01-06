#!/usr/bin/env python3

import json
import sys


cube_input = sys.argv[1]

cube = json.loads(cube_input)
squares = len(cube.keys())

col = 1
print("""<!DOCTYPE html>
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
    margin: 10px;
    float: left;
}
""")


if squares == 96:
    print("""
div.col1,
div.col2,
div.col3 {
    float: left;
}

div.col4 {
    margin-left: 120px;
}

div#upper,
div#bottom {
    margin-left: 180px;
}

""")

elif squares == 54:
    print("""
div.col1,
div.col2 {
    float: left;
}

div.col3 {
    margin-left: 80px;
}

div#upper,
div#bottom {
    margin-left: 150px;
}

""")

elif squares == 24:
    print("""
div.col1 {
    float: left;
}

div.col2 {
    margin-left: 40px;
}

div#upper,
div#bottom {
    margin-left: 110px;
}
""")


print("""
div.square {
    width: 40px;
    height: 40px;
    color: black;
    font-weight: bold;
    line-height: 40px;
    text-align: center;
}

div.square span {
  display:        inline-block;
  vertical-align: middle;
  line-height:    normal;
}

</style>
<title>Title of the document</title>
</head>
<body>
""")


if squares == 96:
    '''
    The squares are numbered like so:

             01 02 03 04
             05 06 07 08
             09 10 11 12
             13 14 15 16

17 18 19 20  33 34 35 36  49 50 51 52  65 66 67 68
21 22 23 24  37 38 39 40  53 54 55 56  69 70 71 72
25 26 27 28  41 42 43 44  57 58 59 60  73 74 75 76
29 30 31 32  45 46 47 48  61 62 63 64  77 78 79 80

             81 82 83 84
             85 86 87 88
             89 90 91 92
             93 94 95 96
    '''

    for index in range(1, 97):

        if index == 1:
            print("<div class='side' id='upper'>")

        elif index == 17:
            print("<div class='side' id='left'>")

        elif index == 33:
            print("<div class='side' id='front'>")

        elif index == 49:
            print("<div class='side' id='right'>")

        elif index == 65:
            print("<div class='side' id='back'>")

        elif index == 81:
            print("<div class='side' id='bottom'>")

        (red, green, blue) = cube[str(index)]
        print("<div class='square col%d' style='background-color: #%s%s%s;'><span>%s</span></div>" %
            (col,
             str(hex(red))[2:].zfill(2),
             str(hex(green))[2:].zfill(2),
             str(hex(blue))[2:].zfill(2),
             str(index).zfill(2)))

        if index in (16, 32, 48, 64, 80, 96):
            print("</div>")

        col += 1

        if col == 5:
            # print("<div class='clear_left'></div>")
            col = 1

        if index == 16 or index == 80 or index == 96:
            print("<div class='clear'></div>")

elif squares == 54:
    '''
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
    '''

    for index in range(1, 55):

        if index == 1:
            print("<div class='side' id='upper'>")

        elif index == 10:
            print("<div class='side' id='left'>")

        elif index == 19:
            print("<div class='side' id='front'>")

        elif index == 28:
            print("<div class='side' id='right'>")

        elif index == 37:
            print("<div class='side' id='back'>")

        elif index == 46:
            print("<div class='side' id='bottom'>")

        (red, green, blue) = cube[str(index)]
        print("<div class='square col%d' style='background-color: #%s%s%s;'><span>%s</span></div>" %
            (col,
             str(hex(red))[2:].zfill(2),
             str(hex(green))[2:].zfill(2),
             str(hex(blue))[2:].zfill(2),
             str(index).zfill(2)))

        if index in (9, 18, 27, 36, 45, 54):
            print("</div>")

        col += 1

        if col == 4:
            # print("<div class='clear_left'></div>")
            col = 1

        if index == 9 or index == 45 or index == 54:
            print("<div class='clear'></div>")

elif squares == 24:
    '''
    The squares are numbered like so:

           01 02
           03 04
    05 06  09 10  13 14  17 18
    07 08  11 12  15 16  19 20
           21 22
           23 24
    '''

    for index in range(1, 25):
        if index == 1:
            print("<div class='side' id='upper'>")

        elif index == 5:
            print("<div class='side' id='left'>")

        elif index == 9:
            print("<div class='side' id='front'>")

        elif index == 13:
            print("<div class='side' id='right'>")

        elif index == 17:
            print("<div class='side' id='back'>")

        elif index == 21:
            print("<div class='side' id='bottom'>")

        (red, green, blue) = cube[str(index)]
        print("<div class='square col%d' style='background-color: #%s%s%s;'><span>%s</span></div>" %
            (col,
             str(hex(red))[2:].zfill(2),
             str(hex(green))[2:].zfill(2),
             str(hex(blue))[2:].zfill(2),
             str(index).zfill(2)))

        if index in (4, 8, 12, 16, 20, 24):
            print("</div>")

        col += 1

        if col == 3:
            # print("<div class='clear_left'></div>")
            col = 1

        if index == 4 or index == 20 or index == 24:
            print("<div class='clear'></div>")

else:
    raise Exception("Only 2x2x2 and 3x3x3 cubes are supported")

print("</body>")
print("</html>")
