#!/usr/bin/env python3

import json

cube_input = """
{"1": [3, 5, 30], "2": [141, 5, 15], "3": [115, 6, 12], "4": [76, 78, 129], "5": [136, 8, 23], "6": [68, 3, 7], "7": [133, 127, 173], "8": [123, 5, 19], "9": [54, 1, 9], "10": [155, 141, 164], "11": [219, 206, 224], "12": [197, 183, 206], "13": [231, 218, 236], "14": [219, 194, 223], "15": [128, 113, 134], "16": [233, 224, 245], "17": [201, 189, 211], "18": [80, 66, 79], "19": [83, 4, 10], "20": [15, 74, 88], "21": [7, 24, 34], "22": [190, 97, 118], "23": [11, 67, 82], "24": [4, 4, 6], "25": [155, 66, 88], "26": [11, 44, 49], "27": [11, 4, 11], "28": [133, 113, 60], "29": [196, 169, 92], "30": [131, 119, 69], "31": [248, 238, 211], "32": [57, 39, 35], "33": [5, 3, 6], "34": [189, 167, 130], "35": [24, 15, 20], "36": [13, 8, 15], "37": [125, 48, 30], "38": [181, 64, 31], "39": [164, 60, 35], "40": [122, 115, 159], "41": [9, 21, 71], "42": [4, 3, 11], "43": [94, 96, 147], "44": [7, 5, 10], "45": [13, 7, 9], "46": [10, 42, 53], "47": [184, 63, 32], "48": [162, 62, 36], "49": [103, 134, 152], "50": [176, 59, 41], "51": [90, 30, 19], "52": [98, 127, 143], "53": [123, 50, 43], "54": [9, 5, 4]}
"""

cube = json.loads(cube_input)
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

div.col1,
div.col2 {
    float: left;
}

div.col3 {
    margin-left: 80px;
}

div.square {
    width: 40px;
    height: 40px;
    color: white;
    font-weight: bold;
    line-height: 40px;
    text-align: center;
}

div#upper,
div#bottom {
    margin-left: 150px;
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

if len(cube.keys) == 54:
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

elif len(cube.keys) == 36:
    for index in range(1, 37):
        pass

else:
    raise Exception("Only 2x2x2 and 3x3x3 cubes are supported")

print("</body>")
print("</html>")
