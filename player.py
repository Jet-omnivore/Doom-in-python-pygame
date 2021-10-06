import pygame
import math
import sys

from pygame.locals import *
from angle import Angle
from numba import njit
from numpy import uint

def clamp(n, min_val, max_val):
    return max(min(n, max_val), min_val)

@njit(fastmath=True)
def angleToVertex(px, py, vx, vy):
    dx = vx - px
    dy = vy - py
    return (math.atan2(dy, dx) * 180 / math.pi)

class Player:
    def __init__(self, player_id=None, x=None, y=None, angle=None):
        self.x = x
        self.y = y
        self.id = player_id
        self.angle = angle
        self.speed = 650
        self.fov = Angle(90)
        self.rotation_speed = 0.6 * 60
        self.z = 41
        self.half_fov = self.fov >> 1
        pygame.event.set_grab(True)

    @property
    def sin(self):
        return self.angle.sin

    @property
    def cos(self):
        return self.angle.cos

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def set_angle(self, angle):
        self.angle = Angle(angle)

    def move(self, dt):
        keys = pygame.key.get_pressed()
        dx, dy = pygame.mouse.get_rel()

        if keys[K_ESCAPE]:
            pygame.quit()
            sys.exit()
        if keys[K_w]:
            self.x += self.cos * self.speed * dt
            self.y += self.sin * self.speed * dt
        if keys[K_s]:
            self.x -= self.cos * self.speed * dt
            self.y -= self.sin * self.speed * dt
        if keys[K_e]:
            self.z += dt * 120
        if keys[K_r]:
            self.z -= dt * 120
        if keys[K_d]:
            nangle = self.angle - 90
            self.x += nangle.cos * self.speed * dt
            self.y += nangle.sin * self.speed * dt
        if keys[K_a]:
            nangle = self.angle + 90
            self.x += nangle.cos * self.speed * dt
            self.y += nangle.sin * self.speed * dt
        self.angle -= dx * self.rotation_speed * dt

    def angle_to_vertex(self, vertex):
        return Angle(angleToVertex(self.x, self.y, vertex.x, vertex.y))

    #cliping vertexes in fov
    def clip_vertexes(self, v1, v2):
        angle1 = self.angle_to_vertex(v1)
        angle2 = self.angle_to_vertex(v2)
        rAngle, rAngle2 = angle1, angle2
        span = angle1 - angle2

        if span >= 180:
            return False, False, False, False

        angle1 -= self.angle
        angle2 -= self.angle

        if angle1 + self.half_fov > self.fov:
            if (angle1 - self.half_fov) >= span:
                return False, False, False, False
            angle1 = self.half_fov

        if (self.half_fov - angle2) > self.fov:
            angle2 = -self.half_fov
        angle1 += 90
        angle2 += 90
        return (rAngle, rAngle2, angle1, angle2)

    def distance(self, vertex):
        return math.sqrt((vertex.y - self.y) ** 2 + (vertex.x - self.x) ** 2)

    def updateHeight(self, subsectorHeight):
        self.z = max(subsectorHeight + 41, self.z - 15)
