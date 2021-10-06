import struct

from data_types import *
from bytes_reader import *

lumps_name = ['THINGS', 'LINEDEFS', 'SIDEDEFS', 'VERTEXES', 'SEGS', 'SSECTORS', 'NODES', 'SECTORS', 'REJECT', 'BLOCKMAP', 'COUNT']
line_flags_name = {
                   'BLOCKING': 0,
                   'BLOCKMONSTERS': 1,
                   'TWOSIDED': 2,
                   'DONTPEGTOP': 4,
                   'DONTPEGBOTTOM': 8,
                   'SECRET': 16,
                   'SOUNDBLOCK': 32,
                   'DONTDRAW': 64,
                   'DRAW': 128
                   }
map_lump_index = {i: j + 1 for i, j in zip(lumps_name, range(len(lumps_name)))}
lump_data_size = {
        'VERTEXES': 4,
        'LINEDEFS': 14,
        'THINGS': 10,
        'SSECTORS': 4,
        'NODES': 28,
        'SEGS': 12,
        'SIDEDEFS': 30,
        'SECTORS': 26
            }

class WadLoader:
    def __init__(self, path, Map):
        self.load_wad(path)
        self.map = Map

    def load_wad(self, path):
        try:
            self.f = open(path, 'rb')
            self.read_header(self.f, 0)
            self.read_directories(self.f)
        except FileNotFoundError:
            pass

    def close_file(self):
        self.f.close()
    
    def read_header(self, f, offset):
        wad_type = read_string(f, offset, 4)
        dir_count = read_uint32(f, offset + 4)
        dir_offset = read_uint32(f, offset + 8)
        self.header = Header(wad_type, dir_count, dir_offset)

    def read_sidedef_data(self, f, offset):
        xoffset = read_int16(f, offset)
        yoffset = read_int16(f, offset + 2)
        upper_tex = read_string(f, offset + 4, 8)
        lower_tex = read_string(f, offset + 12, 8)
        middle_tex = read_string(f, offset + 20, 8)
        sector_id = read_uint16(f, offset + 28)
        return SideDef(xoffset, yoffset, upper_tex, lower_tex, middle_tex, sector_id)

    def read_directories(self, f):
        self.directories = []
        self.dir_dict = {}
        for i in range(self.header.dir_count):
            offset = self.header.dir_offset + 16 * i
            lump_offset = read_uint32(f, offset)
            lump_size = read_uint32(f, offset + 4)
            lump_name = read_string(f, offset + 8, 8)
            directory = Directory(lump_offset, lump_size, lump_name)
            self.directories.append(directory)
            self.dir_dict[lump_name] = len(self.directories) - 1

    def read_vertex_data(self, f, offset):
        x, y = read_int16(f, offset), read_int16(f, offset + 2)
        return Vertex(x, y)

    def read_sector_data(self, f , offset):
        floor_height = read_int16(f, offset)
        ceiling_height = read_int16(f, offset + 2)
        floor_texture = read_string(f, offset + 4, 8)
        ceiling_texture = read_string(f, offset + 12, 8)
        light_level = read_uint16(f, offset + 20)
        Type = read_uint16(f, offset + 22)
        tag = read_uint16(f, offset + 24)
        return Sector(floor_height, ceiling_height, floor_texture, ceiling_texture, light_level, Type, tag)

    def read_linedef_data(self, f, offset):
        startVertex = read_uint16(f, offset) 
        endVertex = read_uint16(f, offset + 2)
        flags = read_uint16(f, offset + 4)
        lineType = read_uint16(f, offset + 6)
        secTag = read_uint16(f, offset + 8)
        rightSideDef = read_uint16(f, offset + 10)
        leftSideDef = read_uint16(f, offset + 12)
        return LineDef(startVertex, endVertex, flags, lineType, secTag, rightSideDef, leftSideDef)

    def read_thing_data(self, f, offset):
        x = read_int16(f, offset)
        y = read_int16(f, offset + 2)
        angle = read_uint16(f, offset + 4)
        Type = read_uint16(f, offset + 6)
        flags = read_uint16(f, offset + 8)
        return Thing(x, y, angle, Type, flags)

    def read_node_data(self, f, offset):
        parameters = []
        for i in range(14):
            if i <= 12:
                parameter = read_int16(f, offset + 2 * i)
            else:
                #reading right and left child id
                parameter = read_uint16(f, offset + 2 * i)
            parameters.append(parameter)
        return Node(*parameters)

    def read_ssector_data(self, f, offset):
        return SubSector(*[read_uint16(f, offset + 2 * i) for i in range(2)])

    def read_seg_data(self, f, offset):
        return Seg(*[read_uint16(f, offset + 2 * i) for i in range(6)])

    def read_map_data(self, add_data_func, read_data_func, data_name):
        index = self.dir_dict.get(self.map.get_name)
        if not index:
            return False
        index += map_lump_index[data_name]
        if self.directories[index].lump_name != data_name:
            print('Failed to load:', data_name)
            return False
        data_size = lump_data_size[data_name]
        data_count = self.directories[index].lump_size // data_size
        for i in range(data_count):
            data = read_data_func(self.f, self.directories[index].lump_offset + i * data_size)
            add_data_func(data)

    def read_map(self, Map):
        self.read_map_data(Map.add_vertex, self.read_vertex_data, 'VERTEXES')
        self.read_map_data(Map.add_line, self.read_linedef_data, 'LINEDEFS')
        self.read_map_data(Map.add_thing, self.read_thing_data, 'THINGS')
        self.read_map_data(Map.add_node, self.read_node_data, 'NODES')
        self.read_map_data(Map.add_ssector, self.read_ssector_data, 'SSECTORS')
        self.read_map_data(Map.add_segs, self.read_seg_data, 'SEGS')
        self.read_map_data(Map.add_side_def, self.read_sidedef_data, 'SIDEDEFS')
        self.read_map_data(Map.add_sector, self.read_sector_data, 'SECTORS')
