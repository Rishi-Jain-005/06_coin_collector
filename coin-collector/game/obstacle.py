"""
Obstacle: a static rectangular hazard.
"""

import pygame


class Obstacle:
    def __init__(self, x, y, width, height, color=(110, 75, 55)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
