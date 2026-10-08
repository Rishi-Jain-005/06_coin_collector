import unittest
from unittest.mock import patch

import pygame

from game.coin import COIN_TYPES, Coin, CoinType
from game.game_engine import (
    INITIAL_LIVES,
    ROUND_DURATION_SECONDS,
    GameEngine,
    PLAYER_START_POSITION,
)
from game.renderer import HEIGHT, WIDTH, draw_scene


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class CoinCollectionTests(unittest.TestCase):
    EXPECTED_VALUES = {
        CoinType.BRONZE: 1,
        CoinType.SILVER: 3,
        CoinType.GOLD: 5,
    }

    def make_engine_with_coin(self, coin_type):
        engine = GameEngine()
        engine.coins = [Coin(100, 100, coin_type=coin_type)]
        engine.player.x = engine.player.y = 100
        return engine

    def test_each_coin_type_awards_its_value_once(self):
        for coin_type in COIN_TYPES:
            with self.subTest(coin_type=coin_type):
                engine = self.make_engine_with_coin(coin_type)
                for _ in range(300):
                    engine.update()
                self.assertEqual(engine.score, self.EXPECTED_VALUES[coin_type])

    def test_coin_type_colors_are_distinct(self):
        colors = {Coin(0, 0, coin_type=coin_type).color for coin_type in COIN_TYPES}
        self.assertEqual(len(colors), 3)

    def test_coin_types_coexist_in_a_new_round(self):
        engine = GameEngine()
        self.assertEqual(
            {coin.coin_type for coin in engine.coins},
            set(COIN_TYPES),
        )

    def test_collected_coin_is_inactive_and_not_rendered(self):
        engine = self.make_engine_with_coin(CoinType.BRONZE)
        coin = engine.coins[0]
        engine.update()
        engine.update()
        self.assertTrue(coin.collected)
        self.assertEqual(engine.score, 1)

        drawn_coins = []
        surface = pygame.Surface((WIDTH, HEIGHT))
        with patch(
            "pygame.draw.circle",
            side_effect=lambda _surface, color, pos, radius: drawn_coins.append(
                (color, pos, radius)
            ),
        ):
            draw_scene(surface, engine.player, [coin])
        self.assertEqual(drawn_coins, [])


class ObstacleTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine()
        self.engine.coins = []
        self.obstacle = self.engine.obstacles[0]

    def test_lives_do_not_change_without_collision(self):
        self.engine.player.x, self.engine.player.y = PLAYER_START_POSITION
        self.engine.update()
        self.assertEqual(self.engine.lives, INITIAL_LIVES)

    def test_collision_deducts_one_life_and_repositions_player(self):
        rect = self.obstacle.get_rect()
        self.engine.player.x = rect.centerx
        self.engine.player.y = rect.centery
        self.engine.update()
        self.assertEqual(self.engine.lives, INITIAL_LIVES - 1)
        self.assertEqual((self.engine.player.x, self.engine.player.y), PLAYER_START_POSITION)

        for _ in range(10):
            self.engine.update()
        self.assertEqual(self.engine.lives, INITIAL_LIVES - 1)

    def test_lives_never_become_negative_and_zero_ends_round(self):
        rect = self.obstacle.get_rect()
        self.engine.lives = 1
        self.engine.score = 9
        self.engine.player.x = rect.centerx
        self.engine.player.y = rect.centery
        self.engine.update()
        self.engine.update()
        self.assertEqual(self.engine.lives, 0)
        self.assertFalse(self.engine.active)
        self.assertEqual(self.engine.score, 9)

    def test_starting_new_round_resets_lives_and_score(self):
        self.engine.lives = 1
        self.engine.score = 12
        self.engine.active = False
        self.engine.start_new_round()
        self.assertEqual(self.engine.lives, INITIAL_LIVES)
        self.assertEqual(self.engine.score, 0)
        self.assertTrue(self.engine.active)

    def test_obstacles_and_spawned_coins_stay_clear_of_boundaries_and_each_other(self):
        for obstacle in self.engine.obstacles:
            rect = obstacle.get_rect()
            self.assertGreaterEqual(rect.left, 0)
            self.assertGreaterEqual(rect.top, 0)
            self.assertLessEqual(rect.right, WIDTH)
            self.assertLessEqual(rect.bottom, HEIGHT)
        self.assertFalse(
            any(
                self.engine.player.get_rect().colliderect(obstacle.get_rect())
                for obstacle in self.engine.obstacles
            )
        )
        for coin in self.engine.coins:
            self.assertFalse(
                any(
                    coin.get_rect().colliderect(obstacle.get_rect())
                    for obstacle in self.engine.obstacles
                )
            )


class TimedRoundTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.engine = GameEngine(clock=self.clock)

    def test_new_round_starts_with_full_state(self):
        self.assertEqual(self.engine.remaining_time, ROUND_DURATION_SECONDS)
        self.assertEqual(self.engine.lives, INITIAL_LIVES)
        self.assertEqual(self.engine.score, 0)
        self.assertTrue(self.engine.active)

    def test_timer_uses_elapsed_time_not_update_count(self):
        for _ in range(120):
            self.engine.update()
        self.assertEqual(self.engine.remaining_time, ROUND_DURATION_SECONDS)
        self.clock.now = 4.25
        self.engine.update()
        self.assertEqual(self.engine.remaining_time, 25.75)

    def test_timeout_ends_round_at_zero_without_collecting_overlapping_coin(self):
        coin = Coin(100, 100, coin_type=CoinType.GOLD)
        self.engine.coins = [coin]
        self.engine.player.x = self.engine.player.y = 100
        self.clock.now = ROUND_DURATION_SECONDS
        self.engine.update()
        self.assertFalse(self.engine.active)
        self.assertEqual(self.engine.end_reason, "TIME UP")
        self.assertEqual(self.engine.remaining_time, 0)
        self.assertFalse(coin.collected)
        self.assertEqual(self.engine.score, 0)

    def test_timer_is_clamped_at_zero(self):
        self.clock.now = ROUND_DURATION_SECONDS + 100
        self.engine.update()
        self.assertEqual(self.engine.remaining_time, 0)

    def test_game_over_freezes_score_lives_and_coin_collection(self):
        obstacle_rect = self.engine.obstacles[0].get_rect()
        self.engine.player.x = obstacle_rect.centerx
        self.engine.player.y = obstacle_rect.centery
        self.engine.lives = 1
        self.engine.score = 17
        self.engine.update()
        self.engine.coins = [Coin(100, 100, coin_type=CoinType.GOLD)]
        self.engine.player.x = self.engine.player.y = 100

        keys_pressed = {
            key: key == pygame.K_RIGHT
            for key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
        }
        self.engine.handle_input(keys_pressed)
        self.clock.now = ROUND_DURATION_SECONDS + 10
        self.engine.update()
        self.assertEqual(self.engine.end_reason, "GAME OVER")
        self.assertEqual(self.engine.score, 17)
        self.assertEqual(self.engine.lives, 0)
        self.assertFalse(self.engine.coins[0].collected)

    def test_restart_resets_round_state_and_regenerates_objects(self):
        self.engine.score = 11
        self.engine.lives = 1
        self.clock.now = 9
        obstacle_rect = self.engine.obstacles[0].get_rect()
        self.engine.player.x = obstacle_rect.centerx
        self.engine.player.y = obstacle_rect.centery
        self.engine.update()
        self.assertFalse(self.engine.active)
        old_coins = self.engine.coins
        old_obstacles = self.engine.obstacles
        self.engine.player.x = 75
        self.engine.player.y = 80
        self.engine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))

        self.assertEqual(self.engine.score, 0)
        self.assertEqual(self.engine.lives, INITIAL_LIVES)
        self.assertEqual(self.engine.remaining_time, ROUND_DURATION_SECONDS)
        self.assertTrue(self.engine.active)
        self.assertIsNone(self.engine.end_reason)
        self.assertEqual((self.engine.player.x, self.engine.player.y), PLAYER_START_POSITION)
        self.assertIsNot(self.engine.coins, old_coins)
        self.assertIsNot(self.engine.obstacles, old_obstacles)
        self.assertTrue(all(not coin.collected for coin in self.engine.coins))

    def test_restart_after_time_up_and_game_over(self):
        for end_reason in ("TIME UP", "GAME OVER"):
            with self.subTest(end_reason=end_reason):
                if end_reason == "TIME UP":
                    self.clock.now = ROUND_DURATION_SECONDS
                    self.engine.update()
                else:
                    self.engine.lives = 1
                    rect = self.engine.obstacles[0].get_rect()
                    self.engine.player.x, self.engine.player.y = rect.center
                    self.engine.update()
                self.assertEqual(self.engine.end_reason, end_reason)
                self.engine.handle_event(
                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
                )
                self.assertTrue(self.engine.active)
                self.assertEqual(self.engine.lives, INITIAL_LIVES)
                self.assertEqual(self.engine.score, 0)
                self.assertEqual(self.engine.remaining_time, ROUND_DURATION_SECONDS)


if __name__ == "__main__":
    unittest.main()
