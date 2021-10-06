import pygame
import sys
import time
import cProfile
import numpy as np

from pygame.locals import *
from player import Player
from wad_reader import WadLoader
from renderer import Renderer
from map import Map

class Engine:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)

        self.width, self.height = 320, 200
        self.window = pygame.display.set_mode((640, 400))
        self.display = pygame.Surface((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.start_time = time.time()

        self.player = Player()
        self.game_map = Map('E1M1', self)
        self.wad_reader = WadLoader('assests/DOOM.WAD', self.game_map)
        self.read_map()
        self.renderer = Renderer(self)

    def remap_x(self, x):
        return (x - self.game_map.min_x) / 15

    def remap_y(self, y):
        return self.height - (y - self.game_map.min_y) / 15

    def read_map(self):
        self.wad_reader.read_map(self.game_map)
        self.game_map.locate_player()
        self.wad_reader.close_file()
        self.game_map.build_linedef()
        self.game_map.build_sidedef()
        self.game_map.build_Seg()
        del self.wad_reader

    def render(self):
        self.display.fill((0, 0, 0))
        self.renderer.init_frame()
        self.game_map.initFrame()
        self.renderer.render()
        self.renderer.show_fps()
        self.window.blit(pygame.transform.scale(self.display, self.window.get_size()), (0, 0))

    def update_movement(self):
        end_time = time.time()
        self.dt = end_time - self.start_time
        self.start_time = end_time
        self.player.move(self.dt)
        subsectorHeight = self.game_map.segs[self.game_map.playerInSubsector.firstSegId].rightSec.FloorHeight
        self.player.updateHeight(subsectorHeight)

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

    def update(self):
        while 1:
            self.render()
            self.update_movement()
            self.event_handler()

            pygame.display.update()
            self.clock.tick()

    def run(self):
        self.update()

e = Engine().run()
cProfile.run('e.render()')
