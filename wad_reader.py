import data_types

from bytes_reader import *
from pygame import Color, Surface
from doomdata import LUMPS, LUMPS_SIZE


TRANSPARENT_COLOR = (152, 0, 136)


# DATA_NAME: [DATA_CONSTRUCTOR_FUNC, DATA_CONSTRUCTOR_FUNC_PARAMETERS]
DATA_CONSTRUCTORS_AND_PATTERN = {
        LUMPS.THINGS: [data_types.Thing, 'INT16 INT16 UINT16 UINT16 UINT16'],
        LUMPS.LINEDEFS: [data_types.LineDef, 'UINT16 UINT16 UINT16 UINT16 UINT16 UINT16 UINT16'],
        LUMPS.VERTEXES: [data_types.Vertex, 'INT16 INT16'],
        LUMPS.SIDEDEFS: [data_types.SideDef, 'INT16 INT16 STR STR STR UINT16'],
        LUMPS.SECTORS: [data_types.Sector, 'INT16 INT16 STR STR UINT16 UINT16 UINT16'],
        LUMPS.SEGS: [data_types.Seg, 'UINT16 UINT16 UINT16 UINT16 UINT16 UINT16'],
        LUMPS.SSECTORS: [data_types.SubSector, 'UINT16 UINT16'],
        LUMPS.NODES: [data_types.Node, 'INT16 ' * 12 + 'UINT16 UINT16'],
        }


# DATA_TYPE: [CONSTRUCTOR, BYTE_SIZE]
READER_FUNCS = {
        'INT16': [read_int16, 2],
        'STR': [read_string, 8],
        'UINT16': [read_uint16, 2]
        }


