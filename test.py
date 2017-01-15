#!/usr/bin/env python3

from pprint import pformat
import subprocess
import json
import logging
import sys


def rgb_matches(text1, text2):
    result = True
    data1 = json.loads(text1)
    data2 = json.loads(text2)

    for (square_index, rgb1) in sorted(data1.items()):
        rgb2 = data2[square_index]
        if rgb1 != rgb2:
            resulit = False
            break

    return result


def get_rgb_delta(text1, text2):
    result = []
    data1 = json.loads(text1)
    data2 = json.loads(text2)

    for (square_index, rgb1) in sorted(data1.items()):
        rgb2 = data2[square_index]
        if rgb1 != rgb2:
            result.append("%2d: %14s != %-14s" % (int(square_index), pformat(rgb1), pformat(rgb2)))

    return '\n'.join(result)


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)5s: %(message)s')
log = logging.getLogger(__name__)

# Color the errors and warnings in red
logging.addLevelName(logging.ERROR, "\033[91m  %s\033[0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.WARNING, "\033[91m%s\033[0m" % logging.getLevelName(logging.WARNING))

# To add a test case:
# - place the cube in the robot, solve it
# - in the log output grab the "RGB json" and save that in a file in test-data
# - in the log output grab the "Final cube for kociema", this is what you put in the entry in the test_cases tuple
test_cases = (
    ('3x3x3 random 01',    'test-data/3x3x3-random-01.txt'),
    ('3x3x3 random 02',    'test-data/3x3x3-random-02.txt'),
    ('3x3x3 random 03',    'test-data/3x3x3-random-03.txt'),
)

results = []

for (desc, filename) in test_cases:
    test_dir = filename[0:-4]
    log.info("filename: %s" % filename)
    log.info("test_dir: %s" % test_dir)

    subprocess.call("cp %s/*.png /tmp/" % test_dir, shell=True)
    output = subprocess.check_output(['./extract_rgb_pixels.py']).decode('ascii').splitlines()[0].strip()

    with open(filename, 'r') as fh:
        expected_output = fh.readlines()[0].strip()

    if rgb_matches(expected_output, output):
        results.append("\033[92mPASS\033[0m: %s" % desc)
    else:
        results.append("\033[91mFAIL\033[0m: %s" % desc)
        results.append(get_rgb_delta(expected_output, output))
        results.append(output)

print('\n'.join(results))
