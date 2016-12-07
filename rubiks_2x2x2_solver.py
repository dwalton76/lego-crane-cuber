#!/usr/bin/env python2

"""
100% of the credit for this 2x2x2 solver goes to
http://codegolf.stackexchange.com/questions/35002/solve-the-rubiks-pocket-cube
"""

import sys


'''
In the codegolf challenge they defined the input as

- -   A B   - -   - -
- -   C D   - -   - -

E F   G H   I J   K L
M N   O P   Q R   S T

- -   U V   - -   - -
- -   W X   - -   - -

But normally we number cubes like this

       01 02
       03 04
05 06  09 10  13 14  17 18
07 08  11 12  15 16  19 20
       21 22
       23 24

So we will define the former layout as "scramble" and the latter as "normal".
Convert the normal layout (sys.argv[1] must be in the 'normal' layout) to
the scramble layout.
'''
normal = list(sys.argv[1])
scramble = normal[0:4]
scramble.append(normal[4])
scramble.append(normal[5])
scramble.append(normal[8])
scramble.append(normal[9])
scramble.append(normal[12])
scramble.append(normal[13])
scramble.append(normal[16])
scramble.append(normal[17])
scramble.append(normal[6])
scramble.append(normal[7])
scramble.append(normal[10])
scramble.append(normal[11])
scramble.append(normal[14])
scramble.append(normal[15])
scramble.append(normal[18])
scramble.append(normal[19])
scramble.extend(normal[20:24])

o = ''.join
d = [{o((' ', x)[x in scramble[12] + scramble[19] + scramble[22]]for x in scramble):[]},
     {' ' * 4 + (scramble[12] * 2 + ' ' * 4 + scramble[19] * 2) * 2 + scramble[22] * 4:[]}]

for h in[0, 1] * 6:
    for s, x in d[h].items():
        for y in range(12):
            d[h][s] = x + [y - [1, -1, 1, 3][h * y % 4]]
            if s in d[1 - h]:
                result = o('RUF'[x / 4] + " 2'"[x % 4]for x in d[0][s] + d[1][s][::-1])
                result = result.replace('2', '2 ')
                result = result.replace("'", "' ")
                result = result.split()
                print ' '.join(result)
                sys.exit(0)
            s = o(s[ord(c) - 97] for c in'acahabcdnpbfegefhugiovjgqkciljdeklflmmmnnvoopxphrqdjrrbsstttuuqsviwwwkxx'[y / 4::3])

print "Could not find a solution"
sys.exit(1)
