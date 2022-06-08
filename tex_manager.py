from pygame import Surface


class TextureManager:
    def __init__(self, renderer):
        self.pnames = []
        self.renderer = renderer
        self.wall_textures = {}

    def load_textures_from_wad(self, wad_reader):
        self.pnames = wad_reader.read_pnames()
        self.wall_textures = wad_reader.load_textures("TEXTURE1", self.pnames)

    def get_column(self, texture, column):
        texture = self.wall_textures[texture]
        x_pos = int(column) % (texture.get_width() - 1)
        rect = (x_pos, 0, 1, texture.get_height())
        target_texture_column = texture.subsurface(rect).copy()
        return target_texture_column
