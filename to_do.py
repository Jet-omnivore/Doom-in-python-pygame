import pygame
import sys
import math

from pygame.locals import *

pygame.init()
window = pygame.display.set_mode((600, 400))
clock = pygame.time.Clock()

pos = 300, 200
fov = math.pi / 2
half_fov = fov / 2
angle = 0

pygame.mouse.set_visible(False)
color = [255, 255, 255]
font = pygame.font.SysFont('arial', 22)

def norm(angle):
    return angle % (2 * math.pi)

while 1:

    window.fill((0, 0, 0))
    mx, my = pygame.mouse.get_pos()
    pygame.draw.circle(window, (255, 0, 0), pos, 3)
    pygame.draw.circle(window, color, (mx, my), 3)
    pygame.draw.line(window, (255, 255, 0), pos, (pos[0] + math.cos(angle) * 5, pos[1] + math.sin(angle) * 5))
    pygame.draw.line(window, (255, 255, 0), pos, (pos[0] + math.cos(angle - half_fov) * 90, pos[1] + math.sin(angle - half_fov) * 90))
    pygame.draw.line(window, (255, 255, 0), pos, (pos[0] + math.cos(angle + half_fov) * 90, pos[1] + math.sin(angle + half_fov) * 90))

    dx, dy = mx - pos[0], my - pos[1]
    angle = norm(angle)
    target_angle = math.atan2(dy, dx)
    target_angle = norm(target_angle - angle)
    target_angle = norm(target_angle + half_fov)
    if target_angle < fov and (target_angle) > 0:
        color[0] = 0
    else:
        color[0] = 255

    keys = pygame.key.get_pressed()
    if keys[QUIT]:
        pygame.quit()
        sys.exit()
    if keys[K_LEFT]:
        angle -= 0.005
    if keys[K_RIGHT]:
        angle += 0.005

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    surf = font.render(f'{angle}', False, (255, 255, 255))
    window.blit(font.render(f'{angle}', False, (255, 255, 255)), (10, 10))
    window.blit(font.render(f'shut up', False, (255, 255, 255)), (10, 25))

    pygame.display.update()
    clock.tick()
