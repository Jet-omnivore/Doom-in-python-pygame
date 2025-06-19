from dataclasses import dataclass, field, InitVar
from ctypes import c_uint16, c_uint32
from pygame import Vector2
from plane import Visplane
from typing import Optional


uint16 = c_uint16
uint32 = c_uint32


@dataclass
class Header:
    wad_type        :    str
    dir_count       :    uint32
    dir_offset      :    uint32


@dataclass
class Directory:
    lump_offset     :    uint32
    lump_size       :    uint32
    lump_name       :    uint32


def Vertex(x, y):
    return Vector2(x, y)


@dataclass
class SideDef:
    xoffset         :    uint16  # textureoffset
    yoffset         :    uint16  # rowoffset
    upperTexture    :    str
    lowerTexture    :    str
    middleTexture   :    str
    sectorId        :    uint16  = field(repr=False)


@dataclass
class LineDef:
    startVertex     :   int
    endVertex       :   int
    flags           :   int
    lineType        :   int
    secTag          :   str
    rightSideDef    :   SideDef
    leftSideDef     :   SideDef


@dataclass
class Thing:
    x               :   int
    y               :   int
    angle           :   float
    type            :   int
    flags           :   int


@dataclass
class SubSector:
    segCount        :   int
    firstSegId      :   int


@dataclass
class Sector:
    FloorHeight     :   int
    CeilingHeight   :   int
    FloorTex        :   str
    CeilingTex      :   str
    LightLevel      :   uint16
    type            :   uint16
    tag             :   uint16


@dataclass
class Seg:
    startVertexId   :   uint16 = field(repr=False)
    endVertexId     :   uint16 = field(repr=False)
    angle           :   float
    lineDefId       :   uint16 = field(repr=False)
    direction       :   uint16
    offset          :   uint16


@dataclass
class Node:
    x               :   int
    y               :   int

    changeX         :   int
    changeY         :   int

    rightBoxTop     :   InitVar[int]
    rightBoxBottom  :   InitVar[int]
    rightBoxLeft    :   InitVar[int]
    rightBoxRight   :   InitVar[int]

    leftBoxTop      :   InitVar[int]
    leftBoxBottom   :   InitVar[int]
    leftBoxLeft     :   InitVar[int]
    leftBoxRight    :   InitVar[int]
    
    rightChildId    :   int
    leftChildId     :   int

    def __post_init__(self, rightBoxTop, 
                            rightBoxBottom, 
                            rightBoxLeft, 
                            rightBoxRight,

                            leftBoxTop, 
                            leftBoxBottom, 
                            leftBoxLeft, 
                            leftBoxRight,):

        self.rightBox = [rightBoxTop,
                         rightBoxBottom,
                         rightBoxLeft,
                         rightBoxRight]

        self.leftBox = [leftBoxTop,
                        leftBoxBottom,
                        leftBoxLeft,
                        leftBoxRight]

        self.bboxes = [self.leftBox, self.rightBox]
        self.children = [self.leftChildId, self.rightChildId]


@dataclass
class RenderData:
    x1: int        
    x2: int

    angle1: float    #  angle to vertex 1
    angle2: float    #  angle to vertex 2

    # distanceToV1: float = 0
    # distanceToNormal: float = 0
    # normalAngle: float = 0
    # v1ScaleFactor: float = 0
    # v2ScaleFactor: float = 0
    # steps: float = 0

    # rightSecCeiling: float = 0
    # rightSecFloor: float = 0
    # ceilingStep: float = 0
    # ceilingEnd: float = 0
    # floorStep: float = 0
    # floorStart: float = 0

    # leftSecCeiling: float = 0
    # leftSecFloor: float = 0

    drawUpperSection: bool = False
    drawLowerSection: bool = False

    # upperHeightStep: float = 0
    # upperHeight: float = 0
    # lowerHeightStep: float = 0
    # lowerHeight: float = 0

    markfloor: bool = False
    markceiling: bool = False

    # ceilingPlane: Optional[Visplane] = None
    # floorPlane: Optional[Visplane] = None

    # seg: Optional[Seg] = None
    
    # a class to store data

    @property
    def rightSideMidTex(self):
        return self.seg.linedef.rightSideDef.middleTexture

    @property
    def rightSideLowerTex(self):
        return self.seg.linedef.rightSideDef.lowerTexture

    @property
    def rightSideUpperTex(self):
        return self.seg.linedef.rightSideDef.upperTexture
