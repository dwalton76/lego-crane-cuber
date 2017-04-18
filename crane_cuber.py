#!/usr/bin/env python3

"""
CraneCuber
A Rubiks cube solving robot made from EV3 + 42009
"""

from copy import deepcopy
from ev3dev.auto import OUTPUT_A, OUTPUT_B, OUTPUT_C, TouchSensor, LargeMotor, MediumMotor
from rubikscolorresolver import RubiksColorSolverGeneric
from math import pi, sqrt
from pprint import pformat
from time import sleep
from threading import Thread, Event
import argparse
import curses
import datetime
import json
import logging
import math
import os
import shutil
import signal
import subprocess
import sys

log = logging.getLogger(__name__)

# positive moves to init position
# negative moves towards camera
# This should be 90 degrees but some extra is needed to account for play between the gears
FLIPPER_DEGREES = -140
FLIPPER_SPEED = 300

# The gear ratio is 1:2.333
# The follower gear rotates 0.428633 time per each revolution of the driver gear
# We need the follower gear to rotate 90 degrees so 90/0.428633 = 209.96
#
# negative moves counter clockwise (viewed from above)
# positive moves clockwise (viewed from above)
TURNTABLE_TURN_DEGREES = 210
TURNTABLE_SPEED = 1050
TURNTABLE_FREE_SPEED = 800
TURN_FREE_TOUCH_DEGREES = 40
TURN_FREE_SQUARE_TT_DEGREES = -40

# positive moves down
# negative moves up
ELEVATOR_SPEED_UP_FAST = 1050
ELEVATOR_SPEED_UP_SLOW = 1050
ELEVATOR_SPEED_DOWN_FAST = 1050
ELEVATOR_SPEED_DOWN_SLOW = 1050


# References
# ==========
# cube sizes
# http://cubeman.org/measure.txt
#
# README editing
# https://jbt.github.io/markdown-editor/


def round_to_quarter_turn(target_degrees):
    """
    round target_degrees up/down so that it is a multiple of TURNTABLE_TURN_DEGREES
    """
    a = int(target_degrees/TURNTABLE_TURN_DEGREES)

    if target_degrees % TURNTABLE_TURN_DEGREES == 0:
        log.info("round_to_quarter_turn %d is already a multiple of %d" % (target_degrees, TURNTABLE_TURN_DEGREES))
        return target_degrees

    log.info("round_to_quarter_turn %d/%d is %s" % (target_degrees, TURNTABLE_TURN_DEGREES, float(target_degrees/TURNTABLE_TURN_DEGREES)))
    result = int(round(float(target_degrees/TURNTABLE_TURN_DEGREES)) * TURNTABLE_TURN_DEGREES)
    log.info("round_to_quarter_turn result is %s" % result)
    return result


def convert_key_strings_to_int(data):
    result = {}
    for (key, value) in data.items():
        if isinstance(key, str) and key.isdigit():
            result[int(key)] = value
        else:
            result[key] = value
    return result


class DummyMotor(object):

    def __init__(self, address):
        self.address = address
        self.connected = True
        self.position = 0

    def reset(self):
        pass

    def stop(self, stop_action=None):
        pass

    def run_forever(self, speed_sp, stop_action):
        pass

    def run_to_abs_pos(self, speed_sp=None, stop_action=None, position_sp=None, ramp_up_sp=None, ramp_down_sp=None):
        pass

    def wait_until(self, state):
        pass

    def wait_while(self, state, timeout=None):
        pass


class DummySensor(object):

    def is_pressed(self):
        return True


