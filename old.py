# clipping line/segs
angle1 = self.player.angleToVertex(line.startVertex)        
angle2 = self.player.angleToVertex(line.endVertex)

clipangle = self.player.half_fov
span = (angle1 - angle2) % 360

if span >= 180:
    return

rw_angle1 = angle1
rw_angle2 = angle2
angle1 = (angle1 - self.player.angle) % 360
angle2 = (angle2 - self.player.angle) % 360

tspan = (angle1 + clipangle) % 360
if tspan > 2 * clipangle:
    tspan = (tspan - 2 * clipangle) % 360
    if tspan >= span:
        return
    angle1 = clipangle
tspan = (clipangle - angle2) % 360
if tspan > 2 * clipangle:
    tspan = (tspan - 2 * clipangle) % 360
    if tspan >= span:
        return
    angle2 = (-clipangle) % 360

angle1 = (angle1 + 90) % 360
angle2 = (angle2 + 90) % 360


def clipSolidWalls(self, seg, x1, x2, angle1, angle2):
        currentWallIndex = 0
        wallRangeLength = len(self.wallRanges)
        if wallRangeLength < 2:
            return

        while currentWallIndex < wallRangeLength and self.wallRanges[currentWallIndex][1] < x1 - 1:
            currentWallIndex += 1
        foundClipWall = self.wallRanges[currentWallIndex]

        if x1 < foundClipWall[0]:
            if x2 < foundClipWall[0] - 1:
                self.storeWallRange(seg, x1, x2, angle1, angle2)
                self.wallRanges.insert(currentWallIndex, [x1, x2])
                return
            self.storeWallRange(seg, x1, foundClipWall[0] - 1, angle1, angle2)
            foundClipWall[0] = x1

        if x2 <= foundClipWall[1]:
            return

        nextWallIndex = currentWallIndex
        nextWall = foundClipWall

        while x2 >= self.wallRanges[nextWallIndex + 1][0] - 1:
            self.storeWallRange(seg, nextWall[1] + 1, self.wallRanges[nextWallIndex + 1][0] - 1, angle1, angle2)
            nextWallIndex += 1
            nextWall = self.wallRanges[nextWallIndex]

            if x2 <= nextWall[1]:
                foundClipWall[1] = nextWall[1]
                if nextWallIndex != currentWallIndex:
                    currentWallIndex += 1
                    foundClipWall = self.wallRanges[currentWallIndex]
                    nextWallIndex += 1
                    del self.wallRanges[currentWallIndex:nextWallIndex]
                return

        self.storeWallRange(seg, nextWall[1] + 1, x2, angle1, angle2)
        foundClipWall[1] = x2

        if nextWallIndex != currentWallIndex:
            currentWallIndex += 1
            nextWallIndex += 1
            del self.wallRanges[currentWallIndex:nextWallIndex]

    def clipPassWalls(self, seg, x1, x2, angle1, angle2):
        currentWallIndex = 0
        length = len(self.wallRanges)

        while currentWallIndex < length and self.wallRanges[currentWallIndex][1] < x1 - 1:
            currentWallIndex += 1
        foundClipWall = self.wallRanges[currentWallIndex]

        if x1 < foundClipWall[0]:
            if x2 < foundClipWall[0] - 1:
                self.storeWallRange(seg, x1, x2, angle1, angle2)
                return
            self.storeWallRange(seg, x1, foundClipWall[0] - 1, angle1, angle2)

        if x2 <= foundClipWall[1]:
            return

        nextWallIndex = currentWallIndex
        nextWall = foundClipWall

        while x2 >= self.wallRanges[nextWallIndex + 1][0] - 1:
            self.storeWallRange(seg, nextWall[1] + 1, self.wallRanges[nextWallIndex + 1][0] - 1, angle1, angle2)
            nextWallIndex += 1
            nextWall = self.wallRanges[nextWallIndex]

            if x2 <= nextWall[1]:
                return

        self.storeWallRange(seg, nextWall[1] + 1, x2, angle1, angle2)


# clips walls in fov
def clipVertexes(self, v1, v2):
    angle1 = self.angleToVertex(v1)
    angle2 = self.angleToVertex(v2)
    tempAngle1, tempAngle2 = angle1, angle2
    span = (angle1 - angle2) % 360

    
    if ((angle1 - angle2) < 0 and (angle1 - angle2) >= -180) or (angle1 - angle2) >= 180:
        return

    span %= 360
    angle1 -= (self.angle)
    angle1 %= 360
    angle2 -= self.angle
    angle2 %= 360

    if (angle1 + self.half_fov) % 360 > self.fov:
        if (angle1 - self.half_fov) >= span: # could be bug here
            return
        angle1 = self.half_fov

    if (self.half_fov - angle2) % 360 > self.fov:
        angle2 = -self.half_fov
    angle1 += 90
    angle2 += 90
    return tempAngle1, tempAngle2, angle1, angle2
