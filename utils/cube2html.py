#!/usr/bin/env python3

import json

# {"1": [7, 6, 22], "2": [2, 5, 20], "3": [7, 6, 20], "4": [6, 3, 14], "5": [10, 7, 24], "6": [6, 6, 18], "7": [17, 29, 69], "8": [131, 149, 127], "9": [124, 4, 16], "10": [171, 76, 58], "11": [155, 189, 92], "12": [122, 1, 6], "13": [206, 239, 255], "14": [7, 117, 150], "15": [5, 41, 163], "16": [129, 3, 6], "17": [8, 109, 139], "18": [149, 69, 46], "19": [158, 193, 89], "20": [167, 73, 21], "21": [198, 240, 254], "22": [172, 72, 22], "23": [199, 243, 254], "24": [145, 182, 69], "25": [8, 121, 135], "26": [114, 4, 3], "27": [196, 238, 252], "28": [4, 144, 169], "29": [7, 61, 196], "30": [6, 130, 154], "31": [132, 18, 18], "32": [9, 55, 190], "33": [2, 130, 141], "34": [170, 91, 25], "35": [8, 124, 139], "36": [153, 87, 37], "37": [157, 190, 101], "38": [10, 120, 147], "39": [146, 182, 84], "40": [152, 186, 89], "41": [152, 187, 87], "42": [167, 63, 26], "43": [206, 239, 255], "44": [191, 232, 254], "45": [9, 44, 170], "46": [22, 32, 41], "47": [16, 43, 156], "48": [16, 41, 134], "49": [99, 17, 40], "50": [129, 4, 8], "51": [160, 66, 41], "52": [208, 245, 251], "53": [125, 6, 8], "54": [14, 112, 151]}

cube_input = """
{"1": [255, 255, 255], "2": [255, 255, 255], "3": [255, 255, 255], "4": [211, 78, 53], "5": [255, 255, 255], "6": [255, 255, 255], "7": [255, 255, 255], "8": [149, 255, 219], "9": [255, 255, 255], "10": [255, 255, 255], "11": [255, 255, 255], "12": [156, 255, 232], "13": [255, 255, 255], "14": [255, 255, 255], "15": [255, 255, 255], "16": [164, 255, 225], "17": [152, 255, 218], "18": [135, 255, 193], "19": [116, 255, 168], "20": [98, 220, 139], "21": [255, 255, 218], "22": [255, 255, 201], "23": [255, 255, 178], "24": [255, 255, 157], "25": [255, 255, 211], "26": [255, 255, 204], "27": [255, 255, 188], "28": [255, 255, 171], "29": [255, 255, 177], "30": [255, 255, 176], "31": [255, 255, 170], "32": [255, 255, 169], "33": [197, 70, 48], "34": [191, 66, 43], "35": [154, 57, 39], "36": [255, 255, 242], "37": [181, 255, 255], "38": [171, 255, 255], "39": [146, 255, 220], "40": [255, 255, 255], "41": [181, 255, 255], "42": [178, 255, 255], "43": [161, 255, 242], "44": [255, 255, 255], "45": [162, 255, 229], "46": [156, 255, 234], "47": [148, 255, 219], "48": [255, 255, 255], "49": [203, 71, 45], "50": [191, 67, 48], "51": [161, 59, 42], "52": [49, 99, 140], "53": [253, 82, 55], "54": [249, 80, 52], "55": [227, 75, 46], "56": [62, 132, 192], "57": [255, 81, 53], "58": [255, 80, 52], "59": [241, 80, 49], "60": [69, 142, 209], "61": [242, 77, 48], "62": [228, 74, 47], "63": [213, 69, 45], "64": [67, 150, 200], "65": [255, 255, 255], "66": [255, 255, 163], "67": [255, 230, 128], "68": [255, 191, 113], "69": [255, 255, 255], "70": [74, 186, 255], "71": [66, 164, 240], "72": [61, 134, 194], "73": [255, 255, 255], "74": [76, 197, 255], "75": [70, 180, 255], "76": [66, 147, 213], "77": [255, 255, 255], "78": [68, 172, 251], "79": [67, 157, 235], "80": [68, 153, 203], "81": [255, 255, 254], "82": [255, 255, 255], "83": [255, 255, 255], "84": [68, 152, 206], "85": [255, 255, 255], "86": [255, 255, 255], "87": [255, 255, 255], "88": [66, 163, 241], "89": [255, 255, 255], "90": [255, 255, 255], "91": [255, 255, 255], "92": [69, 175, 254], "93": [255, 255, 255], "94": [255, 255, 255], "95": [255, 255, 255], "96": [255, 255, 178]}
"""

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
