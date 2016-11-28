#!/usr/bin/env python3

"""
CraneCuber
A Rubiks cube solving robot made from EV3 + 42009
"""

from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C, InfraredSensor, TouchSensor
from ev3dev.helper import LargeMotor, MediumMotor, ColorSensor, MotorStall
from pprint import pformat
from rubiks_rgb_solver import RubiksColorSolver
from subprocess import check_output
from time import sleep
import json
import logging
import os
import signal
import sys
import time

log = logging.getLogger(__name__)

# negative moves to init position
# positive moves towards camera
# This should be 90 degrees but 110 is needed to account for play between the gears
FLIPPER_DEGREES = 110
FLIPPER_SPEED = 200

# negative move counter clockwise (viewed from above)
# positive move clockwise (viewed from above)
TURNTABLE_DEGREES = 150
TURNTABLE_SPEED = 200

# negative moves down
# positive moves up
ELEVATOR_SPEED_UP = 200
ELEVATOR_SPEED_DOWN = 50


class CraneCuber(object):

    def __init__(self, rows_and_cols=3, size_mm=57):
        self.shutdown = False
        self.rows_and_cols = rows_and_cols
        self.size_mm = size_mm
        self.square_size_mm = float(self.size_mm / self.rows_and_cols)
        self.elevator = LargeMotor(OUTPUT_A)
        self.flipper = MediumMotor(OUTPUT_B)
        self.turntable= LargeMotor(OUTPUT_C)
        self.touch_sensor = TouchSensor()
        self.motors = [self.elevator, self.flipper, self.turntable]
        self.rgb_solver = None
        self.cube = {}
        self.rows_in_turntable = 0
        self.facing_up = 'U'
        self.facing_down = 'D'
        self.facing_north = 'B'
        self.facing_west = 'L'
        self.facing_south = 'F'
        self.facing_east = 'R'
        signal.signal(signal.SIGTERM, self.signal_term_handler)
        signal.signal(signal.SIGINT, self.signal_int_handler)

        self.init_motors()
        self.center_pixels = []

        '''
        calibrate_filename = '/tmp/MINDCUB3R-usb-camera.json'
        with open(calibrate_filename, 'r') as fh:
            for square in json.load(fh):
                self.center_pixels.append((square.get('x'), square.get('y')))

        log.info("center_pixels\n%s" % pformat(self.center_pixels))
        '''

    def init_motors(self):

        for x in self.motors:
            if not x.connected:
                log.error("%s is not connected" % x)
                sys.exit(1)
            x.reset()

        # 'brake' stops but doesn't hold the motor in place
        # 'hold' stops and holds the motor in place
        log.info("Initialize elevator %s" % self.elevator)
        self.elevator.reset()
        self.elevator.stop(stop_action='brake')

        log.info("Initialize flipper %s" % self.flipper)
        self.flipper.run_forever(speed_sp=-60, stop_action='hold')
        self.flipper.wait_for_running()
        self.flipper.wait_for_stop()
        self.flipper.stop()
        self.flipper.reset()
        self.flipper.stop(stop_action='hold')
        self.flipper_at_init = True

        log.info("Initialize turntable %s" % self.turntable)
        self.turntable.reset()
        self.turntable.stop(stop_action='hold')

    def shutdown_robot(self):
        log.info('Shutting down')
        self.shutdown = True

        if self.rgb_solver:
            self.rgb_solver.shutdown = True

        for x in self.motors:
            x.shutdown = True

        for x in self.motors:
            x.stop(stop_action='brake')

    def signal_term_handler(self, signal, frame):
        log.error('Caught SIGTERM')
        self.shutdown_robot()

    def signal_int_handler(self, signal, frame):
        log.error('Caught SIGINT')
        self.shutdown_robot()

    def wait_for_touch_sensor(self):
        log.info('waiting for TouchSensor press')

        while True:
            if self.shutdown:
                break

            if self.touch_sensor.is_pressed:
                log.info('TouchSensor pressed')
                break

            sleep(0.01)

    def rotate(self, clockwise, quarter_turns):

        if self.shutdown:
            return

        assert quarter_turns > 0 and quarter_turns <= 2, "quarater_turns is %d, it must be between 0 and 2" % quarter_turns

        if clockwise:
            degrees = TURNTABLE_DEGREES * quarter_turns
        else:
            degrees = TURNTABLE_DEGREES * quarter_turns * -1

        current_pos = self.turntable.position
        final_pos = current_pos + degrees
        log.info("rotate_cube() %d quarter turns, clockwise %s, current_pos %d, final_pos %d" % (quarter_turns, clockwise, current_pos, final_pos))

        self.turntable.run_to_abs_pos(position_sp=final_pos,
                                      speed_sp=TURNTABLE_SPEED,
                                      stop_action='hold',
                                      ramp_up_sp=0)
        self.turntable.wait_for_running()
        self.turntable.wait_for_position(final_pos)
        self.turntable.wait_for_stop()

        # Only update the facing_XYZ variables if the entire side is turning.  For
        # a 3x3x3 this means the middle square is being turned, this happens if at
        # least two rows are up in the turntable
        if self.rows_in_turntable >= 2:
            orig_north = self.facing_north
            orig_west = self.facing_west
            orig_south = self.facing_south
            orig_east = self.facing_east

            if quarter_turns == 2:
                self.facing_north = orig_south
                self.facing_west = orig_east
                self.facing_south = orig_north
                self.facing_east = orig_west
            else:
                if clockwise:
                    self.facing_north = orig_west
                    self.facing_west = orig_south
                    self.facing_south = orig_east
                    self.facing_east = orig_north
                else:
                    self.facing_north = orig_east
                    self.facing_west = orig_north
                    self.facing_south = orig_west
                    self.facing_east = orig_south

    def flip(self):

        if self.shutdown:
            return

        current_pos = self.flipper.position

        if current_pos >= -10 and current_pos <= 10:
            final_pos = FLIPPER_DEGREES
        else:
            final_pos = 0

        log.info("flip() to final_pos %d" % final_pos)
        self.flipper.run_to_abs_pos(position_sp=final_pos,
                                    speed_sp=FLIPPER_SPEED)
        self.flipper.wait_for_running()
        self.flipper.wait_for_position(final_pos)
        self.flipper.wait_for_stop()
        self.flipper_at_init = not self.flipper_at_init

        # facing_west and facing_east won't change
        orig_north = self.facing_north
        orig_south = self.facing_south
        orig_up = self.facing_up
        orig_down = self.facing_down

        # We flipped from the init position to where the flipper is blocking the view of the camera
        if final_pos == FLIPPER_DEGREES:
            self.facing_north = orig_up
            self.facing_south = orig_down
            self.facing_up = orig_south
            self.facing_down = orig_north

        # We flipped from where the flipper is blocking the view of the camera to the init position
        else:
            self.facing_north = orig_down
            self.facing_south = orig_up
            self.facing_up = orig_north
            self.facing_down = orig_south

    def elevate(self, rows):
        """
        'rows' is the number of rows of the cube that should be up in the turntable

        http://studs.sariel.pl/
        - a gear rack 4 studs (32 mm) long has 9 grooves, 1 groove is 3.55555556mm
        - the gear for our elevator has 24 teeth so 360 degrees will raise the elevator by 24 grooves
        - so a 360 degree turn raises the elevator 85.333333333mm

        holder top     ----
        flipper top    ----
                          |
                          |
                          |
                          |
                          |
                          |
                          |
        flipper bottom ----
                           ^^^^
                            ||
                            ||
                            ||
                            ||
        """
        assert rows >= 0 and rows <= self.rows_and_cols, "rows was %d, rows must be between 0 and %d" % (rows, self.rows_and_cols)

        if self.shutdown:
            return

        # nothing to do
        if rows == self.rows_in_turntable:
            return

        if rows:
            # TODO - double check this
            mm_per_stud = 8
            flipper_plus_holder_height_studs = 16
            flipper_plus_holder_height_studs_mm =  flipper_plus_holder_height_studs * mm_per_stud
            mm_per_groove = float(32/9) # 4 stud gear rack is 32mm long and has 9 grooves
            # to_top_holder_mm = flipper_plus_holder_height_studs_mm - self.size_mm
            # dwalton
            final_pos_mm = flipper_plus_holder_height_studs_mm - int((3 - rows) * self.square_size_mm)

            degrees_per_groove = 15 # 360/24
            final_pos_grooves = float(final_pos_mm/mm_per_groove)
            final_pos = int(final_pos_grooves * degrees_per_groove)

            log.info("elevate %d rows, flipper_plus_holder_height_studs_mm %s, mm_per_groove %s, final_pos_mm %s, final_pos_grooves %s, final_pos %s" % (rows, flipper_plus_holder_height_studs_mm, mm_per_groove, final_pos_mm, final_pos_grooves, final_pos))
        else:
            final_pos = 0

        log.info("elevate() to final_pos %d" % final_pos)

        if rows < self.rows_in_turntable:
            self.elevator.run_to_abs_pos(position_sp=final_pos,
                                         speed_sp=ELEVATOR_SPEED_DOWN)
        else:
            self.elevator.run_to_abs_pos(position_sp=final_pos,
                                         speed_sp=ELEVATOR_SPEED_UP)

        self.elevator.wait_for_running()
        self.elevator.wait_for_position(final_pos)
        self.elevator.wait_for_stop()
        self.rows_in_turntable = rows


    def scan_face(self, name):
        """
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
        """
        log.info("scan_face() %s" % name)

        if name == 'U':
            init_square_index = 1
            rotate = 270

        elif name == 'L':
            init_square_index = 10
            rotate = 0

        elif name == 'F':
            init_square_index = 19
            rotate = 0

        elif name == 'R':
            init_square_index = 28
            rotate = 0

        elif name == 'B':
            init_square_index = 37
            rotate = 0

        elif name == 'D':
            init_square_index = 46
            rotate = 270

        else:
            raise Exception("Invalid face %s" % name)

        png_filename = '/tmp/rubiks-side-%d.png' % face_number

        if os.path.exists(png_filename):
            os.unlink(png_filename)

        # capture a single png from the webcam
        subprocess.call(['fswebcam',
                         '--device', '/dev/video0',
                         '--no-timestamp',
                         '--no-title',
                         '--no-subtitle',
                         '--no-banner',
                         '--no-info',
                         '-r', '352x240',
                         '--rotate', rotate,
                         '--png', '1',
                         png_filename])

        im = Image.open(png_filename)
        pix = im.load()

        for index in range(9):
            square_index = init_square_index + index
            (x, y) = self.center_pixels[index]
            (red, green, blue) = pix[x, y]
            log.info("square %d, (%s, %s), RGB (%d, %d, %d)" % (square_index, x, y, red, green, blue))

            # colors is a dict where the square number (as an int) will be
            # the key and a RGB tuple the value
            self.colors[square_index] = (red, green, blue)

        # Now that we know the colors, rm the file
        # os.unlink(png_filename)
        log.info("\n")

    def scan(self):
        log.info("scan()")
        self.colors = {}
        self.scan_face('F')

        self.elevate(3)
        self.rotate(clockwise=True, quarter_turns=1)
        self.elevate(0)
        self.scan_face('R')

        self.elevate(3)
        self.rotate(clockwise=True, quarter_turns=1)
        self.elevate(0)
        self.scan_face('B')

        self.elevate(3)
        self.rotate(clockwise=True, quarter_turns=1)
        self.elevate(0)
        self.scan_face('L')

        # expose the 'D' side, then raise the cube so we can get the flipper out
        # of the way, get the flipper out of the way, then lower the cube
        self.flip()
        self.elevate(3)
        self.flip()
        self.elevate(0)
        self.scan_face('D')

        # rotate to scan the 'U' side
        self.elevate(3)
        self.rotate(clockwise=True, quarter_turns=2)
        self.elevate(0)
        self.scan_face('U')

        # To make troubleshooting easier, move the F of the cube so that it
        # is facing the camera like it was when we started the scan
        self.flip()
        self.elevate(3)
        self.rotate(clockwise=False, quarter_turns=1)
        self.flip()
        self.elevate(0)

        if self.shutdown:
            return

        log.info("RGB json:\n%s\n" % json.dumps(self.colors))
        log.info("RGB pformat:\n%s\n" % pformat(self.colors))
        self.rgb_solver = RubiksColorSolver()
        self.rgb_solver.enter_scan_data(self.colors)
        self.cube_kociemba = self.rgb_solver.crunch_colors()
        log.info("Final Colors (kociemba): %s" % ''.join(self.cube_kociemba))

    def move_north_to_top(self):
        if self.flipper_at_init:
            self.elevate(3)
            self.rotate(clockwise=True, quarter_turns=2)

        self.elevate(0)
        self.flip()
        self.elevate(1)

    def move_west_to_top(self):
        self.elevate(3)

        if self.flipper_at_init:
            self.rotate(clockwise=False, quarter_turns=1)
        else:
            self.rotate(clockwise=True, quarter_turns=1)

        self.elevate(0)
        self.flip()
        self.elevate(1)

    def move_south_to_top(self):
        if not self.flipper_at_init:
            self.rotate(clockwise=True, quarter_turns=2)
        self.elevate(0)
        self.flip()
        self.elevate(1)

    def move_east_to_top(self):
        self.elevate(3)

        if self.flipper_at_init:
            self.rotate(clockwise=True, quarter_turns=1)
        else:
            self.rotate(clockwise=False, quarter_turns=1)

        self.elevate(0)
        self.flip()
        self.elevate(1)

    def get_direction(self, target_face):
        """
        target_face is in one of four locations, call them north, south, east
        and west (as viewed by looking down on the cube from the top with the camera to
        the south)

        Return the direction of target_face
        """

        if self.facing_north == target_face:
            return 'north'

        if self.facing_west == target_face:
            return 'west'

        if self.facing_south == target_face:
            return 'south'

        if self.facing_east == target_face:
            return 'east'

        raise Exception("Could not find target_face %s, north %s, west %s, south %s, east %" %
                        (target_face, self.facing_north, self.facing_west, self.facing_south, self.facing_east))

    def resolve(self):

        if self.shutdown:
            return

        output = check_output(['kociemba', ''.join(map(str, self.cube_kociemba))]).decode('ascii')
        actions = output.strip().split()
        '''
        action will be a series of moves such as
        D2 R' D' F2 B D R2 D2 R' F2 D' F2 U' B2 L2 U2 D R2 U

        The first letter is the face name
        2 means two quarter turns (rotate 180)
        ' means rotate the face counter clockwise
        '''

        log.info('Action (kociemba): %s' % ' '.join(actions))
        total_actions = len(actions)

        for (index, action) in enumerate(actions):
            log.info("Move %d/%d: %s" % (index, total_actions, action))

            if self.shutdown:
                break

            if action.endswith("'"):
                clockwise = False
            else:
                clockwise = True

            if '2' in action:
                quarter_turns = 2
            else:
                quarter_turns = 1

            target_face = action[0]
            direction = None

            if self.facing_up == 'U':
                if target_face == 'U':
                    self.elevate(1)
                elif target_face == 'D':
                    self.elevate(2)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'L':
                if target_face == 'L':
                    self.elevate(1)
                elif target_face == 'R':
                    self.elevate(2)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'F':
                if target_face == 'F':
                    self.elevate(1)
                elif target_face == 'B':
                    self.elevate(2)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'R':
                if target_face == 'R':
                    self.elevate(1)
                elif target_face == 'L':
                    self.elevate(2)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'B':
                if target_face == 'B':
                    self.elevate(1)
                elif target_face == 'F':
                    self.elevate(2)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'D':
                if target_face == 'D':
                    self.elevate(1)
                elif target_face == 'U':
                    self.elevate(2)
                else:
                    direction = self.get_direction(target_face)

            else:
                raise Exception("Invalid face %s" % self.facing_up)

            if direction:
                if direction == 'north':
                    self.move_north_to_top()
                elif direction == 'west':
                    self.move_west_to_top()
                elif direction == 'south':
                    self.move_south_to_top()
                elif direction == 'east':
                    self.move_east_to_top()

            self.rotate(clockwise, quarter_turns)
            log.info("\n")

    def test(self):
        """
        Test the three motors
        """
        '''
        input('Press ENTER to flip (to forward)')
        self.flip()

        if self.shutdown:
            return

        input('Press ENTER to flip (to init)')
        self.flip()

        if self.shutdown:
            return

        input('Press ENTER rotate 90 degrees clockwise')
        self.rotate(clockwise=True, quarter_turns=1)

        if self.shutdown:
            return

        input('Press ENTER rotate 90 degrees counter clockwise')
        self.rotate(clockwise=False, quarter_turns=1)

        if self.shutdown:
            return

        input('Press ENTER rotate 180 degrees clockwise')
        self.rotate(clockwise=True, quarter_turns=2)

        if self.shutdown:
            return

        input('Press ENTER rotate 180 degrees counter clockwise')
        self.rotate(clockwise=False, quarter_turns=2)

        if self.shutdown:
            return
        '''
        # dwalton
        input('Press ENTER elevate to 3 rows')
        self.elevate(3)

        if self.shutdown:
            return

        input('Press ENTER elevate to lower')
        self.elevate(0)

        if self.shutdown:
            return

        input('Press ENTER elevate to 2 rows')
        self.elevate(2)

        if self.shutdown:
            return

        input('Press ENTER elevate to 3 rows')
        self.elevate(3)

        if self.shutdown:
            return

        input('Press ENTER elevate to 2 rows')
        self.elevate(2)

        if self.shutdown:
            return

        input('Press ENTER elevate to lower')
        self.elevate(0)

        if self.shutdown:
            return


if __name__ == '__main__':

    # logging.basicConfig(filename='rubiks.log',
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
    log = logging.getLogger(__name__)

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

    cc = CraneCuber()

    try:
        # cc.wait_for_touch_sensor()
        cc.test()
        #cc.scan()
        #cc.resolve()
        cc.shutdown_robot()

    except Exception as e:
        log.exception(e)
        cc.shutdown_robot()
        sys.exit(1)
