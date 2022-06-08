import math
import constants


RAD1 = math.pi / 180
HALFWIDTH = constants.WIDTH >> 1
HALFHEIGHT = constants.HEIGHT >> 1


def isClosedDoor(seg):
    return (seg.backSec.CeilingHeight <= seg.frontSec.FloorHeight or
            seg.backSec.FloorHeight >= seg.frontSec.CeilingHeight)


def isPortal(seg):
    return (seg.frontSec.CeilingHeight != seg.backSec.CeilingHeight or
            seg.frontSec.FloorHeight != seg.backSec.FloorHeight)


dcos = lambda angle: math.cos(angle * RAD1)
dsin = lambda angle: math.sin(angle * RAD1)
dtan = lambda angle: math.tan(angle * RAD1)
dcot = lambda angle: 1 / math.tan(angle * RAD1)

def angleToScreenX(angle):
    x = 0
    # left side of fov
    if angle > 90:
        angle -= 90  # set the angle to with of player angle(0)
        x = HALFWIDTH - round(math.tan(angle * RAD1) * HALFWIDTH)
    # right side
    else:
        angle = 90 - angle
        x = HALFWIDTH + round(math.tan(angle * RAD1) * HALFWIDTH)
    return x
