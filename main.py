import pygame
import sys
import constants
import time
import cProfile

from pygame.locals import QUIT
from player import Player
from wad_reader import WadLoader
from renderer import Renderer
from map import Map

class Engine:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)

        self.width, self.height = constants.WIDTH, constants.HEIGHT
        window_flags = pygame.SCALED + pygame.RESIZABLE
        self.window = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), window_flags)
        self.display = pygame.Surface((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.start_time = time.time()

        self.player = Player()
        self.game_map = Map('E1M1', self)
        self.wad_reader = WadLoader('assets/DOOM.WAD', self.game_map)
        self.renderer = Renderer(self)

        # init texture manager
        # don't add pallete to texture manager
        self.init_game()

    def init_game(self):
        self.wad_reader.read_map()
        self.renderer.TextureManager.load_textures_from_wad(self.wad_reader)
        self.wad_reader.close_file()

        self.game_map.locate_player()
        self.game_map.build_linedef()
        self.game_map.build_sidedef()
        self.game_map.build_Seg()
    
    def render(self):
        self.display.fill((53, 81, 92))
        self.renderer.init_frame()
        self.game_map.initFrame()
        self.game_map.render_bsp_nodes()
        self.renderer.show_fps()
        pygame.transform.scale(self.display, self.window.get_size(), self.window)

    def update_movement(self):
        end_time = time.time()
        self.dt = end_time - self.start_time
        self.start_time = end_time
        self.player.move(self.dt)

        subsectorHeight = self.game_map.data['SEGS'][self.game_map.playerInSubsector.firstSegId].frontSec.FloorHeight
        self.player.updateHeight(subsectorHeight)

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def update(self):
        while 1:
            self.render()
            self.event_handler()
            self.update_movement()

            pygame.display.update()
            self.clock.tick()


    def run(self):
        self.update()

e = Engine()
e.run()
# cProfile.run('e.render()')
