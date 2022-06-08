import pygame
import math

from classDef import classicDoomScreenXtoView
from constants import ANG90
from funcs import dcos, dtan, dsin, isClosedDoor
# dcos, dtan, dsin angles are in degrees
from tex_manager import TextureManager
from doomdata import LINDEF_FLAGS


def clamp(n, min_val, max_val):
    return max(min(n, max_val), min_val)


SKYFLATNAME = "F_SKY1"

# left sector -> back sector


class Renderer:
    def __init__(self, engine):
        self.engine = engine
        self.player = self.engine.player
        self.game_map = self.engine.game_map

        self.font = pygame.font.SysFont('arial', 10)

        self.screenXtoAngle = dict(enumerate(classicDoomScreenXtoView))
        
        self.halfHeight = self.engine.height / 2
        self.halfWidth = self.engine.width / 2

        halfFOV = (self.player.fov / 2)
        self.perpendicularDistToScreen = self.halfWidth / dtan(halfFOV)

        self.maxScale = 64
        self.minScale = 0.00390625

        self.floorClipHeight = []
        self.ceilingClipHeight = []

        self.TextureManager = TextureManager(self)

    def init_frame(self):
        self.wallRanges = [[-math.inf, -1], [self.engine.width, math.inf]]
        self.floorClipHeight = [self.engine.height] * self.engine.width
        self.ceilingClipHeight = [-1] * self.engine.width

    def clipSolidWalls(self, renderData):
        currentWallIndex = 0
        START = 0
        END = 1
        x1, x2 = renderData.x1, renderData.x2

        for currentWallIndex, wallRange in enumerate(self.wallRanges):
            if wallRange[1] >= x1 - 1:
                break
        foundClipWall = self.wallRanges[currentWallIndex]

        if x1 < foundClipWall[START]:
            if x2 < foundClipWall[START] - 1:
                # the wall is in the left and not touching the to another wall(right wall/foundClipWall)
                self.storeWallRange(renderData)
                self.wallRanges.insert(currentWallIndex, [x1, x2])
                return
            # otherwise if the right side of wall is hidden by another wall (found clip wall) 
            # then draw the wall upto left side of found clip wall
            renderData.x2 = foundClipWall[START] - 1
            self.storeWallRange(renderData)
            foundClipWall[START] = x1

        if x2 <= foundClipWall[END]:
            return

        nextWallIndex = currentWallIndex
        nextWall = foundClipWall

        while x2 >= self.wallRanges[nextWallIndex + 1][START] - 1:
            renderData.x1 = nextWall[END] + 1
            renderData.x2 = self.wallRanges[nextWallIndex + 1][START] - 1
            self.storeWallRange(renderData)

            nextWallIndex += 1
            nextWall = self.wallRanges[nextWallIndex]

            if x2 <= nextWall[END]:
                foundClipWall[END] = nextWall[END]
                if nextWallIndex is not currentWallIndex:
                    currentWallIndex += 1
                    foundClipWall = self.wallRanges[currentWallIndex]
                    nextWallIndex += 1
                    del self.wallRanges[currentWallIndex:nextWallIndex]
                return

        renderData.x1, renderData.x2 = nextWall[END] + 1, x2
        self.storeWallRange(renderData)
        foundClipWall[END] = x2

        if nextWallIndex is not currentWallIndex:
            del self.wallRanges[currentWallIndex + 1:nextWallIndex + 1]

    def clipPassWalls(self, renderData):
        currentWallIndex = 0
        START = 0
        END = 1
        x1, x2 = renderData.x1, renderData.x2
        
        for currentWallIndex, wallRange in enumerate(self.wallRanges):
            if wallRange[END] >= x1 - 1:
                break
        foundClipWall = self.wallRanges[currentWallIndex]

        if x1 < foundClipWall[START]:
            if x2 < foundClipWall[START] - 1:
                self.storeWallRange(renderData)
                return
            renderData.x2 = foundClipWall[START] - 1
            self.storeWallRange(renderData)

        if x2 <= foundClipWall[END]:
            return

        nextWallIndex = currentWallIndex
        nextWall = foundClipWall

        while x2 >= self.wallRanges[nextWallIndex + 1][START] - 1:
            renderData.x1 = nextWall[END] + 1
            renderData.x2 = self.wallRanges[nextWallIndex + 1][START] - 1
            self.storeWallRange(renderData)

            nextWallIndex += 1
            nextWall = self.wallRanges[nextWallIndex]

            if x2 <= nextWall[END]:
                return

        renderData.x1, renderData.x2 = nextWall[END] + 1, x2
        self.storeWallRange(renderData)

    def storeWallRange(self, renderData):
        if renderData.x1 == renderData.x2:
            return

        seg = renderData.seg
        sidedef = seg.sidedef
        frontSec = seg.frontSec
        linedef = seg.linedef
        viewz = self.player.z
        
        linedef.flags |= LINDEF_FLAGS.MAPPED.value

        renderData.normalAngle = ANG90 + seg.angle # adding 90 degrees

        # equivalent to (v1angle.angle - NormalAngle) offsetangle
        normalToV1Angle = renderData.normalAngle - renderData.angle1

        renderData.distToV1 = self.player.distance(seg.startVertex)

        renderData.distofNormal = dcos(normalToV1Angle) * renderData.distToV1 # rw_distance

        # v1ScaleFactor
        renderData.scale1 = self.scaleFactor(renderData.x1, renderData)
        # v2ScaleFactor
        renderData.scale2 = self.scaleFactor(renderData.x2, renderData)

        renderData.scaleSteps = (renderData.scale2 - renderData.scale1) / (renderData.x2 - renderData.x1)

        renderData.worldtop = frontSec.CeilingHeight  - viewz  # frontSecCeiling
        renderData.worldbottom = frontSec.FloorHeight - viewz  # frontSecFloor

        renderData.ceilingStep = -(renderData.worldtop * renderData.scaleSteps)  # at 681
        # the hegiht where the ceiling ends/ the y value of end ceiling
        renderData.ceilingEnd = round(self.halfHeight - (renderData.worldtop * renderData.scale1))

        renderData.floorStep = -(renderData.worldbottom * renderData.scaleSteps)
        # the height where floor starts / the y value of floor start
        renderData.floorStart = round(self.halfHeight - (renderData.worldbottom * renderData.scale1))

        # markfloor = updateFloor, markceiling = updateCeiling

        toptexturemid = bottomtexturemid = 0
        renderData.midtexture = renderData.bottomtexture = renderData.toptexture = renderData.masked_texture = 0
        if not seg.backSec:
            renderData.markfloor = renderData.markceiling = True
            renderData.midtexture = 1
            if linedef.flags & LINDEF_FLAGS.DONTPEGBOTTOM.value:
                textureheight = self.TextureManager.wall_textures[sidedef.middleTexture].get_height()
                vtop = frontSec.FloorHeight + textureheight
                renderData.midtexturemid = vtop - viewz
            else:
                renderData.midtexturemid = renderData.worldtop
            
            renderData.midtexturemid += sidedef.yoffset

        else:
            renderData.backSecCeiling = seg.backSec.CeilingHeight - viewz
            renderData.backSecFloor = seg.backSec.FloorHeight - viewz

            if frontSec.CeilingTex == seg.backSec.CeilingTex == SKYFLATNAME: # replace 'F_SKY1' with skyflatnum
                renderData.worldtop = renderData.worldbottom

            self.ceilingFloorUpdate(renderData)

            # renderData.backSecCeiling == worldtop
            # renderData.backSecFloor == worldbottom
            if renderData.backSecCeiling < renderData.worldtop:
                renderData.drawUpperSection = True
                renderData.upperHeightStep = -(renderData.backSecCeiling * renderData.scaleSteps)
                # upper height -> height of the upper section of portals/ y value of bottom part of upper section rect(portal)
                renderData.upperHeight = round(self.halfHeight - (renderData.backSecCeiling * renderData.scale1))

                if sidedef.upperTexture:
                    renderData.toptexture = 1
                if linedef.flags & LINDEF_FLAGS.DONTPEGTOP.value:
                    toptexturemid = renderData.worldtop
                else:
                    textureheight = self.TextureManager.wall_textures[sidedef.upperTexture].get_height()
                    vtop = seg.backSec.CeilingHeight + textureheight
                    toptexturemid = vtop - viewz

            if renderData.backSecFloor > renderData.worldbottom:
                renderData.drawLowerSection = True
                renderData.lowerHeightStep = -(renderData.backSecFloor * renderData.scaleSteps)
                # lower height -> height of the lower section of portals/ y value of top part of lower section rect(portal)
                if sidedef.lowerTexture:
                    renderData.bottomtexture = 1
                renderData.lowerHeight = round(self.halfHeight - (renderData.backSecFloor * renderData.scale1))

                if linedef.flags & LINDEF_FLAGS.DONTPEGBOTTOM.value:
                    bottomtexturemid = renderData.backSecCeiling
                else:
                    bottomtexturemid = renderData.backSecFloor

            toptexturemid += sidedef.yoffset
            bottomtexturemid += sidedef.yoffset

            if sidedef.middleTexture:
                renderData.masked_texture = True
                # 2 lines more line 608
            
        renderData.segtextured = renderData.midtexture | renderData.toptexture | renderData.bottomtexture | renderData.masked_texture
        if renderData.segtextured:
            renderData.rw_offset = -dsin(normalToV1Angle) * renderData.distToV1
            renderData.rw_offset += sidedef.xoffset + seg.offset
            renderData.rw_centerangle = self.player.angle - renderData.normalAngle # ang90 ?

            # fixed colormap implementation lightnum line 639

        # check plane function

        self.renderSegLoop(renderData)

    def renderSegLoop(self, renderData):
        currentX = renderData.x1
        lower_surf = self.TextureManager.wall_textures.get(renderData.rightSideLowerTex, None)
        upper_surf = self.TextureManager.wall_textures.get(renderData.rightSideUpperTex, None)

        columns_to_draw = []
        for currentX in range(renderData.x1, renderData.x2 + 1):  # renderData.v2XScreen? --> outline
            returned = self.ValidateRange(renderData, currentX)
            if not returned:
                continue

            currentX, currentCeilingEnd, currentFloorStart = returned

            # mark ceiling check and markfloor check at 219
            
            texture_column = 0
            if renderData.segtextured:
                angle = renderData.rw_centerangle + self.screenXtoAngle[currentX]
                texture_column = renderData.rw_offset - dtan(angle) * renderData.distofNormal

                # calculate lighting at 260
                iscale = 1 / renderData.scale1

            # draw middle section
            if renderData.midtexture:
                mid_tex = renderData.seg.sidedef.middleTexture 
                source = self.TextureManager.get_column(mid_tex, texture_column)
                scale = round(currentFloorStart + 1 - currentCeilingEnd)

                tex_scale = round(renderData.floorStart - renderData.ceilingEnd + 1)
                source_column = pygame.transform.scale(source, (1, tex_scale))
                # self.engine.test.append((tex_scale / source.get_height())/ renderData.scale1)
                real_column = source_column.subsurface((0, abs(currentCeilingEnd-renderData.ceilingEnd), 1, scale))#source_column.get_height() - abs(currentCeilingEnd-renderData.ceilingEnd)))
                columns_to_draw.append((real_column, (currentX, currentCeilingEnd)))
                # self.engine.display.blit(real_column, (currentX, currentCeilingEnd))

                self.ceilingClipHeight[currentX] = self.engine.height
                self.floorClipHeight[currentX] = -1 
            else:
                # self.drawUpperSection(renderData, currentX, currentCeilingEnd, upper_surf)
                #---------------draw upper Section---------------------# 

                if renderData.toptexture:
                    mid = renderData.upperHeight
                    renderData.upperHeight += renderData.upperHeightStep
                    if mid >= self.floorClipHeight[currentX]:
                        mid = self.floorClipHeight[currentX] + 1
                    if mid >= currentCeilingEnd:
                        upperTex = renderData.seg.sidedef.upperTexture 
                        wall_column = self.TextureManager.get_column(upperTex, texture_column)
                        wall_height = int(mid + 1 - currentCeilingEnd)

                        expected_height = round(abs(renderData.upperHeight + 1 - renderData.ceilingEnd))
                        expected_tex = pygame.transform.scale(wall_column, (1, expected_height))
                        y_pos = abs(currentCeilingEnd - renderData.ceilingEnd)
                        if y_pos + wall_height <= expected_height:
                            actual_tex = expected_tex.subsurface((0, y_pos, 1, wall_height))
                        else:
                            actual_tex = expected_tex.subsurface((0, y_pos, 1, expected_height - y_pos))
                        columns_to_draw.append((actual_tex, (currentX, currentCeilingEnd)))
                        self.ceilingClipHeight[currentX] = mid
                    else:
                        self.ceilingClipHeight[currentX] = currentCeilingEnd - 1
                else:
                    if renderData.markceiling:
                        self.ceilingClipHeight[currentX] = currentCeilingEnd - 1

                #------------------------------------------------------#
                # self.drawLowerSection(renderData, currentX, currentFloorStart, lower_surf)
                #---------------draw lower Section---------------------# 

                if renderData.bottomtexture:
                    mid = renderData.lowerHeight
                    renderData.lowerHeight += renderData.lowerHeightStep

                    if mid <= self.ceilingClipHeight[currentX]:
                        mid = self.ceilingClipHeight[currentX] + 1

                    if mid <= currentFloorStart:
                        lowerTex = renderData.seg.sidedef.lowerTexture
                        wall_column = self.TextureManager.get_column(lowerTex, texture_column)
                        wall_height = int(currentFloorStart + 1 - mid)

                        expected_height = abs(round((renderData.floorStart + 1 - renderData.lowerHeight)))
                        expected_tex = pygame.transform.scale(wall_column, (1, expected_height))
                        y_pos = abs(renderData.lowerHeight - mid)
                        if wall_height + y_pos <= expected_height:
                            actual_tex = expected_tex.subsurface((0, y_pos, 1, wall_height))
                        else:
                            actual_tex = expected_tex.subsurface((0, y_pos, 1, expected_height - y_pos))
                        # y_pos = abs(round(mid))
                        # if y_pos + wall_height <= expected_height:
                            # actual_tex = expected_tex.subsurface((0, y_pos, 1, wall_height))
                        # else:
                            # actual_tex = expected_tex.subsurface((0, y_pos, 1, expected_height - y_pos))
                        columns_to_draw.append((actual_tex, (currentX, mid)))
                        self.floorClipHeight[currentX] = mid
                    else:
                        self.floorClipHeight[currentX] = currentFloorStart + 1
                else:
                    if renderData.markfloor: 
                        self.floorClipHeight[currentX] = currentFloorStart + 1

                #------------------------------------------------------#

            renderData.scale1 += renderData.scaleSteps
            renderData.ceilingEnd += renderData.ceilingStep
            renderData.floorStart += renderData.floorStep
        self.engine.display.blits(columns_to_draw)

    def drawLowerSection(self, renderData, currentX, currentFloorStart, surf):
        if not surf:
            return
        if not renderData.drawLowerSection:
            if renderData.markfloor:
                self.floorClipHeight[currentX] = currentFloorStart + 1
            return
        
        lowerHeight = renderData.lowerHeight
        renderData.lowerHeight += renderData.lowerHeightStep

        if lowerHeight <= self.ceilingClipHeight[currentX]:
            lowerHeight = self.ceilingClipHeight[currentX] + 1
       
        if lowerHeight <= currentFloorStart:
            # dist = self.distance(currentX, renderData)
            # alpha = (50000 / (int(dist) + 0.001))
            # surf.set_alpha(alpha)
            # self.engine.display.blit(pygame.transform.scale(surf, (1, int(currentFloorStart + 1) - int(lowerHeight))), (currentX, lowerHeight))
            wall_column = pygame.transform.scale(surf.subsurface((currentX % surf.get_width(), 0, 1, surf.get_height())), (1, int(currentFloorStart + 1) - int(lowerHeight)))
            self.engine.display.blit(wall_column, (currentX, lowerHeight))
            self.floorClipHeight[currentX] = lowerHeight
        else:
            self.floorClipHeight[currentX] = currentFloorStart + 1

    def drawMiddleSection(self, renderData, currentX, CeilingEnd, FloorStart, surf):
        if not surf:
            return
        print("boop")
        # surf = self.TextureManager.textures[renderData.rightSideMidTex]
        # dist = self.distance(currentX, renderData)
        # alpha = (50000 / (int(dist) + 0.001))
        # surf.set_alpha(alpha)
        angle = renderData.rw_centerangle + self.screenXtoAngle[currentX]
        tex_col = renderData.rw_offset - dtan(angle) * renderData.distofNormal
        wall_height = int(FloorStart + 1 - CeilingEnd)
        wall_column = pygame.transform.scale(surf.subsurface((tex_col % surf.get_width(), 0, 1, surf.get_height())), (1, wall_height))
        self.engine.display.blit(wall_column, (currentX, CeilingEnd))

        self.ceilingClipHeight[currentX] = self.engine.height
        self.floorClipHeight[currentX] = -1 

    def drawUpperSection(self, renderData, currentX, currentCeilingEnd, surf):
        if not surf:
            return
        if not renderData.drawUpperSection:
            if renderData.markceiling:
                self.ceilingClipHeight[currentX] = currentCeilingEnd - 1
            return

        upperHeight = renderData.upperHeight
        renderData.upperHeight += renderData.upperHeightStep

        if upperHeight >= self.floorClipHeight[currentX]:
            upperHeight = self.floorClipHeight[currentX] + 1

        if upperHeight >= currentCeilingEnd:

            # dist = self.distance(currentX, renderData)
            # alpha = (50000 / (int(dist) + 0.001))
            # surf.set_alpha(alpha)

            wall_height = int(upperHeight + 1) - int(currentCeilingEnd)
            wall_column = pygame.transform.scale(surf.subsurface((currentX % surf.get_width(), 0, 1, surf.get_height())), (1, wall_height))
            self.engine.display.blit(wall_column, (currentX, currentCeilingEnd))
            self.ceilingClipHeight[currentX] = upperHeight
        else:
            self.ceilingClipHeight[currentX] = currentCeilingEnd - 1

    def ValidateRange(self, renderData, currentX):
        yl = renderData.ceilingEnd
        yh = renderData.floorStart

        if yl < self.ceilingClipHeight[currentX] + 1:
            yl = self.ceilingClipHeight[currentX] + 1
        if yh >= self.floorClipHeight[currentX]:
            yh = self.floorClipHeight[currentX] - 1
        if yl > yh:
            renderData.ceilingEnd += renderData.ceilingStep
            renderData.floorStart += renderData.floorStep
            return 
        return currentX, yl, yh

    def show_fps(self, pos=(5, 3)) -> None:
        text = self.font.render(str(int(self.engine.clock.get_fps())), False, (255, 255, 255))
        self.engine.display.blit(text, pos)

    def scaleFactor(self, vxscreen: int, renderData) -> int:
        '''
        (distofNormal / scewAngle.cos) => distance to the vertex
        (self.perpendicularDistToScreen / screenXAngle.cos) => distance to the screen
        scaling factor = distance to the vertex / distance to the screen
        simplifying (self.perpendicularDistToScreen / screenXAngle.cos) / (distofNormal / scew_angle.cos)
        we get, (self.perpendicularDistToScreen * scew_angle.cos) / (distofNormal * screenXAngle.cos)
        '''

        screenXAngle = self.screenXtoAngle[vxscreen]
        scew_angle = screenXAngle + self.player.angle - renderData.normalAngle
        dist = renderData.distofNormal * dcos(screenXAngle)
        scaleFactor = (self.perpendicularDistToScreen * dcos(scew_angle)) / dist
        return clamp(scaleFactor, self.minScale, self.maxScale)

    def distance(self, vxscreen, renderData) -> float:
        '''
        inverseNormalAngle = normalAngle - angle180
        viewRelativeAngle= inverseNormalAngle - (self.player.angle + viewAngle)
        interceptDistance = distofNormal / viewRelativeAngle.cos
        return abs(viewAngle.cos * interceptDistance)
        '''

        viewAngle = self.screenXtoAngle[vxscreen]
        viewRelativeAngle = viewAngle + self.player.angle - renderData.normalAngle
        interceptDistance = renderData.distofNormal / dcos(viewRelativeAngle)
        return abs(interceptDistance)

    def ceilingFloorUpdate(self, renderData) -> None:
        worldhigh = renderData.backSecCeiling
        worldlow = renderData.backSecFloor
        frontSec = renderData.seg.frontSec

        if worldhigh != renderData.worldtop:
            renderData.markceiling = True

        if worldlow != renderData.worldbottom:
            renderData.markfloor = True

        if isClosedDoor(renderData.seg):
            renderData.markceiling = True
            renderData.markfloor = True

        if frontSec.CeilingHeight <= self.player.z and frontSec.CeilingTex != SKYFLATNAME:
            renderData.markceiling = False

        if frontSec.FloorHeight   >= self.player.z:
            renderData.markfloor = False