class CraneCuber3x3x3(object):

    def __init__(self, SERVER, emulate, screen, rows_and_cols=3, size_mm=57):
        self.SERVER = SERVER
        self.emulate = emulate
        self.screen = screen
        self.shutdown = False
        self.rows_and_cols = rows_and_cols
        self.size_mm = size_mm
        self.square_size_mm = float(self.size_mm / self.rows_and_cols)

        if self.emulate:
            self.elevator = DummyMotor(OUTPUT_A)
            self.flipper = DummyMotor(OUTPUT_B)
            self.turntable= DummyMotor(OUTPUT_C)
            self.touch_sensor = DummySensor()
        else:
            self.elevator = LargeMotor(OUTPUT_A)
            self.flipper = MediumMotor(OUTPUT_B)
            self.turntable= LargeMotor(OUTPUT_C)
            self.touch_sensor = TouchSensor()

        self.motors = [self.elevator, self.flipper, self.turntable]
        self.rows_in_turntable = 0
        self.facing_up = 'U'
        self.facing_down = 'D'
        self.facing_north = 'B'
        self.facing_west = 'L'
        self.facing_south = 'F'
        self.facing_east = 'R'
        signal.signal(signal.SIGTERM, self.signal_term_handler)
        signal.signal(signal.SIGINT, self.signal_int_handler)
        self.time_elevate = 0
        self.time_flip = 0
        self.time_rotate = 0
        self.flipper_at_init = True
        self.colors = {}

        # These numbers are for a 57mm 3x3x3 cube
        self.TURN_BLOCKED_TOUCH_DEGREES = 112
        self.TURN_BLOCKED_SQUARE_TT_DEGREES = 40
        self.TURN_BLOCKED_SQUARE_CUBE_DEGREES = (-1 * self.TURN_BLOCKED_TOUCH_DEGREES) - self.TURN_BLOCKED_SQUARE_TT_DEGREES
        self.rows_in_turntable_to_count_as_face_turn = 2

    def init_motors(self):

        for x in self.motors:
            if not x.connected:
                log.error("%s is not connected" % x)
                sys.exit(1)
            x.reset()

        # 'brake' stops but doesn't hold the motor in place
        # 'hold' stops and holds the motor in place
        log.info("Initialize elevator %s" % self.elevator)
        self.elevator.run_forever(speed_sp=20, stop_action='hold')
        self.elevator.wait_until('running')
        self.elevator.wait_until('stalled')
        self.elevator.stop()
        self.elevator.reset()
        self.elevator.stop(stop_action='brake')

        log.info("Initialize flipper %s" % self.flipper)
        self.flipper.run_forever(speed_sp=100, stop_action='hold')
        self.flipper.wait_until('running')
        self.flipper.wait_until('stalled')
        self.flipper.stop()
        self.flipper.reset()
        self.flipper.stop(stop_action='hold')
        self.flipper_at_init = True

        log.info("Initialize turntable %s" % self.turntable)
        self.turntable.reset()
        self.turntable.stop(stop_action='hold')

    def shutdown_robot(self):

        if self.shutdown:
            return

        log.info('shutting down')
        self.elevate(0)

        if self.flipper.position > 10:
            self.flip()

        for x in self.motors:
            x.stop(stop_action='brake')

        self.shutdown = True

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

    def _rotate(self, final_pos):

        if self.rows_in_turntable == self.rows_and_cols:
            speed = TURNTABLE_FREE_SPEED
        else:
            speed = TURNTABLE_SPEED

        self.turntable.run_to_abs_pos(position_sp=final_pos,
                                      speed_sp=speed,
                                      stop_action='hold',
                                      ramp_up_sp=100,
                                      ramp_down_sp=200)
        self.turntable.wait_until('running')
        self.turntable.wait_while('running')

        # uncomment this if you want to test with 100% accurate rotate position
        '''
        prev_pos = None

        while self.turntable.position != final_pos:
            log.info("turntable() position is %d, it should be %d" % (self.turntable.position, final_pos))
            self.turntable.run_to_abs_pos(position_sp=final_pos,
                                         speed_sp=200)
            self.turntable.wait_while('running', timeout=100)

            if prev_pos is not None and self.turntable.position == prev_pos:
                break
            prev_pos = self.turntable.position
        '''

    def rotate(self, clockwise, quarter_turns):

        if self.shutdown:
            return

        assert quarter_turns > 0 and quarter_turns <= 2, "quarter_turns is %d, it must be between 0 and 2" % quarter_turns
        current_pos = self.turntable.position
        start = datetime.datetime.now()
        TT_GEAR_SLIP_DEGREES = 2

        # cube will turn freely since none of the rows are being held
        if self.rows_in_turntable == self.rows_and_cols:
            turn_degrees = TURN_FREE_TOUCH_DEGREES + (TURNTABLE_TURN_DEGREES * quarter_turns)
            square_turntable_degrees = TURN_FREE_SQUARE_TT_DEGREES

            if not clockwise:
                turn_degrees *= -1
                square_turntable_degrees *= -1

            turn_pos = current_pos + turn_degrees
            square_turntable_pos = round_to_quarter_turn(turn_pos + square_turntable_degrees)

            self._rotate(turn_pos)
            self._rotate(square_turntable_pos)

            finish = datetime.datetime.now()
            delta_ms = ((finish - start).seconds * 1000) + ((finish - start).microseconds / 1000)
            self.time_rotate += delta_ms

            log.info("rotate_cube() FREE %d quarter turns, clockwise %s), current_pos %d, turn_pos %d, square_turntable_pos %d took %dms" %
                (quarter_turns, clockwise, current_pos, turn_pos, square_turntable_pos, delta_ms))

        else:
            turn_degrees = self.TURN_BLOCKED_TOUCH_DEGREES + (TURNTABLE_TURN_DEGREES * quarter_turns)
            square_cube_degrees = self.TURN_BLOCKED_SQUARE_CUBE_DEGREES
            square_turntable_degrees = self.TURN_BLOCKED_SQUARE_TT_DEGREES

            if not clockwise:
                turn_degrees *= -1
                square_cube_degrees *= -1
                square_turntable_degrees *= -1

            turn_pos = current_pos + turn_degrees
            square_cube_pos = turn_pos + square_cube_degrees
            square_turntable_pos = round_to_quarter_turn(square_cube_pos + square_turntable_degrees)

            self._rotate(turn_pos)
            self._rotate(square_cube_pos)
            self._rotate(square_turntable_pos)

            finish = datetime.datetime.now()
            delta_ms = ((finish - start).seconds * 1000) + ((finish - start).microseconds / 1000)
            self.time_rotate += delta_ms
            log.info("rotate_cube() BLOCKED %d quarter turns, clockwise %s, current_pos %d, turn_pos %d, square_cube_pos %d, square_turntable_pos %d took %dms" %
                (quarter_turns, clockwise, current_pos, turn_pos, square_cube_pos, square_turntable_pos, delta_ms))

        # Only update the facing_XYZ variables if the entire side is turning.  For
        # a 3x3x3 this means the middle square is being turned, this happens if at
        # least two rows are up in the turntable
        if self.rows_in_turntable >= self.rows_in_turntable_to_count_as_face_turn:
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

            # log.info("north %s, west %s, south %s, east %s (original)" % (orig_north, orig_west, orig_south, orig_east))
            # log.info("north %s, west %s, south %s, east %s" % (self.facing_north, self.facing_west, self.facing_south, self.facing_east))

    def flip_settle_cube(self):
        """
        Even though this move looks like it isn't needed, it is.  The reason
        being if you don't tilt the flipper to get the cube to slide back, when
        we go to raise the cube it is too easy for it to jam up because it may
        have slid forward too far.
        """

        if self.shutdown:
            return

        self.flipper.run_to_abs_pos(position_sp=FLIPPER_DEGREES/2,
                                    speed_sp=FLIPPER_SPEED,
                                    ramp_up_sp=0,
                                    ramp_down_sp=100,
                                    stop_action='hold')
        self.flipper.wait_until('running')
        self.flipper.wait_while('running', timeout=1000)

        self.flipper.run_to_abs_pos(position_sp=0,
                                    speed_sp=FLIPPER_SPEED/2,
                                    ramp_up_sp=0,
                                    ramp_down_sp=100,
                                    stop_action='hold')
        self.flipper.wait_until('running')
        self.flipper.wait_while('running', timeout=1000)

    def flip(self):

        if self.shutdown:
            return

        current_pos = self.flipper.position

        if current_pos >= -10 and current_pos <= 10:
            final_pos = FLIPPER_DEGREES
        else:
            final_pos = 0

        # If the elevator is raised then the cube is not in the flipper so we
        # can flip it pretty quickly.  If the cube is in the flipper though we
        # have to flip more slowly, if you flip too fast the momentum can cause
        # the cube to slide a little when the flipper stops.  When the cube
        # slides like this it is no longer lined up with the turntable above so
        # when we raise the cube it jams up.
        if self.rows_in_turntable == 0:
            speed = FLIPPER_SPEED
        else:
            speed = FLIPPER_SPEED * 2

        start = datetime.datetime.now()
        self.flipper.run_to_abs_pos(position_sp=final_pos,
                                    speed_sp=speed,
                                    ramp_up_sp=0,
                                    ramp_down_sp=100,
                                    stop_action='hold')
        self.flipper.wait_until('running')
        self.flipper.wait_while('running', timeout=2000)
        self.flipper_at_init = not self.flipper_at_init
        finish = datetime.datetime.now()
        delta_ms = ((finish - start).seconds * 1000) + ((finish - start).microseconds / 1000)
        self.time_flip += delta_ms
        log.info("flip() to final_pos %s took %dms" % (final_pos, delta_ms))

        if final_pos == 0 and self.flipper.position != final_pos:
            self.flipper.reset()
            self.flipper.stop(stop_action='hold')

        # uncomment this if you want to test with 100% accurate flip position
        '''
        prev_pos = None

        # Make sure we stopped where we should have
        while self.flipper.position != final_pos:
            log.info("flip() position is %d, it should be %d" % (self.flipper.position, final_pos))
            self.flipper.run_to_abs_pos(position_sp=final_pos,
                                        speed_sp=30,
                                        stop_action='hold')
            self.flipper.wait_while('running', timeout=100)

            if prev_pos is not None and self.flipper.position == prev_pos:
                break
            prev_pos = self.flipper.position
        '''

        # facing_west and facing_east won't change
        orig_north = self.facing_north
        orig_south = self.facing_south
        orig_up = self.facing_up
        orig_down = self.facing_down

        # Sometimes we flip when the elevator is raised all the way up, we do
        # this to get the flipper out of the way so we can take a pic of the
        # cube. If that is the case then then do not alter self.facing_xyz.
        if not self.rows_in_turntable:

            # We flipped from the init position to where the flipper is blocking the view of the camera
            if abs(final_pos - FLIPPER_DEGREES) <= 20:
                self.facing_north = orig_up
                self.facing_south = orig_down
                self.facing_up = orig_south
                self.facing_down = orig_north
                # log.info("flipper1 north %s, south %s, up %s, down %s" %
                #          (self.facing_north, self.facing_south, self.facing_up, self.facing_down))

            # We flipped from where the flipper is blocking the view of the camera to the init position
            else:
                self.facing_north = orig_down
                self.facing_south = orig_up
                self.facing_up = orig_north
                self.facing_down = orig_south
                # log.info("flipper2 north %s, south %s, up %s, down %s" %
                #          (self.facing_north, self.facing_south, self.facing_up, self.facing_down))

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
            # 16 studs at 8mm per stud = 128mm
            flipper_plus_holder_height_studs_mm = 130
            cube_rows_height = int((self.rows_and_cols - rows) * self.square_size_mm)
            final_pos_mm = flipper_plus_holder_height_studs_mm - cube_rows_height

            # The table in section 5 shows says that our 16 tooth gear has an outside diameter of 17.4
            # http://www.robertcailliau.eu/Alphabetical/L/Lego/Gears/Dimensions/
            diameter = 17.4
            circ = diameter * pi

            # We divide by 3 because our gear ratio is 3:1
            final_pos = int(((final_pos_mm / circ) * 360)/3) * -1
        else:
            final_pos = 0

        start = datetime.datetime.now()

        # going down
        if rows < self.rows_in_turntable:
            if final_pos:
                self.elevator.run_to_abs_pos(position_sp=final_pos,
                                             speed_sp=ELEVATOR_SPEED_DOWN_SLOW,
                                             ramp_up_sp=0,
                                             ramp_down_sp=100,
                                             stop_action='hold')
            else:
                self.elevator.run_to_abs_pos(position_sp=0,
                                             speed_sp=ELEVATOR_SPEED_DOWN_FAST,
                                             ramp_up_sp=0,
                                             ramp_down_sp=300, # ramp_down so we don't slam into the ground
                                             stop_action='hold')
        # going up
        else:
            if self.rows_in_turntable:
                self.elevator.run_to_abs_pos(position_sp=final_pos,
                                             speed_sp=ELEVATOR_SPEED_UP_SLOW,
                                             ramp_up_sp=0,
                                             ramp_down_sp=100,
                                             stop_action='hold')
            else:
                self.elevator.run_to_abs_pos(position_sp=final_pos,
                                             speed_sp=ELEVATOR_SPEED_UP_FAST,
                                             ramp_up_sp=200, # ramp_up here so we don't slam into the cube at full speed
                                             ramp_down_sp=200, # ramp_down so we stop at the right spot
                                             stop_action='hold')

        self.elevator.wait_until('running')
        self.elevator.wait_while('running')
        finish = datetime.datetime.now()
        delta_ms = ((finish - start).seconds * 1000) + ((finish - start).microseconds / 1000)
        self.time_elevate += delta_ms
        log.info("elevate() from %d to %d took %dms" % (self.rows_in_turntable, rows, delta_ms))
        self.rows_in_turntable = rows

        if final_pos == 0 and self.elevator.position != final_pos:
            self.elevator.reset()
            self.elevator.stop(stop_action='hold')

        # uncomment this if you want to test with 100% accurate elevate position
        '''
        if final_pos:
            prev_pos = None

            while self.elevator.position != final_pos:
                log.info("elevate() position is %d, it should be %d" % (self.elevator.position, final_pos))
                self.elevator.run_to_abs_pos(position_sp=final_pos,
                                             speed_sp=100,
                                             stop_action='hold')
                self.elevator.wait_while('running', timeout=100)

                if prev_pos is not None and self.elevator.position == prev_pos:
                    break
                prev_pos = self.elevator.position
        '''

    def elevate_max(self):
        self.elevate(self.rows_and_cols)

    def scan_face(self, name):

        if self.shutdown:
            return

        log.info("scan_face() %s" % name)
        png_filename = '/tmp/rubiks-side-%s.png' % name

        if os.path.exists(png_filename):
            os.unlink(png_filename)

        if self.emulate:
            shutil.copy('/home/dwalton/lego/rubiks-cube-tracker/test/test-data/3x3x3-random-01/rubiks-side-%s.png' % name, '/tmp/')
        else:
            # capture a single png from the webcam
            cmd = ['fswebcam',
                   '--device', '/dev/video0',
                   '--no-timestamp',
                   '--no-title',
                   '--no-subtitle',
                   '--no-banner',
                   '--no-info',
                   '-r', '352x240',
                   '--png', '1']

            # The L, F, R, and B sides are simple, for the U and D sides the cube in
            # the png is rotated by 90 degrees so tell fswebcam to rotate 270
            if name in ('U', 'D'):
                cmd.append('--rotate')
                cmd.append('270')

            cmd.append(png_filename)
            subprocess.call(cmd)

        if not os.path.exists(png_filename):
            self.shutdown = True
            return

    def scan(self):

        if self.shutdown:
            return

        log.info("scan()")
        self.colors = {}
        self.scan_face('F')

        self.elevate_max()
        self.rotate(clockwise=True, quarter_turns=1)
        self.elevate(0)
        #self.flip_settle_cube()
        self.scan_face('R')

        self.elevate_max()
        self.rotate(clockwise=True, quarter_turns=1)
        self.elevate(0)
        #self.flip_settle_cube()
        self.scan_face('B')

        self.elevate_max()
        self.rotate(clockwise=True, quarter_turns=1)
        self.elevate(0)
        #self.flip_settle_cube()
        self.scan_face('L')

        # expose the 'D' side, then raise the cube so we can get the flipper out
        # of the way, get the flipper out of the way, then lower the cube
        self.flip()
        self.elevate_max()
        self.flip()
        self.elevate(0)
        self.flip_settle_cube()
        self.scan_face('D')

        # rotate to scan the 'U' side
        self.elevate_max()
        self.rotate(clockwise=True, quarter_turns=2)
        self.elevate(0)
        #self.flip_settle_cube()
        self.scan_face('U')

        # To make troubleshooting easier, move the F of the cube so that it
        # is facing the camera like it was when we started the scan
        self.flip()
        self.elevate_max()
        self.rotate(clockwise=False, quarter_turns=1)
        self.flip()
        self.elevate(0)
        #self.flip_settle_cube()

    def get_colors(self):

        if self.shutdown:
            return

        if self.SERVER:
            cmd = 'scp /tmp/rubiks-side-*.png robot@%s:/tmp/' % self.SERVER
            log.info(cmd)
            subprocess.call(cmd, shell=True)
            cmd = 'ssh robot@%s rubiks-cube-tracker.py --directory /tmp/' % self.SERVER
        else:
            # There isn't opencv support in python3 yet so this has to remain a subprocess call for now
            cmd = 'rubiks-cube-tracker.py --directory /tmp/'

        try:
            log.info(cmd)
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode('ascii').strip()
        except Exception as e:
            log.warning("rubiks-cube-tracker.py failed")
            log.exception(e)
            self.shutdown_robot()
            return

        self.colors = json.loads(output)

    def resolve_colors(self):

        if self.shutdown:
            return

        log.info("RGB json:\n%s\n" % json.dumps(self.colors, sort_keys=True))
        # log.info("RGB pformat:\n%s\n" % pformat(self.colors))

        if self.SERVER:
            cmd = ['ssh',
                   'robot@%s' % self.SERVER,
                   'rubiks-color-resolver.py',
                   '--json',
                   "'%s'" % json.dumps(self.colors)]

            try:
                log.info(' '.join(cmd))
                self.resolved_colors = json.loads(subprocess.check_output(cmd).decode('ascii').strip())
            except Exception as e:
                log.warning("rubiks-color-resolver.py failed")
                log.exception(e)
                self.shutdown_robot()
                return

        else:
            square_count = len(self.colors.keys())
            square_count_per_side = int(square_count/6)
            width = int(sqrt(square_count_per_side))
            cube = RubiksColorSolverGeneric(width)
            cube.enter_scan_data(self.colors)
            cube.crunch_colors()
            self.resolved_colors = cube.cube_for_json()

        self.resolved_colors['squares'] = convert_key_strings_to_int(self.resolved_colors['squares'])
        self.cube_for_resolver = self.resolved_colors['kociemba']

        log.info("Final Colors: %s" % self.cube_for_resolver)
        log.info("north %s, west %s, south %s, east %s, up %s, down %s" %
                 (self.facing_north, self.facing_west, self.facing_south, self.facing_east, self.facing_up, self.facing_down))

    def move_north_to_top(self, rows=1):
        log.info("move_north_to_top() - flipper_at_init %s" % self.flipper_at_init)
        if self.flipper_at_init:
            self.elevate_max()
            self.rotate(clockwise=True, quarter_turns=2)

        self.elevate(0)
        self.flip()
        self.elevate(rows)

    def move_west_to_top(self, rows=1):
        log.info("move_west_to_top() - flipper_at_init %s" % self.flipper_at_init)
        self.elevate_max()

        if self.flipper_at_init:
            self.rotate(clockwise=False, quarter_turns=1)
        else:
            self.rotate(clockwise=True, quarter_turns=1)

        self.elevate(0)
        self.flip()
        self.elevate(rows)

    def move_south_to_top(self, rows=1):
        log.info("move_south_to_top() - flipper_at_init %s" % self.flipper_at_init)

        if not self.flipper_at_init:
            self.elevate_max()
            self.rotate(clockwise=True, quarter_turns=2)

        self.elevate(0)
        self.flip()
        self.elevate(rows)

    def move_east_to_top(self, rows=1):
        log.info("move_east_to_top() - flipper_at_init %s" % self.flipper_at_init)
        self.elevate_max()

        if self.flipper_at_init:
            self.rotate(clockwise=True, quarter_turns=1)
        else:
            self.rotate(clockwise=False, quarter_turns=1)

        self.elevate(0)
        self.flip()
        self.elevate(rows)

    def move_down_to_top(self, rows=1):
        log.info("move_down_to_top() - flipper_at_init %s" % self.flipper_at_init)
        self.elevate(0)
        self.flip()
        self.elevate_max()
        self.flip() # empty flip
        self.elevate(0)
        self.flip()
        self.elevate(rows)

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

        if self.facing_down == target_face:
            return 'down'

        raise Exception("Could not find target_face %s, north %s, west %s, south %s, east %s, up %s, down %s" %
                        (target_face,
                         self.facing_north, self.facing_west, self.facing_south, self.facing_east,
                         self.facing_up, self.facing_down))

    def run_actions(self, actions):
        """
        action will be a series of moves such as
        D'  B2  Rw' Uw  R2  Fw  D   Rw2 B   R2  Uw  D2  Rw2 U2  Fw2 U2  L   F
        R   Uw2 B'  R   Uw2 L'  D   B   L2  U   B2  D   B2  F'  U'  R   B2  R2
        F2  R'  B2  F2  D2  L'  U2  z'

        https://www.randelshofer.ch/cubetwister/doc/notations/wca_4x4.html
        - the first letter is the face name
        - the w means turn both layers of that face
        - 2 means two quarter turns (rotate 180)
        - ' means rotate counter clockwise
        - ignore the x, y, z at the end, this is just rotating the entire cube to get the F side back to the front
        """

        log.info('Moves: %s' % ' '.join(actions))
        total_actions = len(actions)
        start = datetime.datetime.now()
        moves = 0
        self.time_elevate = 0
        self.time_flip = 0
        self.time_rotate = 0

        # If use_shortcut is True and we do back-to-back set of moves on opposite
        # faces (like "F B") do not bother flipping the cube around to make B face
        # up, just rotate with F facing up.
        #
        # 2x2x2 - does not apply since solver only uses U F and R
        # 3x3x3 - works just fine
        # 4x4x4 - does not work...cube doesn't solve...need to investigate
        # 5x5x5 - works just fine
        if self.rows_and_cols in (3, 5):
            use_shortcut = True
        else:
            use_shortcut = False

        for (index, action) in enumerate(actions):
            desc = "Move %d/%d: %s" % (index, total_actions, action)
            log.info(desc)
            #log.info("Up %s, Down %s, North %s, West %s, South %s, East %s" %
            #        (self.facing_up, self.facing_down, self.facing_north, self.facing_west, self.facing_south, self.facing_east))

            if self.shutdown:
                break

            if action.startswith('x') or action.startswith('y') or action.startswith('z'):
                continue

            if action.endswith("'") or action.endswith("’"):
                action = action[0:-1]
                clockwise = False
            else:
                clockwise = True

            if action.endswith('2'):
                quarter_turns = 2
                action = action[0:-1]
            elif action.endswith('1'):
                quarter_turns = 1
                action = action[0:-1]
            else:
                quarter_turns = 1

            target_face = action[0]
            direction = None

            # The 4x4x4 java solver is the only one that uses this notation
            if 'w' in action:
                rows = 2
            else:
                rows = 1

            if self.facing_up == 'U':
                if target_face == 'U':
                    self.elevate(rows)
                elif use_shortcut and target_face == 'D':
                    rows = self.rows_and_cols - rows
                    self.elevate(rows)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'L':
                if target_face == 'L':
                    self.elevate(rows)
                elif use_shortcut and target_face == 'R':
                    rows = self.rows_and_cols - rows
                    self.elevate(rows)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'F':
                if target_face == 'F':
                    self.elevate(rows)
                elif use_shortcut and target_face == 'B':
                    rows = self.rows_and_cols - rows
                    self.elevate(rows)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'R':
                if target_face == 'R':
                    self.elevate(rows)
                elif use_shortcut and target_face == 'L':
                    rows = self.rows_and_cols - rows
                    self.elevate(rows)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'B':
                if target_face == 'B':
                    self.elevate(rows)
                elif use_shortcut and target_face == 'F':
                    rows = self.rows_and_cols - rows
                    self.elevate(rows)
                else:
                    direction = self.get_direction(target_face)

            elif self.facing_up == 'D':
                if target_face == 'D':
                    self.elevate(rows)
                elif use_shortcut and target_face == 'U':
                    rows = self.rows_and_cols - rows
                    self.elevate(rows)
                else:
                    direction = self.get_direction(target_face)

            else:
                raise Exception("Invalid face %s" % self.facing_up)

            if direction:
                if direction == 'north':
                    self.move_north_to_top(rows)
                elif direction == 'west':
                    self.move_west_to_top(rows)
                elif direction == 'south':
                    self.move_south_to_top(rows)
                elif direction == 'east':
                    self.move_east_to_top(rows)
                elif direction == 'down':
                    self.move_down_to_top(rows)
                else:
                    raise Exception("Unsupported direction %s" % direction)

            self.rotate(clockwise, quarter_turns)
            log.info("\n\n\n\n")
            moves += 1

        finish = datetime.datetime.now()
        delta_ms = ((finish - start).seconds * 1000) + ((finish - start).microseconds / 1000)
        log.info("SOLVED!! %ds in elevate, %ds in flip, %ds in rotate, %ds in run_actions, %d moves, avg %dms per move" %
            (int(self.time_elevate/1000), int(self.time_flip/1000), int(self.time_rotate/1000),
             int(delta_ms/1000), moves, int(delta_ms/moves)))

    def compress_actions(self, actions):
        actions = actions.replace("Uw Uw Uw ", "Uw' ")
        actions = actions.replace("Uw Uw ", "Uw2 ")
        actions = actions.replace("U U U ", "U' ")
        actions = actions.replace("U U ", "U2 ")

        actions = actions.replace("Lw Lw Lw ", "Lw' ")
        actions = actions.replace("Lw Lw ", "Lw2 ")
        actions = actions.replace("L L L ", "L' ")
        actions = actions.replace("L L ", "L2 ")

        actions = actions.replace("Fw Fw Fw ", "Fw' ")
        actions = actions.replace("Fw Fw ", "Fw2 ")
        actions = actions.replace("F F F ", "F' ")
        actions = actions.replace("F F ", "F2 ")

        actions = actions.replace("Rw Rw Rw ", "Rw' ")
        actions = actions.replace("Rw Rw ", "Rw2 ")
        actions = actions.replace("R R R ", "R' ")
        actions = actions.replace("R R ", "R2 ")

        actions = actions.replace("Bw Bw Bw ", "Bw' ")
        actions = actions.replace("Bw Bw ", "Bw2 ")
        actions = actions.replace("B B B ", "B' ")
        actions = actions.replace("B B ", "B2 ")

        actions = actions.replace("Dw Dw Dw ", "Dw' ")
        actions = actions.replace("Dw Dw ", "Dw2 ")
        actions = actions.replace("D D D ", "D' ")
        actions = actions.replace("D D ", "D2 ")
        return actions

    def resolve_actions(self):

        if self.shutdown:
            return

        if self.SERVER:
            cmd = 'ssh robot@%s "kociemba %s"' % (self.SERVER, self.cube_for_resolver)
        else:
            cmd = 'kociemba %s' % self.cube_for_resolver

        log.info(cmd)
        output = subprocess.check_output(cmd, shell=True).decode('ascii').strip()
        actions = output.split()
        self.run_actions(actions)

        self.elevate(0)

        if not self.flipper_at_init:
            self.flip()

    def test_foo(self):
        #foo = ("U", "Uw", "Dw", "D")
        foo = ("U'", "D'")
        self.run_actions(foo)

    def test_basics(self):
        """
        Test the three motors
        """

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

        input('Press ENTER elevate to 1 rows')
        self.elevate(1)

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

        input('Press ENTER elevate to max rows')
        self.elevate_max()

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

        input('Press ENTER to rotate 1 row clockwise')
        self.elevate(1)
        self.rotate(clockwise=True, quarter_turns=1)

        if self.shutdown:
            return

        input('Press ENTER to rotate 1 row counter clockwise')
        self.elevate(1)
        self.rotate(clockwise=False, quarter_turns=1)

        if self.shutdown:
            return

        input('Press ENTER to rotate 2 row clockwise')
        self.elevate(2)
        self.rotate(clockwise=True, quarter_turns=1)

        if self.shutdown:
            return

        input('Press ENTER to rotate 2 row counter clockwise')
        self.elevate(2)
        self.rotate(clockwise=False, quarter_turns=1)

        if self.shutdown:
            return

        self.elevate(0)

    def test_patterns(self):
        """
        https://ruwix.com/the-rubiks-cube/rubiks-cube-patterns-algorithms/
        """
        # tetris = ("L", "R", "F", "B", "U’", "D’", "L’", "R’")
        checkerboard = ("F", "B2", "R’", "D2", "B", "R", "U", "D’", "R", "L’", "D’", "F’", "R2", "D", "F2", "B’")
        self.run_actions(checkerboard)


