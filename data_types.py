from dataclasses import dataclass
from angle import Angle
from numpy import uint16, uint32

@dataclass
class Header:
    wad_type: str
    dir_count: uint32
    dir_offset: uint32

@dataclass
class Directory:
    lump_offset: uint32
    lump_size: uint32
    lump_name: uint32

@dataclass
class Vertex:
    x: int
    y: int

@dataclass
class SideDef:
    xoffset: uint16
    yoffset: uint16
    upperTexture: str
    lowerTexture: str
    middleTexture: str
    sectorId: uint16

@dataclass
class LineDef:
    startVertex: int
    endVertex: int
    flags: int
    lineType: int
    secTag: str
    rightSideDef: SideDef
    leftSideDef: SideDef

@dataclass
class Thing:
    x: int 
    y: int
    angle: Angle
    type: int
    flags: int

@dataclass
class SubSector:
    segCount: int
    firstSegId: int

@dataclass
class Seg:
    startVertexId: uint16
    endVertexId: uint16
    angle: Angle
    lineDefId: uint16
    direction: uint16
    offset: uint16

@dataclass
class Sector:
    FloorHeight: int
    CeilingHeight: int
    FloorTex: str
    CeilingTex: str
    LightLevel: uint16
    type: uint16
    tag: uint16

@dataclass
class Node:
    x: int
    y: int

    changeX: int
    changeY: int

    rightBoxTop: int
    rightBoxBottom: int
    rightBoxLeft: int
    rightBoxRight: int

    leftBoxTop: int
    leftBoxBottom: int
    leftBoxLeft: int
    leftBoxRight: int

    rightChildId: uint16
    leftChildId: uint16


@dataclass
class SegmentRenderData:
        v1XScreen: int
        v2XScreen: int

        v1Angle: Angle = Angle(0)
        v2Angle: Angle = Angle(0)

        distanceToV1: float = 0
        distanceToNormal: float = 0
        v1ScaleFactor: float = 0
        v2ScaleFactor: float = 0
        steps: float = 0

        rightSectorCeiling: float = 0
        rightSectorFloor: float = 0
        ceilingStep: float = 0
        ceilingEnd: float = 0
        floorStep: float = 0
        floorStart: float = 0

        leftSectorCeiling: float = 0
        leftSectorFloor: float = 0

        drawUpperSection: bool = False
        drawLowerSection: bool = False

        upperHeightStep: float = 0
        upperHeight: float = 0
        lowerHeightStep: float = 0
        lowerHeight: float = 0

        updateFloor: bool = False
        updateCeiling: bool = False

        seg: Seg = None
