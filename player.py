import pygame
import math
import sys

from pygame.locals import K_ESCAPE, K_w, K_s, K_e, K_r, K_d, K_a, K_SPACE
from funcs import dcos, dsin, dtan


def clamp(n, min_val, max_val):
    return max(min(n, max_val), min_val)


class Player:
    def __init__(self, player_id=None, x=None, y=None):
        self.x = x
        self.y = y
        self.id = player_id
        self.angle = 90  # angle
        self.speed = 620
        self.fov = 90
        self.rotation_speed = 0.25 * 60
        self.z = 21
        self.timer = 0
        self.half_fov = self.fov / 2
        pygame.event.set_grab(True)

    @property
    def sin(self):
        return dsin(self.angle)

    @property
    def cos(self):
        return dcos(self.angle)

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def set_angle(self, angle):
        self.angle = angle

    def move(self, dt):
        self.timer += dt
        keys = pygame.key.get_pressed()
        dx, dy = pygame.mouse.get_rel()

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
            left_side_angle = self.angle - 90
            self.x += dcos(left_side_angle) * self.speed * dt
            self.y += dsin(left_side_angle) * self.speed * dt
        if keys[K_a]:
            right_side_angle = self.angle + 90
            self.x += dcos(right_side_angle) * self.speed * dt
            self.y += dsin(right_side_angle) * self.speed * dt

        self.angle -= dx * self.rotation_speed * dt

    def angleToVertex(self, vertex):
        dx = vertex.x - self.x
        dy = vertex.y - self.y
        return math.atan2(dy, dx) * 180 / math.pi

    def distance(self, vertex):
        return math.dist(list(vertex), [self.x, self.y])

    def updateHeight(self, subsectorHeight):
        self.z = max(subsectorHeight + 41, self.z - 15)
