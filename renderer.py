import pygame
import random
import time
import math

from angle import Angle
from angle import RAD1
from classDef import classicDoomScreenXtoView
from data_types import SegmentRenderData
from numba import njit

HALFWIDTH = 320 >> 1
HALFHEIGHT = 200 >> 1

@njit(fastmath=True)
def angleToScreen(angle):
    x = 0
    #left side of fov
    if angle > 90:
        #set the angle to with of player angle(0)
        angle -= 90
        x = HALFWIDTH - round(math.tan(angle * RAD1) * HALFWIDTH)
    #right side
    else:
        angle = 90 - angle
        x = HALFWIDTH + round(math.tan(angle * RAD1) * HALFWIDTH)
    return x

def clamp(n, min_val, max_val):
    return max(min(n, max_val), min_val)

class Renderer:
    def __init__(self, engine):
        self.engine = engine
        self.player = self.engine.player
        self.game_map = self.engine.game_map
        self.remap_x, self.remap_y = self.engine.remap_x, self.engine.remap_y
        self.wall_colors = {}
        self.font = pygame.font.SysFont('arial', 10)

        screen_angle = (self.player.fov >> 1)
        fstep = self.player.fov / (self.engine.width + 1)
        useClassicDoomScreenToAngle = True

        self.screenXtoAngle = {}
        if useClassicDoomScreenToAngle:
            self.screenXtoAngle = {k: Angle(val) for k, val in enumerate(classicDoomScreenXtoView)}
        else:
            for i in range(self.engine.width + 1):
                self.screenXtoAngle[i] = screen_angle
                screen_angle -= fstep

        self.half_width = self.engine.width >> 1
        self.halfHeight = self.engine.height >> 1
        self.half_fov = (self.player.fov >> 1)
        self.p_dist_to_screen = self.half_width / self.half_fov.tan

        self.max_scale = 64
        self.min_scale = 0.00390625
        self.testSurf = pygame.Surface((1, 1))
        self.testSurf.convert()
        self.testSurf.fill((255, 0, 0))
        self.floorClipHeight = []
        self.ceilingClipHeight = []

        self.generateTextureSurf()

    def angleToScreen(self, angle):
        return angleToScreen(angle.angle)

    def init_frame(self):
        self.wall_ranges = [[-999999999, -1], [self.engine.width, 999999999]]
        self.floorClipHeight = [self.engine.height for i in range(self.engine.width)]
        self.ceilingClipHeight = [-1 for i in range(self.engine.width)]

    def generateTextureSurf(self):
        self.textures = {}
        for seg in self.game_map.segs:
            c = self.get_wall_color(seg.linedef.rightSideDef.middleTexture)
            if seg.linedef.rightSideDef.middleTexture not in self.textures:
                surf = pygame.Surface((1, 1))
                surf.convert()
                surf.fill(c)
                self.textures[seg.linedef.rightSideDef.middleTexture] = surf.copy()

    def clipSolidWalls(self, seg, x1, x2, angle1, angle2):
        index = 0
        length = len(self.wall_ranges)
        if length < 2:
            return

        while index < length and self.wall_ranges[index][1] < x1 - 1:
            index += 1
        found_clip_wall = self.wall_ranges[index]

        if x1 < found_clip_wall[0]:
            if x2 < found_clip_wall[0] - 1:
                self.storeWallRange(seg, x1, x2, angle1, angle2)
                self.wall_ranges.insert(index, [x1, x2])
                return
            self.storeWallRange(seg, x1, found_clip_wall[0] - 1, angle1, angle2)
            found_clip_wall[0] = x1

        if x2 <= found_clip_wall[1]:
            return

        next_wall_index = index
        next_wall = found_clip_wall

        while x2 >= self.wall_ranges[next_wall_index + 1][0] - 1:
            self.storeWallRange(seg, next_wall[1] + 1, self.wall_ranges[next_wall_index + 1][0] - 1, angle1, angle2)
            next_wall_index += 1
            next_wall = self.wall_ranges[next_wall_index]

            if x2 <= next_wall[1]:
                found_clip_wall[1] = next_wall[1]
                if next_wall_index != index:
                    index += 1
                    found_clip_wall = self.wall_ranges[index]
                    next_wall_index += 1
                    del self.wall_ranges[index:next_wall_index]
                return

        self.storeWallRange(seg, next_wall[1] + 1, x2, angle1, angle2)
        found_clip_wall[1] = x2

        if next_wall_index != index:
            index += 1
            next_wall_index += 1
            del self.wall_ranges[index:next_wall_index]

    def clipPassWalls(self, seg, x1, x2, angle1, angle2):
        index = 0
        length = len(self.wall_ranges)

        while index < length and self.wall_ranges[index][1] < x1 - 1:
            index += 1
        found_clip_wall = self.wall_ranges[index]

        if x1 < found_clip_wall[0]:
            if x2 < found_clip_wall[0] - 1:
                self.storeWallRange(seg, x1, x2, angle1, angle2)
                return
            self.storeWallRange(seg, x1, found_clip_wall[0] - 1, angle1, angle2)

        if x2 <= found_clip_wall[1]:
            return

        next_wall_index = index
        next_wall = found_clip_wall

        while x2 >= self.wall_ranges[next_wall_index + 1][0] - 1:
            self.storeWallRange(seg, next_wall[1] + 1, self.wall_ranges[next_wall_index + 1][0] - 1, angle1, angle2)
            next_wall_index += 1
            next_wall = self.wall_ranges[next_wall_index]

            if x2 <= next_wall[1]:
                return

        self.storeWallRange(seg, next_wall[1] + 1, x2, angle1, angle2)

    def storeWallRange(self, seg, x1, x2, angle1, angle2):
        surf = self.textures[seg.linedef.rightSideDef.middleTexture]
        if x1 == x2:
            return
        self.calcWallHeight(seg, x1, x2, angle1, angle2, surf=surf)

    def drawWallInFov(self, seg, v1Angle, v2Angle, angle1, angle2):
        x1 = self.angleToScreen(angle1)
        x2 = self.angleToScreen(angle2)

        #only solid walls
        if not seg.leftSec:
            self.clipSolidWalls(seg, x1, x2, v1Angle, v2Angle)
            return

        #only closed doors
        if seg.leftSec.CeilingHeight <= seg.rightSec.FloorHeight or seg.leftSec.FloorHeight >= seg.rightSec.CeilingHeight:
           self.clipSolidWalls(seg, x1, x2, v1Angle, v2Angle)
           return

        #see through walls
        if seg.rightSec.CeilingHeight != seg.leftSec.CeilingHeight or seg.rightSec.FloorHeight != seg.leftSec.FloorHeight:
            self.clipPassWalls(seg, x1, x2, v1Angle, v2Angle)
            return

    def render(self, render_auto_map=False):
        if render_auto_map:
            self.render_auto_map()
        else:
            self.game_map.render_bsp_nodes()

    def render_auto_map(self):
        for line in self.game_map.linedef:
            svertex, evertex = line.startVertex, line.endVertex
            pygame.draw.line(self.engine.display, (255, 255, 255),
                            (self.remap_x(svertex.x), self.remap_y(svertex.y)),
                            (self.remap_x(evertex.x), self.remap_y(evertex.y)))

    def get_wall_color(self, texture):
        if texture not in self.wall_colors:
            self.wall_colors[texture] = [random.randint(0, 255) for i in range(3)]
        return self.wall_colors[texture]

    def calcWallHeight(self, seg, x1, x2, v1angle, v2angle, *, surf=None, color=(255, 0, 0)):
        angle90 = Angle(90)
        segToNormalAngle = Angle((seg.angle) + angle90.angle)
        normalToV1Angle = Angle(segToNormalAngle.angle - v1angle.angle)
        segToPlayerAnge = angle90 - normalToV1Angle

        renderData = SegmentRenderData(x1, x2, v1angle, v2angle)

        renderData.distToV1 = self.player.distance(seg.startVertex)
        renderData.distToNormal = segToPlayerAnge.sin * renderData.distToV1

        renderData.v1ScaleFactor = self.scaleFactor(x1, segToNormalAngle, renderData.distToNormal)
        renderData.v2ScaleFactor = self.scaleFactor(x2, segToNormalAngle, renderData.distToNormal)

        renderData.steps = (renderData.v2ScaleFactor - renderData.v1ScaleFactor) / (x2 - x1)

        renderData.rightSectorCeiling = seg.rightSec.CeilingHeight - self.player.z
        renderData.rightSectorFloor = seg.rightSec.FloorHeight - self.player.z

        renderData.ceilingStep = -(renderData.rightSectorCeiling * renderData.steps)
        renderData.ceilingEnd = round(self.halfHeight - (renderData.rightSectorCeiling * renderData.v1ScaleFactor))

        renderData.floorStep = -(renderData.rightSectorFloor * renderData.steps)
        renderData.floorStart = round(self.halfHeight - (renderData.rightSectorFloor * renderData.v1ScaleFactor))

        renderData.seg = seg

        if seg.leftSec:
            renderData.leftSectorCeiling = seg.leftSec.CeilingHeight - self.player.z
            renderData.leftSectorFloor = seg.leftSec.FloorHeight - self.player.z

            self.ceilingFloorUpdate(renderData)

            if renderData.leftSectorCeiling < renderData.rightSectorCeiling:
                renderData.drawUpperSection = True
                renderData.upperHeightStep = -(renderData.leftSectorCeiling * renderData.steps)
                renderData.upperHeight = round(self.halfHeight - (renderData.leftSectorCeiling * renderData.v1ScaleFactor))

            if renderData.leftSectorFloor > renderData.rightSectorFloor:
                renderData.drawLowerSection = True
                renderData.lowerHeightStep = -(renderData.leftSectorFloor * renderData.steps)
                renderData.lowerHeight = round(self.halfHeight - (renderData.leftSectorFloor * renderData.v1ScaleFactor))

        currentX = renderData.v1XScreen
        while currentX <= renderData.v2XScreen:
            currentCeilingEnd = renderData.ceilingEnd
            currentFloorStart = renderData.floorStart

            currentX, currentCeilingEnd, currentFloorStart, valid = self.ValidateRange(renderData, currentX, currentCeilingEnd, currentFloorStart)
            if not valid:
                continue
            if renderData.seg.leftSec:
                self.drawUpperSection(renderData, currentX, currentCeilingEnd, surf=surf)
                self.drawLowerSection(renderData, currentX, currentFloorStart, surf=surf)
            else:
                self.drawMiddleSection(renderData, currentX, currentCeilingEnd, currentFloorStart, surf=surf)
            #pygame.draw.line(self.engine.display, color, (currentX, currentCeilingEnd), (currentX, currentFloorStart))
            renderData.ceilingEnd += renderData.ceilingStep
            renderData.floorStart += renderData.floorStep
            currentX += 1

    def drawLowerSection(self, renderData, currentX, currentFloorStart, *, surf=None, color=(255, 0, 0)):
        if renderData.drawLowerSection:
            lowerHeight = renderData.lowerHeight
            renderData.lowerHeight += renderData.lowerHeightStep

            if lowerHeight <= self.ceilingClipHeight[currentX]:
                lowerHeight = self.ceilingClipHeight[currentX] + 1
            if lowerHeight <= currentFloorStart:
                #pygame.draw.line(self.engine.display, color, (currentX, lowerHeight), (currentX, currentFloorStart))
                self.engine.display.blit(pygame.transform.scale(surf, (1, int(currentFloorStart + 1) - int(lowerHeight))), (currentX, lowerHeight))
                self.floorClipHeight[currentX] = lowerHeight
            else:
                self.floorClipHeight[currentX] = currentFloorStart + 1
        elif renderData.updateFloor:
            self.floorClipHeight[currentX] = currentFloorStart + 1

    def drawMiddleSection(self, renderData, currentX, CeilingEnd, FloorStart, *, surf=None, color=(255, 0, 0), alpha=255):
        #pygame.draw.line(self.engine.display, color, (currentX, CeilingEnd), (currentX, FloorStart))
        surf.set_alpha(alpha)
        self.engine.display.blit(pygame.transform.scale(surf, (1, int(FloorStart + 1) - int(CeilingEnd))), (currentX, CeilingEnd))
        self.ceilingClipHeight[(currentX)] = self.engine.height
        self.floorClipHeight[(currentX)] = -1

    def drawUpperSection(self, renderData, currentX, currentCeilingEnd, *, surf=None, color=(255, 0, 0)):
        if renderData.drawUpperSection:
            upperHeight = renderData.upperHeight
            renderData.upperHeight += renderData.upperHeightStep

            if upperHeight >= self.floorClipHeight[currentX]:
                upperHeight = self.floorClipHeight[currentX] - 1
            if upperHeight >= currentCeilingEnd:
                #pygame.draw.line(self.engine.display, color, (currentX, currentCeilingEnd), (currentX, upperHeight))
                self.engine.display.blit(pygame.transform.scale(surf, (1, int(upperHeight + 1) - int(currentCeilingEnd))), (currentX, currentCeilingEnd))
                self.ceilingClipHeight[currentX] = upperHeight
            else:
                self.ceilingClipHeight[currentX] = currentCeilingEnd - 1
        elif renderData.updateCeiling:
            self.ceilingClipHeight[currentX] = currentCeilingEnd - 1

    def ValidateRange(self, renderData, currentX, currentCeilingEnd, currentFloorStart):
        currentX = int(currentX)
        if currentCeilingEnd < self.ceilingClipHeight[currentX] + 1:
            currentCeilingEnd = self.ceilingClipHeight[currentX] + 1
        if currentFloorStart >= self.floorClipHeight[currentX]:
            currentFloorStart = self.floorClipHeight[currentX] - 1
        if currentCeilingEnd > currentFloorStart:
            renderData.ceilingEnd += renderData.ceilingStep
            renderData.floorStart += renderData.floorStep
            currentX += 1
            return currentX, currentCeilingEnd, currentFloorStart, False
        return currentX, currentCeilingEnd, currentFloorStart, True

    def render_player(self):
        px, py = self.engine.remap_x(self.player.x), self.engine.remap_y(self.player.y)
        pygame.draw.circle(self.engine.display, (255, 0, 0), (px, py), 1)
        pygame.draw.line(self.engine.display, (255, 255, 0),
                                    (px, py),
                                    (px + self.player.cos * 5, py - self.player.sin * 5))


    def show_fps(self, pos=(5, 3)):
        text = self.font.render(str(int(self.engine.clock.get_fps())), False, (255, 255, 255))
        self.engine.display.blit(text, pos)

    def scaleFactor(self, vxscreen, segToNormalAngle, distToNormal):
        screenXAngle = self.screenXtoAngle[vxscreen] 
        scew_angle = screenXAngle + self.player.angle - segToNormalAngle
        scaleFactor = (self.p_dist_to_screen * scew_angle.cos) / (distToNormal * screenXAngle.cos)
        return clamp(scaleFactor, self.min_scale, self.max_scale)

    def ceilingFloorUpdate(self, renderData):
        if not renderData.seg.leftSec:
            renderData.updateFloor = True
            renderData.updateCeiling = True
            return

        if renderData.leftSectorCeiling != renderData.rightSectorCeiling:
            renderData.updateCeiling = True

        if renderData.leftSectorFloor != renderData.rightSectorFloor:
            renderData.updateFloor = True

        if renderData.seg.leftSec.CeilingHeight <= renderData.seg.rightSec.FloorHeight or renderData.seg.leftSec.FloorHeight >= renderData.seg.rightSec.CeilingHeight:
            renderData.updateCeiling = True
            renderData.updateFloor = True

        if renderData.seg.rightSec.CeilingHeight <= self.player.z:
            renderData.updateCeiling = False

        if renderData.seg.rightSec.FloorHeight >= self.player.z:
            renderData.updateFloor = False
