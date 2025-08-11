import pygame
from random import randrange

class ColorGenerator:
    def __init__(self):
        self.last_update = pygame.time.get_ticks()
        self.update_interval = 500  # milliseconds (2 seconds)
        self.current_color = self._generate_colors()

    def _generate_colors(self):
        r, g, b = randrange(0, 255), randrange(0, 255), randrange(0, 255)
        return r, g, b

    def update_color(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.update_interval:
            self.current_color = self._generate_colors()
            self.last_update = now

    def get_color(self):
        return self.current_color
