import pygame
import math
import sys
import time
import numpy as np
import random

from numba import jit
from wad_reader import WadLoader
from player import Player

class Map:
    def __init__(self, name, engine):
        self.vertexes = []
        self.linedef = []
        self.things = []
        self.nodes = []
        self.ssectors = []
        self.segs = []
        self.side_defs = []
        self.sectors = []
        self.name = name
        self.engine = engine
        self.player = self.engine.player
        self.subSectorIdentifier = np.uint16(0x8000) #32768
        self.min_x, self.min_y, self.max_x, self.max_y = 0, 0, 0, 0
        self.playerInSubsector = None
        self.maxSubsectorLimit = 120#reduces some quality
        self.continueTrasverse = 1

    @property
    def get_name(self):
        return self.name

    def build_linedef(self):
        side_def_length = len(self.side_defs)
        for linedef in self.linedef:
            linedef.startVertex = self.vertexes[linedef.startVertex]
            linedef.endVertex = self.vertexes[linedef.endVertex]
            linedef.rightSideDef = self.side_defs[linedef.rightSideDef]
            if linedef.leftSideDef < side_def_length:
                linedef.leftSideDef = self.side_defs[linedef.leftSideDef]
            else:
                linedef.leftSideDef = None

    def build_Seg(self):
        for seg in self.segs:
            seg.startVertex = self.vertexes[seg.startVertexId]
            seg.endVertex = self.vertexes[seg.endVertexId]
            seg.linedef = self.linedef[seg.lineDefId]
            seg.angle = float(seg.angle << 16) * 8.38190317e-8
            seg.offset = (seg.offset << 16) / (1 << 16)

            right_side_def = seg.linedef.rightSideDef
            left_side_def = seg.linedef.leftSideDef

            if seg.direction:
                left_side_def = seg.linedef.rightSideDef
                right_side_def = seg.linedef.leftSideDef

            seg.rightSec = None
            seg.leftSec = None
            if right_side_def:
                seg.rightSec = right_side_def.sector
            if left_side_def:
                seg.leftSec = left_side_def.sector
            del seg.startVertexId, seg.endVertexId, seg.lineDefId

    def build_sidedef(self):
        for sidedef in self.side_defs:
            sidedef.sector = self.sectors[sidedef.sectorId]
            del sidedef.sectorId

    def add_vertex(self, vertex):
        self.vertexes.append(vertex)
        self.min_x = min(self.min_x, vertex.x)
        self.min_y = min(self.min_y, vertex.y)
        self.max_x = max(self.max_x, vertex.x)
        self.max_y = max(self.max_y, vertex.y)

    def add_line(self, line_def):
        self.linedef.append(line_def)

    def add_side_def(self, side_def):
        self.side_defs.append(side_def)

    def add_thing(self, thing):
        self.things.append(thing)

    def add_node(self, node):
        self.nodes.append(node)

    def add_ssector(self, ssector):
        self.ssectors.append(ssector)

    def add_sector(self, sector):
        self.sectors.append(sector)

    def add_segs(self, seg):
        self.segs.append(seg)

    def point_on_left(self, nodeId):
        node = self.nodes[nodeId]
        dx = self.player.x - node.x
        dy = self.player.y - node.y
        return (((dx * node.changeY) - (dy * node.changeX)) <= 0)

    def render_subsector(self, subsector_id):
        subsector = self.ssectors[subsector_id]
        for i in range(subsector.segCount):
            if self.trasversedSubsectors > self.maxSubsectorLimit:
                self.continueTrasverse = 0
            seg = self.segs[subsector.firstSegId + i]
            v1Angle, v2Angle, angle1, angle2 = self.player.clip_vertexes(seg.startVertex, seg.endVertex)
            if angle1:
                #pygame.draw.line(self.engine.display, (255, 0, 0), (self.engine.remap_x(seg.startVertex.x), self.engine.remap_y(seg.startVertex.y)), (self.engine.remap_x(seg.endVertex.x), self.engine.remap_y(seg.endVertex.y)))
                #continue
                self.trasversedSubsectors += 1
                self.engine.renderer.drawWallInFov(seg, v1Angle, v2Angle, angle1, angle2)

    def render_bsp_nodes(self, nodeId=235):
        if not nodeId:
            nodeId = 235#root node ->len(self.nodes) - 1
        stack = [nodeId]
        while len(stack):
            if not self.continueTrasverse:
                return
            currentNodeId = stack.pop()
            if (currentNodeId & self.subSectorIdentifier):
                self.render_subsector(currentNodeId & (~self.subSectorIdentifier))
                if not self.playerInSubsector:
                    self.playerInSubsector = self.ssectors[currentNodeId & (~self.subSectorIdentifier)]
                continue
            #reversing the order of append in order to visit secondly added node first
            if self.point_on_left(currentNodeId):
                stack.append(self.nodes[currentNodeId].rightChildId)
                stack.append(self.nodes[currentNodeId].leftChildId)
            else:
                stack.append(self.nodes[currentNodeId].leftChildId)
                stack.append(self.nodes[currentNodeId].rightChildId)

    def locate_player(self):
        for thing in self.things:
            if thing.type == 1:
                self.player.set_x(thing.x)
                self.player.set_y(thing.y)
                self.player.set_angle(thing.angle)
                self.player.id = 1
                break

    def initFrame(self):
        self.playerInSubsector = None
        self.continueTrasverse = 1
        self.trasversedSubsectors = 0