class CraneCuber2x2x2(CraneCuber3x3x3):

    def __init__(self, SERVER, emulate, screen, rows_and_cols=2, size_mm=40):
        CraneCuber3x3x3.__init__(self, SERVER, emulate, screen, rows_and_cols, size_mm)

        # These are for a 40mm 2x2x2 cube
        self.TURN_BLOCKED_TOUCH_DEGREES = 77
        self.TURN_BLOCKED_SQUARE_TT_DEGREES = 40
        self.TURN_BLOCKED_SQUARE_CUBE_DEGREES = -117
        self.rows_in_turntable_to_count_as_face_turn = 2

    def resolve_actions(self):

        if self.shutdown:
            return

        if self.SERVER:
            cmd = 'ssh robot@%s rubiks_2x2x2_solver.py "%s"' % (self.SERVER, ''.join(self.cube_for_resolver))
        else:
            cmd = 'rubiks_2x2x2_solver.py "%s"' % ''.join(self.cube_for_resolver)

        log.info(cmd)
        output = subprocess.check_output(cmd, shell=True).decode('ascii').strip()

        if output != 'Cube is already solved':
            actions = output.strip().split()
            self.run_actions(actions)

        self.elevate(0)

        if not self.flipper_at_init:
            self.flip()


class CraneCuber4x4x4(CraneCuber3x3x3):

    def __init__(self, SERVER, emulate, screen, rows_and_cols=4, size_mm=62):
        CraneCuber3x3x3.__init__(self, SERVER, emulate, screen, rows_and_cols, size_mm)

        # These are for a 62mm 4x4x4 cube
        # 60 is perfect for clockwise
        self.TURN_BLOCKED_TOUCH_DEGREES = 65
        self.TURN_BLOCKED_SQUARE_TT_DEGREES = 20
        self.TURN_BLOCKED_SQUARE_CUBE_DEGREES = (-1 * self.TURN_BLOCKED_TOUCH_DEGREES) - self.TURN_BLOCKED_SQUARE_TT_DEGREES
        self.rows_in_turntable_to_count_as_face_turn = 4

    def resolve_actions(self):

        if self.shutdown:
            return

        if self.SERVER:
            cmd = "ssh robot@%s 'cd /home/robot/rubiks-cube-solvers/4x4x4/TPR-4x4x4-Solver && java -cp .:threephase.jar:twophase.jar solver %s'" % (self.SERVER, ''.join(self.cube_for_resolver))
        else:
            cmd = "cd /home/robot/rubiks-cube-solvers/4x4x4/TPR-4x4x4-Solver && java -cp .:threephase.jar:twophase.jar solver %s" % ''.join(self.cube_for_resolver)

        log.info(cmd)
        output = subprocess.check_output(cmd, shell=True).decode('ascii').splitlines()[-1].strip()

        actions = output.split()
        self.run_actions(actions)

        self.elevate(0)

        if not self.flipper_at_init:
            self.flip()


