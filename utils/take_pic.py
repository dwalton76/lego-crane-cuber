#!/usr/bin/env python2

import cv2

dev = 0
width = 352
height = 240
brightness = None
contrast = None
saturation = None
gain = None

with open('camera.conf', 'r') as fh:
    for line in fh:
        line = line.strip()

        if line.startswith('device'):
            # device /dev/video0
            dev = int(line[-1])

        elif line.startswith('resolution'):
            (width, height) = line.split()[1].split('x')
            width = int(width)
            height = int(height)

        elif line.startswith('brightness'):
            brightness = float(line.split()[1])

        elif line.startswith('contrast'):
            contrast = float(line.split()[1])

        elif line.startswith('saturation'):
            saturation = float(line.split()[1])

        elif line.startswith('gain'):
            gain = float(line.split()[1])

cam = cv2.VideoCapture(dev)
cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, width)
cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, height)
print "width      : %s" % width
print "height     : %s" % height

if brightness:
    print "brightness : %s" % brightness
    cam.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS, brightness)

if contrast:
    print "contrast   : %s" % contrast
    cam.set(cv2.cv.CV_CAP_PROP_CONTRAST, contrast)

if saturation:
    print "saturation : %s" % saturation
    cam.set(cv2.cv.CV_CAP_PROP_SATURATION, saturation)

if gain:
    print "gain       : %s" % gain
    cam.set(cv2.cv.CV_CAP_PROP_GAIN, gain)

print("calling cam.read")
(ret, image) = cam.read() # captures image
print("end     cam.read")
#cv2.imshow("Test Picture", im) # displays captured image
cv2.imwrite("foo.png", image) # writes image test.bmp to disk
print("end     imwrite")
cam.release()

