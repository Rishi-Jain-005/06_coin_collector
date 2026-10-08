"""
GameEngine: owns the player and all coins.
"""

import random
import time
import math
import pygame

from game.player import Player
from game.coin import COIN_TYPES, Coin, CoinType
from game.collection import check_collection
from game.obstacle import Obstacle
from game.renderer import WIDTH, HEIGHT

NUM_COINS = 6
INITIAL_LIVES = 3
ROUND_DURATION_SECONDS = 30
PLAYER_START_POSITION = (WIDTH / 2, HEIGHT / 2)


class GameEngine:
    def __init__(self, clock=time.monotonic):
        self.player = Player(*PLAYER_START_POSITION)
        self._clock = clock
        self.start_new_round()

    def _new_obstacles(self):
        return [
            Obstacle(120, 100, 140, 35),
            Obstacle(420, 130, 40, 130),
            Obstacle(250, 360, 160, 35),
        ]

    def start_new_round(self):
        self.player.x, self.player.y = PLAYER_START_POSITION
        self.obstacles = self._new_obstacles()
        self.coins = self._new_coins()
        self.score = 0
        self.lives = INITIAL_LIVES
        self.active = True
        self.end_reason = None
        self.remaining_time = float(ROUND_DURATION_SECONDS)
        self.round_started_at = self._clock()

    def _update_timer(self, current_time):
        if not self.active:
            return
        elapsed = current_time - self.round_started_at
        self.remaining_time = max(0.0, ROUND_DURATION_SECONDS - elapsed)
        if self.remaining_time == 0:
            self._end_round("TIME UP")

    def _new_coins(self):
        coin_types = list(COIN_TYPES[:NUM_COINS])
        coin_types.extend(
            random.choice(COIN_TYPES)
            for _ in range(NUM_COINS - len(coin_types))
        )
        random.shuffle(coin_types)
        return [self._random_coin(coin_type) for coin_type in coin_types]

    def _random_coin(self, coin_type=CoinType.BRONZE):
        while True:
            x = random.randint(30, WIDTH - 30)
            y = random.randint(30, HEIGHT - 30)
            coin = Coin(x=x, y=y, radius=12, coin_type=coin_type)
            if (
                not self.player.get_rect().colliderect(coin.get_rect())
                and not any(
                    obstacle.get_rect().colliderect(coin.get_rect())
                    for obstacle in self.obstacles
                )
            ):
                return coin

    def handle_input(self, keys_pressed):
        self._update_timer(self._clock())
        if not self.active:
            return
        dx = dy = 0
        if keys_pressed[pygame.K_UP]:
            dy -= self.player.speed
        if keys_pressed[pygame.K_DOWN]:
            dy += self.player.speed
        if keys_pressed[pygame.K_LEFT]:
            dx -= self.player.speed
        if keys_pressed[pygame.K_RIGHT]:
            dx += self.player.speed
        self.player.move(dx, dy, WIDTH, HEIGHT)

    def handle_event(self, event):
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_r
            and not self.active
        ):
            self.start_new_round()

    def update(self):
        self._update_timer(self._clock())
        if not self.active:
            return
        if any(
            self.player.get_rect().colliderect(obstacle.get_rect())
            for obstacle in self.obstacles
        ):
            self.lives = max(0, self.lives - 1)
            self.player.x, self.player.y = PLAYER_START_POSITION
            if self.lives == 0:
                self._end_round("GAME OVER")
            return

        collected = check_collection(self.player, self.coins)
        for coin in collected:
            self.score += coin.value

    def _end_round(self, reason):
        self.active = False
        self.end_reason = reason

    def draw(self, surface, font):
        from game import renderer
        renderer.draw_scene(surface, self.player, self.coins, self.obstacles)
        renderer.draw_text(surface, font, f"Score: {self.score}", (10, 10))
        renderer.draw_text(surface, font, f"Lives: {self.lives}", (10, 38))
        timer_display = math.ceil(self.remaining_time)
        renderer.draw_text(surface, font, f"TIME: {timer_display}", (10, 66))
        if not self.active:
            renderer.draw_end_screen(
                surface, font, self.end_reason, self.score
            )
