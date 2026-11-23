"""낙서와 플레이어의 방향별 충돌 및 생성 규칙 회귀 검사."""

import unittest
from types import SimpleNamespace

import pico2d
from core import game_world
from modes import play_mode
from items.doodle import Doodle
from actors.player import Player


class TerrainTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.platform = Doodle(300, 160)  # 윗면 176, 아랫면 144
        game_world.add_object(self.platform, game_world.TERRAIN)

    def tearDown(self):
        play_mode.exit()

    def player(self, x=300, y=108):
        player = Player(x, 80, 960)
        player.y = y
        return player

    def test_jump_through_bottom_and_land_on_top(self):
        player = self.player()
        player.jump()
        highest = player.y
        for _ in range(100):
            player.update(.01)
            highest = max(highest, player.y)
        self.assertGreater(highest - player.HEIGHT / 2, 176)
        self.assertAlmostEqual(player.y, 204)
        self.assertTrue(player.grounded)
        player.jump()
        player.update(.05)
        self.assertGreater(player.y, 204)

    def test_both_sides_block(self):
        for x, key, expected in ((200, pico2d.SDLK_RIGHT, 238),
                                  (400, pico2d.SDLK_LEFT, 362)):
            with self.subTest(key=key):
                player = self.player(x, 160)
                player.pressed_keys.add(key)
                player.update(.2)
                self.assertAlmostEqual(player.x, expected)

    def test_walking_off_platform_falls_to_floor(self):
        player = self.player(y=204)
        player.pressed_keys.add(pico2d.SDLK_RIGHT)
        player.update(.3)
        self.assertLess(player.y, 204)
        self.assertFalse(player.grounded)
        player.update(.5)
        self.assertAlmostEqual(player.y, 108)
        self.assertTrue(player.grounded)

    def test_high_speed_fall_lands_on_highest_crossed_platform(self):
        game_world.add_object(Doodle(300, 240), game_world.TERRAIN)
        player = self.player(y=400)
        player.velocity_y = -2000
        player.grounded = False
        player.update(.2)
        self.assertAlmostEqual(player.y, 284)
        self.assertTrue(player.grounded)

    def test_ascending_inside_platform_can_move_without_side_snap(self):
        player = self.player(y=160)
        player.velocity_y = 400
        player.grounded = False
        player.pressed_keys.add(pico2d.SDLK_RIGHT)
        player.update(.02)
        self.assertGreater(player.x, 300)
        self.assertLess(player.x, 310)
        self.assertGreater(player.y, 160)

    def test_move_release_and_floor_jump_regression(self):
        player = self.player(100)
        player.pressed_keys.add(pico2d.SDLK_LEFT)
        player.update(.1)
        player.clear_input()
        x = player.x
        player.update(.1)
        self.assertEqual(player.x, x)
        player.jump()
        player.update(.1)
        velocity = player.velocity_y
        player.jump()
        self.assertEqual(player.velocity_y, velocity)
        player.update(1)
        self.assertAlmostEqual(player.y, 108)

    def test_spawn_rules_and_fixed_position(self):
        play_mode.enter()
        player = play_mode.player
        first = play_mode.spawn_doodle()
        self.assertGreater(first.x, player.x)
        self.assertIsNone(play_mode.spawn_doodle())
        player.facing = -1
        self.assertLess(play_mode.spawn_doodle().x, player.x)
        player.x = 18
        self.assertIsNone(play_mode.spawn_doodle())
        player.x = 942
        player.facing = 1
        self.assertIsNone(play_mode.spawn_doodle())
        player.x, player.y = 500, 300
        air = play_mode.spawn_doodle()
        position = (air.x, air.y)
        game_world.update(.05)
        self.assertEqual((air.x, air.y), position)
        player.y = 530
        self.assertIsNone(play_mode.spawn_doodle())

    def test_spawn_key_ignores_repeat_and_focus_loss_clears_input(self):
        play_mode.enter()
        events = [SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_s),
                  SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_s),
                  SimpleNamespace(type=pico2d.SDL_WINDOWEVENT,
                                  event=pico2d.SDL_WINDOWEVENT_FOCUS_LOST)]
        from unittest.mock import patch
        with patch.object(pico2d, 'get_events', return_value=events):
            self.assertTrue(play_mode.handle_events())
        self.assertEqual(len(game_world.objects(game_world.TERRAIN)), 1)
        self.assertFalse(play_mode.player.pressed_keys)


if __name__ == '__main__':
    unittest.main()
