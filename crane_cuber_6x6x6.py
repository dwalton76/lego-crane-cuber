#!/usr/bin/env python3

"""
CraneCuber
A Rubiks cube solving robot made from EV3 + 42009
"""

from ev3dev.ev3 import Leds
from crane_cuber_core import CraneCuber6x6x6
import logging
import sys

log = logging.getLogger(__name__)

# logging.basicConfig(filename='rubiks.log',
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)12s %(levelname)8s: %(message)s')
log = logging.getLogger(__name__)

# Color the errors and warnings in red
logging.addLevelName(logging.ERROR, "\033[91m   %s\033[0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.WARNING, "\033[91m %s\033[0m" % logging.getLevelName(logging.WARNING))

cc = CraneCuber6x6x6()

try:
    while not cc.shutdown:
        cc.scan()
        cc.get_colors()
        cc.resolve_colors()
        cc.resolve_moves()
        cc.wait_for_touch_sensor()

    cc.shutdown_robot()
    Leds.set_color(Leds.LEFT, Leds.GREEN)
    Leds.set_color(Leds.RIGHT, Leds.GREEN)

except Exception as e:
    Leds.set_color(Leds.LEFT, Leds.RED)
    Leds.set_color(Leds.RIGHT, Leds.RED)
    log.exception(e)
    cc.shutdown_robot()
    Leds.set_color(Leds.LEFT, Leds.GREEN)
    Leds.set_color(Leds.RIGHT, Leds.GREEN)
    sys.exit(1)
