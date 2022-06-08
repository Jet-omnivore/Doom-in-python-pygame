import pygame

from math import atan2, pi
from constants import ANG180
from data_types import RenderData
from funcs import isClosedDoor, isPortal, angleToScreenX


DEG1 = ANG180 / pi
CHECKCOORD = [
    [3, 0, 2, 1],
    [3, 0, 2, 0],
    [3, 1, 2, 0],
    [0, 0, 0, 0],
    [2, 0, 2, 1],
    [0, 0, 0, 0],
    [3, 1, 3, 0],
    [0, 0, 0, 0],
    [2, 0, 3, 1],
    [2, 1, 3, 1],
    [2, 1, 3, 0]
    ]
class BOXSIDE:
    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3


class Map:
    def __init__(self, name, engine):
        self.data = {}

        self.name = name
        self.engine = engine
        self.player = self.engine.player
        self.subSecIdentifier = 0x8000 # 32768 uint16? could be bug here
        self.playerInSubsector = None

    def get_name(self):
        return self.name

    def build_linedef(self):
        # acutal lines/outlines of game map
        side_def_length = len(self.data['SIDEDEFS'])
        for linedef in self.data['LINEDEFS']:
            linedef.startVertex = self.data['VERTEXES'][linedef.startVertex]
            linedef.endVertex = self.data['VERTEXES'][linedef.endVertex]
            linedef.rightSideDef = self.data['SIDEDEFS'][linedef.rightSideDef]

            if linedef.leftSideDef < side_def_length:
                linedef.leftSideDef = self.data['SIDEDEFS'][linedef.leftSideDef]
            else:
                linedef.leftSideDef = None

    def build_Seg(self):
        for seg in self.data['SEGS']:
            seg.startVertex = self.data['VERTEXES'][seg.startVertexId]
            seg.endVertex = self.data['VERTEXES'][seg.endVertexId]
            seg.linedef = self.data['LINEDEFS'][seg.lineDefId]
            seg.angle = float(seg.angle << 16) * 8.38190317e-8
            seg.offset = (seg.offset << 16) / (1 << 16)

            right_side_def = seg.linedef.rightSideDef
            left_side_def = seg.linedef.leftSideDef

            if seg.direction:
                left_side_def = seg.linedef.rightSideDef
                right_side_def = seg.linedef.leftSideDef
                seg.sidedef = seg.linedef.leftSideDef
            else:
                seg.sidedef = seg.linedef.rightSideDef

            seg.frontSec = right_side_def.sector
            seg.backSec = None

            if left_side_def:
                seg.backSec = left_side_def.sector
            del seg.startVertexId, seg.endVertexId, seg.lineDefId

    def build_sidedef(self):
        
        def check_texture(texture_name):
            if texture_name == '-':
                return ''
            return texture_name.upper()

        for sidedef in self.data['SIDEDEFS']:
            sidedef.sector = self.data['SECTORS'][sidedef.sectorId]
            sidedef.middleTexture = check_texture(sidedef.middleTexture)
            sidedef.upperTexture = check_texture(sidedef.upperTexture)
            sidedef.lowerTexture = check_texture(sidedef.lowerTexture)
            del sidedef.sectorId

    def add_data(self, data_name, data):
        self.data.setdefault(data_name, [])  # dict has key or not? 
        self.data[data_name].append(data)

    def add_line(self, line):
        # line clipping
        angle1 = self.player.angleToVertex(line.startVertex)        
        angle2 = self.player.angleToVertex(line.endVertex)
        
        clipangle = self.player.half_fov
        span = (angle1 - angle2) % 360

        if span >= ANG180:
            return

        rw_angle1 = angle1
        rw_angle2 = angle2
        angle1 -= self.player.angle
        angle2 -= self.player.angle

        tspan = (angle1 + clipangle) % 360
        if tspan > 2 * clipangle:
            tspan -= 2 * clipangle
            if tspan >= span:
                return
            angle1 = clipangle
        tspan = (clipangle - angle2) % 360
        if tspan > 2 * clipangle:
            tspan -= 2 * clipangle
            if tspan >= span:
                return
            angle2 = -clipangle

        angle1 += 90
        angle2 += 90 
        x1 = angleToScreenX(angle1)
        x2 = angleToScreenX(angle2)

        if x1 == x2:
            return

        renderData = RenderData(x1, x2, rw_angle1, rw_angle2)
        renderData.seg = line
        # only solid walls / one sided wall
        if not line.backSec:
            self.engine.renderer.clipSolidWalls(renderData)
            return
    
        if isClosedDoor(line):
            self.engine.renderer.clipSolidWalls(renderData)
            return

        if isPortal(line):
            self.engine.renderer.clipPassWalls(renderData)

    def point_on_left(self, nodeId):
        node = self.data['NODES'][nodeId]
        dx = self.player.x - node.x
        dy = self.player.y - node.y
        return (dx * node.changeY - dy * node.changeX) <= 0

    def render_subsector(self, subsector_id):
        subsector = self.data['SSECTORS'][subsector_id]
        for i in range(subsector.segCount):
            seg = self.data['SEGS'][subsector.firstSegId + i]
            self.add_line(seg)

    def render_bsp_nodes(self):
        nodeId = len(self.data['NODES']) - 1 # root node
        stack = [nodeId]

        isLeafNode = lambda nodeId: nodeId & self.subSecIdentifier
        getNodeIndex = lambda nodeId: nodeId & (~self.subSecIdentifier)

        while len(stack):
            currentNodeId = stack.pop()
            if isLeafNode(currentNodeId):
                self.render_subsector(getNodeIndex(currentNodeId))
                if not self.playerInSubsector:
                    self.playerInSubsector = self.data['SSECTORS'][getNodeIndex(currentNodeId)]
                continue 
            side = self.point_on_left(currentNodeId)
            node = self.data['NODES'][currentNodeId]
            stack.append(node.children[side])
            # implement bbox to speed up the process
            stack.append(node.children[side ^ 1])

    def locate_player(self):
        thing = self.data['THINGS'][0]
        self.player.set_x(thing.x)
        self.player.set_y(thing.y)
        self.player.set_angle(thing.angle)
        self.player.id = 1

    def initFrame(self):
        self.playerInSubsector = None