class WadLoader:
    def __init__(self, path, Map):
        self.load_wad(path)
        self.map = Map

    def load_wad(self, path):
        try:
            self.file = open(path, 'rb')
            self.read_header(0)
            self.read_directories()
        except FileNotFoundError:
            raise FileNotFoundError

    def close_file(self):
        self.file.close()

    def read_header(self, offset):
        wad_type = read_string(self.file, offset, 4)
        dir_count = read_uint32(self.file, offset + 4)
        dir_offset = read_uint32(self.file, offset + 8)
        self.header = data_types.Header(wad_type, dir_count, dir_offset)

    def readIndividualLumpData(self, offset, lump):
        parameters = []
        constructor_func, parameter_pattern = DATA_CONSTRUCTORS_AND_PATTERN[lump]
        for parameter_type in parameter_pattern.split(' '):
            try:
                reader_func, byte_size = READER_FUNCS[parameter_type]
            except KeyError as ke:
                raise KeyError(ke, lump.name)
            readed_parameter = reader_func(self.file, offset)
            parameters.append(readed_parameter)
            offset += byte_size

        try:
            newObj = constructor_func(*parameters)
        except TypeError as te:
            raise TypeError(te, lump.name)
        return newObj

    def read_directories(self):
        self.directories = []
        self.dir_dict = {}
        for i in range(self.header.dir_count):
            offset = self.header.dir_offset + 16 * i
            lump_offset = read_uint32(self.file, offset)
            lump_size = read_uint32(self.file, offset + 4)
            lump_name = read_string(self.file, offset + 8)
            directory = data_types.Directory(lump_offset, lump_size, lump_name)
            self.directories.append(directory)
            self.dir_dict[lump_name] = len(self.directories) - 1

    def read_map_data(self, data):
        try:
            index = self.dir_dict[self.map.get_name()]
        except KeyError:
            raise Exception(f"{self.map.get_name} not found make sure you have specified the correct game map name")

        index += data.value  # data index
        if self.directories[index].lump_name != data.name:
            print(self.directories[index].lump_name, data.name)
            raise KeyError
        data_size = LUMPS_SIZE[data.name].value
        data_count = self.directories[index].lump_size // data_size
        for i in range(data_count):
            offset = self.directories[index].lump_offset + i * data_size
            returned_obj = self.readIndividualLumpData(offset, data)
            self.map.add_data(data.name, returned_obj)

    def read_playpal(self):
        index = self.dir_dict.get('PLAYPAL', None)
        self.playpal = []

        if index == None:
            print("Error! PLAYPAL index not found", index)
            return 
        if self.directories[index].lump_name != 'PLAYPAL':
            raise KeyError

        for i in range(14):
            pallete = []
            offset = self.directories[index].lump_offset + (i * 3 * 256)
            for _ in range(256):
                r = read_color_value(self.file, offset)
                g = read_color_value(self.file, offset + 1)
                b = read_color_value(self.file, offset + 2)
                offset += 3
                color = Color(r, g, b)
                pallete.append(color)
            self.playpal.append(pallete)

    def load_patch(self, patch_name):
        ''' this function reads patches from doom wad file, call this function only if playpal lump is readed'''

        lump_index = self.dir_dict.get(patch_name, None)

        if lump_index == None:
            print(f"Error! {patch_name} index not found", lump_index)
            return
        
        patch_lump = self.directories[lump_index]
        if patch_lump.lump_name != patch_name:
            raise KeyError

        offset = self.directories[lump_index].lump_offset
        patch_width = read_uint16(self.file, offset)
        patch_height = read_uint16(self.file, offset + 2)
        xoffset = read_int16(self.file, offset + 4)
        yoffset = read_int16(self.file, offset + 6)

        offset += 8

        patch_surf = Surface((patch_width, patch_height))
        patch_surf.fill(TRANSPARENT_COLOR)
        patch_surf.set_colorkey(TRANSPARENT_COLOR)

        isTerminatingColumn = lambda y_offset: y_offset == 0xff

        for column_index in range(patch_width):
            # reading header patch data offset index value 
            column_data_offset = read_uint32(self.file, offset + column_index * 4)
        
            
            #---------- reading patch column data ---------------#

            foffset = patch_lump.lump_offset + column_data_offset

            column_y_offset_value = read_uint8(self.file, foffset)
            foffset += 1

            while not isTerminatingColumn(column_y_offset_value):

                # column length == number of column pixels data available in this column
                column_length = read_uint8(self.file, foffset)
                # incrementing extra 1 + (1) here to ignore padding data
                foffset += 2
                
                for i in range(column_length):
                    color_index = read_uint8(self.file, foffset) 
                    foffset += 1
                    patch_surf.set_at((column_index, column_y_offset_value + i), self.playpal[0][color_index])
                #incrementing 1 to ignore post padding data
                foffset += 1

                #reading next column y offset
                column_y_offset_value = read_uint8(self.file, foffset)
                foffset += 1

        return patch_surf

    def load_textures(self, texture_name, pnames):
        lump_index = self.dir_dict.get(texture_name, None)

        if lump_index == None:
            print(f"Error! {texture_name} index not found", lump_index)
            return
        
        texture_lump = self.directories[lump_index]
        if texture_lump.lump_name != texture_name:
            raise KeyError

        texture_header = {}
        texture_header['numtextures'] = read_int32(self.file, texture_lump.lump_offset)
        textures = {}

        for i in range(texture_header['numtextures']):
            offset = read_uint32(self.file, texture_lump.lump_offset + 4 + (i * 4))
            
            # reading texture data
            foffset = texture_lump.lump_offset + offset
            texture_data_name = read_string(self.file, foffset)
            # texture_data_flags = read_int32(self.file, foffset + 8)
            texture_data_width = read_int16(self.file, foffset + 12)
            texture_data_height = read_int16(self.file, foffset + 14)
            texture_data_patchcount = read_int16(self.file, foffset + 20)

            tex_surf = Surface((texture_data_width, texture_data_height))
            tex_surf.fill(TRANSPARENT_COLOR)
            tex_surf.set_colorkey(TRANSPARENT_COLOR)
            textures[texture_data_name] = tex_surf

            foffset += 22
            for i in range(texture_data_patchcount):
                texture_patch_xoffset = read_int16(self.file, foffset)
                texture_patch_yoffset = read_int16(self.file, foffset + 2)
                texture_patch_patchindex = read_int16(self.file, foffset + 4)

                patch_name = pnames[texture_patch_patchindex]
                patch = self.load_patch(patch_name)

                tex_surf.blit(patch, (texture_patch_xoffset, texture_patch_yoffset))
                foffset += 10

        return textures


    def read_pnames(self):
        lump_index = self.dir_dict.get("PNAMES", None)

        if lump_index == None:
            print("Error! pnames index not found", lump_index)
            return
        
        patch_lump = self.directories[lump_index]
        if patch_lump.lump_name != "PNAMES":
            raise KeyError
        
        pname_numpatches = read_int32(self.file, patch_lump.lump_offset)
        pnames = []
        for i in range(pname_numpatches):
            name = read_string(self.file, patch_lump.lump_offset + 4 + (i * 8))
            if name.islower():
                name = name.upper()
            pnames.append(name)
        return pnames

    def read_map(self):
        self.read_map_data(LUMPS.VERTEXES)
        self.read_map_data(LUMPS.LINEDEFS)
        self.read_map_data(LUMPS.THINGS)
        self.read_map_data(LUMPS.NODES)
        self.read_map_data(LUMPS.SSECTORS)
        self.read_map_data(LUMPS.SEGS)
        self.read_map_data(LUMPS.SIDEDEFS)
        self.read_map_data(LUMPS.SECTORS)
        
        self.read_playpal()

    def get_uid_for_name(self, name):
        return self.dir_dict.get(name.upper(), -1)
