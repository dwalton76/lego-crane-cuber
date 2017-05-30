#!/usr/bin/env python2

import cv2

cam = cv2.VideoCapture(0)
cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 352)
cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)

# 0.20000000298023224
# cam.set(cv2.cv.CV_CAP_PROP_SATURATION, 0.05)


#test = cam.get(cv2.cv.CV_CAP_PROP_POS_MSEC)
#ratio = cam.get(cv2.cv.CV_CAP_PROP_POS_AVI_RATIO)
#frame_rate = cam.get(cv2.cv.CV_CAP_PROP_FPS)
width = cam.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
height = cam.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
brightness = cam.get(cv2.cv.CV_CAP_PROP_BRIGHTNESS)
contrast = cam.get(cv2.cv.CV_CAP_PROP_CONTRAST)
saturation = cam.get(cv2.cv.CV_CAP_PROP_SATURATION)
#hue = cam.get(cv2.cv.CV_CAP_PROP_HUE)
gain = cam.get(cv2.cv.CV_CAP_PROP_GAIN)
#exposure = cam.get(cv2.cv.CV_CAP_PROP_EXPOSURE)

#print("Test: ", test)
#print("Ratio: ", ratio)
#print("Frame Rate: ", frame_rate)

print("Height: ", height)
print("Width: ", width)
print("Brightness: ", brightness)
print("Contrast: ", contrast)
print("Saturation: ", saturation)
#print("Hue: ", hue)
print("Gain: ", gain)
#print("Exposure: ", exposure)

print("calling cam.read")
(ret, image) = cam.read() # captures image
print("end     cam.read")
#cv2.imshow("Test Picture", im) # displays captured image
cv2.imwrite("test.png", image) # writes image test.bmp to disk
print("end     imwrite")
cam.release()

