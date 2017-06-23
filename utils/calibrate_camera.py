#!/usr/bin/env python2

import cv2

cam = cv2.VideoCapture(0)
cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 352)
cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)

#print("calling cam.read")
#(ret, image) = cam.read() # captures image
#print("end     cam.read")
#cv2.imshow("Test Picture", im) # displays captured image
#cv2.imwrite("test.png", image) # writes image test.bmp to disk
#print("end     imwrite")

# cam.set(cv2.cv.CV_CAP_PROP_SATURATION, 0.05)
width = cam.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
height = cam.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
brightness = cam.get(cv2.cv.CV_CAP_PROP_BRIGHTNESS) * 100
contrast = cam.get(cv2.cv.CV_CAP_PROP_CONTRAST) * 100
saturation = cam.get(cv2.cv.CV_CAP_PROP_SATURATION) * 100
#hue = cam.get(cv2.cv.CV_CAP_PROP_HUE)
gain = cam.get(cv2.cv.CV_CAP_PROP_GAIN) * 100
#exposure = cam.get(cv2.cv.CV_CAP_PROP_EXPOSURE)
cam.release()

print "Brightness : %s" % brightness
print "Contrast   : %s" % contrast
print "Saturation : %s" % saturation
print "Gain       : %s" % gain

with open('fswebcam.conf', 'w') as fh:
    fh.write('device /dev/video0\n')
    fh.write('no-timestamp\n')
    fh.write('no-title\n')
    fh.write('no-subtitle\n')
    fh.write('no-banner\n')
    fh.write('no-info\n')
    fh.write('resolution 352x240\n')
    fh.write('png 1\n')

    if brightness:
        fh.write('set "Brightness"=%s%%\n' % brightness)

    if contrast:
        fh.write('set "Contrast"=%s%%\n' % contrast)

    if saturation:
        fh.write('set "Saturation"=%s%%\n' % saturation)

    if gain:
        fh.write('set "Gain"=%s%%\n' % gain)