class CraneCuber5x5x5(CraneCuber3x3x3):

    def __init__(self, SERVER, emulate, screen, rows_and_cols=5, size_mm=63):
        CraneCuber3x3x3.__init__(self, SERVER, emulate, screen, rows_and_cols, size_mm)

        # These are for a 63mm 5x5x5 cube
        self.TURN_BLOCKED_TOUCH_DEGREES = 52
        self.TURN_BLOCKED_SQUARE_TT_DEGREES = 15
        self.TURN_BLOCKED_SQUARE_CUBE_DEGREES = (-1 * self.TURN_BLOCKED_TOUCH_DEGREES) - self.TURN_BLOCKED_SQUARE_TT_DEGREES
        self.rows_in_turntable_to_count_as_face_turn = 3

    def resolve_actions(self):

        if self.shutdown:
            return

        # The self.cube_for_resolver order is U L F R B D but the 5x5x5 solver needs U R L B F D order
        cube_string = (self.cube_for_resolver[0:25] +    # U
                       self.cube_for_resolver[75:100] +  # R
                       self.cube_for_resolver[25:50] +   # L
                       self.cube_for_resolver[100:125] + # B
                       self.cube_for_resolver[50:75] +   # F
                       self.cube_for_resolver[125:150])  # D
        cube_string = ''.join(cube_string)
        log.info("cube string for 5x5x5 reducer %s" % cube_string)

        if self.SERVER:
            cmd = "ssh robot@%s 'cd /home/robot/rubiks-cube-solvers/5x5x5/ && java -cp bin -Xmx4g justsomerandompackagename.reducer %s'" % (self.SERVER, cube_string)
        else:
            cmd = "cd /home/robot/rubiks-cube-solvers/5x5x5/ && java -cp bin -Xmx4g justsomerandompackagename.reducer %s" % cube_string

        log.info(cmd)
        output = subprocess.check_output(cmd, shell=True).decode('ascii').splitlines()
        '''
        The 5x5x5 reducer will produce the following in the very last lines of output:

        All Moves (106 total) - Rw Uw Rw Bw Rw Rw F F Uw Uw Bw Rw Lw Lw Dw Dw B B B Uw Uw Uw Dw L Rw Rw Lw Lw Dw U U U F Rw Rw Uw Uw F F F Dw Dw F F F Uw Uw B B Uw Uw Bw Bw Rw Rw Uw Uw L D D D L D D D F F U Lw Lw D L U U U Bw Bw Lw Lw U Bw Bw U U U F F Fw Fw U U U Rw Rw D Bw Bw U L L F F Bw Bw Rw Rw
        U - LUUURDUUUUDUUUUDUUUUDDDDB
        D - UDDDUBDDDUBDDDUBDDDUBFFFU
        R - LLLLBLRRRRLRRRRLRRRRFFFFL
        L - FLLLRRLLLBRLLLBRLLLBRRRRF
        F - FBBBDUFFFBUFFFBUFFFBLFFFR
        B - URRRDFBBBDFBBBDFBBBDBLLLD
        '''
        found_all_moves = False
        tmp = {}
        for line in output:
            line = line.strip()
            if line.startswith("All Moves"):
                found_all_moves = True
                actions = line.split(' - ')[1].strip()
                log.info("5x5x5 -> 3x3x3 reduction moves %s" % actions)
            elif found_all_moves:
                if '-' in line:
                    log.info("5x5x5 -> 3x3x3 state: %s" % line)
                    (side_name, squares) = line.split('-')
                    side_name = side_name.strip()
                    squares = squares.strip()
                    '''
                    Example:
                    U - LUUURDUUUUDUUUUDUUUUDDDDB

                    The cube has been reduced to a 3x3x3 so we want the
                    corners, the middle of each edge and the center square

                    LUUUR
                    DUUUU
                    DUUUU
                    DUUUU
                    DDDDB
                    '''
                    tmp[side_name] = squares[0] + squares[2] + squares[4] + squares[10] + squares[12] + squares[14] + squares[20] + squares[22] + squares[24]

        # kociemba uses order U R F D L B
        cube_string_for_3x3x3 = tmp['U'] + tmp['R'] + tmp['F'] + tmp['D'] + tmp['L'] + tmp['B']
        log.info("tmp U %s" % tmp['U'])
        log.info("tmp R %s" % tmp['R'])
        log.info("tmp F %s" % tmp['F'])
        log.info("tmp D %s" % tmp['D'])
        log.info("tmp L %s" % tmp['L'])
        log.info("tmp B %s" % tmp['B'])
        log.info("cube_string_for_3x3x3 %s" % cube_string_for_3x3x3)

        # The only reason we cd to the directory here is so the cache dir is in the same place each time
        if self.SERVER:
            cmd = 'ssh robot@%s "cd /home/robot/rubiks-cube-solvers/3x3x3/ && kociemba %s"' % (self.SERVER, cube_string_for_3x3x3)
        else:
            cmd = 'cd /home/robot/rubiks-cube-solvers/3x3x3/ && kociemba %s' % cube_string_for_3x3x3

        log.info(cmd)
        output = subprocess.check_output(cmd, shell=True).decode('ascii').strip()

        kociemba_actions = output.strip()
        actions += ' ' + kociemba_actions
        actions = self.compress_actions(actions).split()
        self.run_actions(actions)
        self.elevate(0)

        if not self.flipper_at_init:
            self.flip()


