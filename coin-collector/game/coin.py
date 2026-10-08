"""
Coin: a static collectible circle. Drawn as a circle, hit-tested as a
bounding square around it.
"""

import pygame
from enum import Enum


class CoinType(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


COIN_PROPERTIES = {
    CoinType.BRONZE: (1, (176, 112, 55)),
    CoinType.SILVER: (3, (192, 192, 192)),
    CoinType.GOLD: (5, (255, 215, 0)),
}
COIN_TYPES = tuple(COIN_PROPERTIES)


class Coin:
    def __init__(self, x, y, radius=12, coin_type=CoinType.BRONZE):
        self.x = x
        self.y = y
        self.radius = radius
        self.coin_type = coin_type
        self.value, self.color = COIN_PROPERTIES[coin_type]
        self.collected = False

    def get_rect(self):
        return pygame.Rect(
            int(self.x - self.radius), int(self.y - self.radius),
            self.radius * 2, self.radius * 2,
        )
