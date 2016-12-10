#!/usr/bin/env python3

"""
CraneCuber
A Rubiks cube solving robot made from EV3 + 42009
"""

from crane_cuber_core import CraneCuber3x3x3
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

cc = CraneCuber3x3x3()

try:
    while not cc.shutdown:
        cc.scan()
        cc.get_colors()
        cc.resolve_colors()
        cc.resolve_moves()
        cc.wait_for_touch_sensor()
    cc.shutdown_robot()

except Exception as e:
    log.exception(e)
    cc.shutdown_robot()
    sys.exit(1)