class CraneCuber6x6x6(CraneCuber3x3x3):

    def __init__(self, SERVER, emulate, sceen, rows_and_cols=6, size_mm=67):
        CraneCuber3x3x3.__init__(self, SERVER, emulate, screen, rows_and_cols, size_mm)

        # These are for a 67mm 6x6x6 cube
        self.TURN_BLOCKED_TOUCH_DEGREES = 29
        self.TURN_BLOCKED_SQUARE_TT_DEGREES = 13
        self.TURN_BLOCKED_SQUARE_CUBE_DEGREES = (-1 * self.TURN_BLOCKED_TOUCH_DEGREES) - self.TURN_BLOCKED_SQUARE_TT_DEGREES
        self.rows_in_turntable_to_count_as_face_turn = 6

    def resolve_actions(self):
        raise Exception("No solver available for 6x6x6")


if __name__ == '__main__':

    # logging.basicConfig(level=logging.INFO,
    logging.basicConfig(filename='/tmp/cranecuber.log',
                        level=logging.INFO,
                        format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
    log = logging.getLogger(__name__)

    # Color the errors and warnings in red
    logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

    parser = argparse.ArgumentParser()
    parser.add_argument('--emulate', action='store_true', default=False, help='Run in emulator mode')
    args = parser.parse_args()

    server_conf = "server.conf"
    SERVER = None

    if os.path.exists(server_conf):

        with open(server_conf, 'r') as fh:
            for line in fh.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    SERVER = line
                    break

        if SERVER is None:
            print("ERROR: The server.conf does not contain a server")
            sys.exit(1)

    if SERVER:
        log.info("Verify we can ssh to %s without a password" % SERVER)
        cmd = 'ssh robot@%s ls /tmp' % SERVER
        try:
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode('ascii').strip()
        except Exception as e:
            print("ERROR: '%s' failed due to %s, cannot ssh to server" % (cmd, e))
            sys.exit(1)

    # Use this to test your TURN_BLOCKED_TOUCH_DEGREES
    '''
    #cc = CraneCuber4x4x4(SERVER)
    cc = CraneCuber3x3x3(SERVER, args.emulate, screen)
    cc.init_motors()
    cc.test_foo()
    cc.shutdown_robot()
    sys.exit(0)
    '''
    cc = None

    # curses
    begin_x = 0
    begin_y = 0
    height = 5
    width = 40
    screen = curses.initscr()
    win = curses.newwin(height, width, begin_y, begin_x)

    try:
        while True:
            # Size doesn't matter for scanning so use a CraneCuber3x3x3 object
            cc = CraneCuber3x3x3(SERVER, args.emulate, screen)
            cc.init_motors()
            cc.wait_for_touch_sensor()
            cc.scan()
            cc.get_colors()

            if cc.shutdown:
                break

            # We have scanned all sides and know how many squares there are, use
            # this to create an object of the appropriate class
            #
            # cc.colors is a dict where the square_index is the key and the RGB is the value
            colors = deepcopy(cc.colors)
            squares_per_side = len(colors.keys()) / 6
            size = int(math.sqrt(squares_per_side))

            if size == 2:
                cc = CraneCuber2x2x2(SERVER, args.emulate, screen)
            elif size == 3:
                cc = CraneCuber3x3x3(SERVER, args.emulate, screen)
            elif size == 4:
                cc = CraneCuber4x4x4(SERVER, args.emulate, screen)
            elif size == 5:
                cc = CraneCuber5x5x5(SERVER, args.emulate, screen)
            elif size == 6:
                cc = CraneCuber6x6x6(SERVER, args.emulate, screen)
            else:
                raise Exception("%dx%dx%d cubes are not yet supported" % (size, size, size))

            cc.colors = colors
            cc.resolve_colors()
            cc.resolve_actions()

            if cc.shutdown or args.emulate:
                break

        cc.shutdown_robot()

    except Exception as e:
        log.exception(e)

        if cc:
            cc.shutdown_robot()

        sys.exit(1)

