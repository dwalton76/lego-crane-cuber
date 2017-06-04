#!/usr/bin/env python2

"""
Author: Igor Maculan - n3wtron@gmail.com
A Simple mjpg stream http server

https://gist.github.com/n3wtron/4624820
"""

# sudo apt-get install python-opencv
import cv2

# sudo apt-get install python-pil
from PIL import Image

import logging
import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import StringIO
import time

log = logging.getLogger(__name__)

capture = None
shutdown = False

class CamHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()

            while not shutdown:
                try:
                    rc,img = capture.read()

                    if not rc:
                        log.info("Failed to capture image")
                        continue

                    imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                    jpg = Image.fromarray(imgRGB)
                    tmpFile = StringIO.StringIO()
                    jpg.save(tmpFile,'JPEG')
                    self.wfile.write("--jpgboundary")
                    self.send_header('Content-type','image/jpeg')
                    self.send_header('Content-length',str(tmpFile.len))
                    self.end_headers()
                    jpg.save(self.wfile,'JPEG')
                    time.sleep(0.05)
                except Exception as e:
                    log.exception(e)
                    break
        else:
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('<a href="/cam.mjpg">camera</a>')
            self.wfile.write('</body></html>')


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def main():
    global capture
    capture = cv2.VideoCapture(0)
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320); 
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240);
    capture.set(cv2.cv.CV_CAP_PROP_SATURATION,0.2);
    global img
    server = None

    try:
        PORT = 8000
        server = ThreadedHTTPServer(('0.0.0.0', PORT), CamHandler)
        log.info("server started on port %d" % PORT)
        server.serve_forever()
    except:
        global shutdown
        log.info("Caught Exception...shutting down")

        shutdown = True
        if capture:
            capture.release()

        if server:
            server.shutdown
            server.socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
    log = logging.getLogger(__name__)

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

    main()
