#!/usr/bin/env python2

import cv2
import numpy as np
import sys


def picToAscii(filename):
    """
    We display the first scan in ascii so we can tell if the camera alignment is off
    """

    def transform(img):
        transformedAscii = []
        for i in img:
            temp = []
            for j in i:
                temp.append(asciiToNum[j])
            transformedAscii.append(temp)
        return transformedAscii

    def setupAsciiMapping():
        asciiToNum = {}
        characterSet = list('  ..,,::;;ii11ttffLL;;::..ii11ttL')

        for i in range(26):
            for j in range(10):
                asciiToNum[i*10+j]=characterSet[i]
        return asciiToNum

    def arrayToString(arr):
        '''
        ascii = ''
        for i in transformedAscii:
            ascii+= ' '.join(i)
            ascii+='\n'
        return ascii
        '''
        ascii = []
        for i in transformedAscii:
            ascii.append(' '.join(i))
            ascii.append('\n')
        return ''.join(ascii)

    asciiToNum = setupAsciiMapping()

    image = cv2.imread(filename)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    canny = cv2.Canny(blurred, 20, 40)
    kernel = np.ones((3,3), np.uint8)
    dilated = cv2.dilate(canny, kernel, iterations=2)
    small = cv2.resize(dilated, (0,0), fx=0.2, fy=0.2)

    transformedAscii = transform(small)
    return arrayToString(transformedAscii)

if __name__ == '__main__':
    print(picToAscii(sys.argv[1]))
