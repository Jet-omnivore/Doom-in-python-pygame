from dataclasses import dataclass
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

SKYFLATNAME = "F_SKY1"

@dataclass
class Visplane:
    height: int
    pic: str  # texture
    lightLevel: int

    minx: int = SCREEN_WIDTH
    maxx: int = -1
    
    def __post_init__(self):
        self.top = []
        self.bottom = []


class VisplaneManager:
    def __init__(self):
        self.visplanes = []

        self.floorclip = [SCREEN_HEIGHT] * SCREEN_WIDTH
        self.ceilingclip = [-1] * SCREEN_WIDTH

    def clear_planes(self):
        for i in range(SCREEN_WIDTH):
            self.floorclip[i] = SCREEN_HEIGHT
            self.ceilingclip[i] = -1

        self.visplanes.clear()

    def find_plane(self, height, pic, lightLevel):
        
        if pic == SKYFLATNAME:
            height = 0
            lightLevel = 0

        for check in self.visplanes:
            if height == check.height and pic == check.pic and lightLevel == check.lightLevel:
               return check

        check = Visplane(height, pic, lightLevel, SCREEN_WIDTH, -1)
        check.top = [0xff] * SCREEN_WIDTH
        check.bottom = [0xff] * SCREEN_WIDTH
        self.visplanes.append(check)

        return check

    def check_plane(self, plane, start, stop):

        intrl = None
        unionl = None
        intrh = None
        unionh = None

        if start < plane.minx:
            intrl = plane.minx
            unionl = start
        else:
            unionl = plane.minx
            intrl = start
        if stop > plane.maxx:
             intrh = plane.maxx
             unionh = stop
        else:
             unionh = plane.maxx
             intrh = stop

        x = 0
        for x in range(intrl, intrh + 1):
            if plane.top[x] != 0xff:
                break

        if x > intrh:
            plane.minx = unionl
            plane.maxx = unionh
            
            return plane

        new_plane = Visplane(plane.height, plane.pic, plane.lightLevel)
        new_plane.minx = start
        new_plane.maxx = stop

        new_plane.top = [0xff] * SCREEN_WIDTH
        self.visplanes.append(new_plane)
        return new_plane
