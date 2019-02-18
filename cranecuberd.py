#!/usr/bin/env python2
# This uses python2 instead of python3 because OpenCV is not yet supported in python3

import argparse
import cv2
import logging
import os
import random
import signal
import socket
import string
import subprocess
import sys
import numpy as np
from threading import Event

SCRATCHPAD_DIR = '/tmp/cranecuberd/'


class BrokenSocket(Exception):
    pass


def open_tcp_socket(address='0.0.0.0', port=10000):
    """
    open/return a TCP socket
    """
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((address, port))
    tcp_socket.listen(1)

    log.info("TCP socket opened on (%s, %s)" % (address, port))
    return tcp_socket


def get_random_string(length=6):
    """
    Return a random string 'length' characters long
    """
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


class CraneCuberDaemon(object):

    def __init__(self, dev_video, ip, port):
        self.shutdown_event = Event()
        self.dev_video = dev_video
        self.ip = ip
        self.port = port

    def __str__(self):
        return 'CraneCuberDaemon'

    def signal_handler(self, signal, frame):
        log.info("received SIGINT or SIGTERM")
        self.shutdown_event.set()

    def main(self):
        caught_exception = False

        # Log the process ID upon start-up.
        pid = os.getpid()
        log.info('cranecuberd started with PID %s for /dev/video%d' % (pid, self.dev_video))

        tcp_socket = open_tcp_socket(self.ip, self.port)

        while True:

            # Wrap everything else in try/except so that we can log errors
            # and exit cleanly
            try:
                if self.shutdown_event.is_set():
                    log.info("Shutdown signal RXed.  Breaking out of the loop.")
                    break

                try:
                    (connection, _) = tcp_socket.accept()
                except socket.error as e:
                    if isinstance(e.args, tuple) and e[0] == 4:
                        # 4 is 'Interrupted system call', a.k.a. SIGINT.
                        # The user wants to stop cranecuberd.
                        log.info("socket.accept() caught signal, starting shutdown")
                        raise BrokenSocket("socket.accept() caught signal, starting shutdown")
                    else:
                        log.info("socket hit error\n%s" % e)
                        tcp_socket.close()
                        tcp_socket = open_tcp_socket()
                        continue

                total_data = []

                # RX the entire packet
                while True:
                    data = connection.recv(4096)

                    # If the client is using python2 data will be a str but if they
                    # are using python3 data will be encoded and must be decoded to
                    # a str
                    if not isinstance(data, str):
                        data = data.decode()

                    data = data.strip()
                    log.info("RXed %s" % data)

                    total_data.append(data)
                    data = ''.join(total_data)

                    # Do we have the entire packet?
                    if data.startswith('<START>') and data.endswith('<END>'):

                        # Remove the <START> and <END>
                        data = data[7:-5]

                        if data.startswith('TAKE_PICTURE'):
                            side_name = data.strip().split(':')[1]
                            png_filename = os.path.join(SCRATCHPAD_DIR, 'rubiks-side-%s.png' % side_name)

                            if side_name == 'F':

                                for filename in os.listdir(SCRATCHPAD_DIR):
                                    if filename.endswith('.png'):
                                        os.unlink(os.path.join(SCRATCHPAD_DIR, filename))

                                # Take a pic but throw it away, we do this so the camera adjusts the current lighting conditions
                                camera = cv2.VideoCapture(self.dev_video)
                                camera.read()
                                del(camera)
                                camera = None

                                # Now take a pic, keep it and note the brightness, etc
                                camera = cv2.VideoCapture(self.dev_video)
                                (retval, img) = camera.read()

                                brightness = camera.get(cv2.CAP_PROP_BRIGHTNESS)
                                contrast = camera.get(cv2.CAP_PROP_CONTRAST)
                                saturation = camera.get(cv2.CAP_PROP_SATURATION)
                                gain = camera.get(cv2.CAP_PROP_GAIN)

                            else:
                                # Set the brightness, etc to be the same as when we took a pic of side F.
                                # This makes rubiks-color-resolver's job much easier.
                                camera = cv2.VideoCapture(self.dev_video)
                                camera.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
                                camera.set(cv2.CAP_PROP_CONTRAST, contrast)
                                camera.set(cv2.CAP_PROP_SATURATION, saturation)
                                camera.set(cv2.CAP_PROP_GAIN, gain)
                                (retval, img) = camera.read()

                            # If you do not delete the VideoCapture object opencv2 will sometimes return the
                            # exact same image when you call read() back-to-back.  This is really bad when
                            # you have flipped the cube to a new side and end up with a pic of the previous
                            # side.
                            del(camera)
                            camera = None

                            if retval:
                                # Save the image to disk
                                cv2.imwrite(png_filename, img)

                                size = os.path.getsize(png_filename)

                                if size:
                                    response = 'FINISHED: image %s is %d bytes' % (png_filename, size)
                                else:
                                    response = 'ERROR: image %s is 0 bytes' % png_filename
                            else:
                                response = 'ERROR: image %s camera.read() failed' % png_filename

                        elif data == 'GET_RGB_COLORS':
                            cmd = ['rubiks-cube-tracker.py', '--directory', SCRATCHPAD_DIR]
                            log.info("cmd: %s" % ' '.join(cmd))
                            response = subprocess.check_output(cmd).strip()

                        elif data.startswith('GET_CUBE_STATE:'):
                            cmd = ['rubiks-color-resolver.py', '--json', '--rgb', data[len('GET_CUBE_STATE:'):]]
                            log.info("cmd: %s" % ' '.join(cmd))
                            response = subprocess.check_output(cmd).strip()

                        elif data == 'GET_CUBE_STATE_FROM_PICS':
                            # Have not tested this
                            cmd = ['rubiks-cube-tracker.py', '--directory', SCRATCHPAD_DIR]
                            log.info("cmd: %s" % ' '.join(cmd))
                            rgb = subprocess.check_output(cmd).strip()

                            cmd = ['rubiks-color-resolver.py', '--json', '--rgb', rgb]
                            log.info("cmd: %s" % ' '.join(cmd))
                            response = subprocess.check_output(cmd).strip()

                        elif data.startswith('GET_SOLUTION:'):
                            cube_state = data.split(':')[1]

                            if len(cube_state) <= 96:
                                cpu_mode = "--normal"
                            else:
                                cpu_mode = "--fast"

                            cmd = "cd ~/rubiks-cube-NxNxN-solver/; ./usr/bin/rubiks-cube-solver.py %s --state %s" % (cpu_mode, cube_state)
                            log.info("cmd: %s" % cmd)
                            response = subprocess.check_output(cmd, shell=True).strip()

                        elif data == 'PING':
                            response = 'REPLY'

                        else:
                            log.warning("RXed %s (not supported)" % data)

                        # TX our response and close the socket
                        connection.send(response)
                        connection.close()
                        log.info("TXed %s response\n%s\n\n" % (data, response))

                        # We have the entire msg so break out of the inside 'while True' loop
                        break

            except Exception as e:
                log.exception(e)
                caught_exception = True
                break

        log.info('cranecuberd is stopping with PID %s' % pid)

        if tcp_socket:
            tcp_socket.close()
            tcp_socket = None

        if caught_exception:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="takepidc: daemon that takes webcam pics via OpenCV")
    parser.add_argument('-d', '--daemon', help='run as a daemon', action='store_true', default=False)
    parser.add_argument('--video', type=int, default=0, help='The X in /dev/videoX')
    parser.add_argument('--ip', type=str, default='')
    parser.add_argument('--port', type=int, default=10000)
    parser_args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s')
    log = logging.getLogger(__name__)
    logging.addLevelName(logging.ERROR, "\033[91m  %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m%s\033[0m" % logging.getLevelName(logging.WARNING))

    # barf if not running as root...we can't take a pic in that scenario
    if os.geteuid() != 0:
        print("cranecuberd.py must be run with root privs")
        sys.exit(1)

    if not os.path.exists(SCRATCHPAD_DIR):
        os.makedirs(SCRATCHPAD_DIR, mode=0755)

    ccd = CraneCuberDaemon(parser_args.video, parser_args.ip, parser_args.port)

    if parser_args.daemon:
        from daemon import DaemonContext
        context = DaemonContext(
            working_directory=SCRATCHPAD_DIR,
            signal_map={
                signal.SIGTERM: ccd.signal_handler,
                signal.SIGINT: ccd.signal_handler,
            }
        )

        context.open()
        with context:
            ccd.main()

    else:
        signal.signal(signal.SIGINT, ccd.signal_handler)
        signal.signal(signal.SIGTERM, ccd.signal_handler)
        ccd.main()
