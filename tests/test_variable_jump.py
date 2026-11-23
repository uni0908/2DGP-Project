"""스페이스바 유지 시간에 따른 점프 높이와 착지를 검증한다."""

import unittest
from types import SimpleNamespace

import pico2d
from core import game_world
from player import Player


class VariableJumpTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()

    def simulate(self, hold_time):
        player = Player(120, 80, 960)
        player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN,
                                            key=pico2d.SDLK_SPACE))
        peak = player.y
        released = False
        for i in range(200):
            if i * .008 >= hold_time and not released:
                player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYUP,
                                                    key=pico2d.SDLK_SPACE))
                released = True
            player.update(.008)
            peak = max(peak, player.y)
        self.assertTrue(player.grounded)
        self.assertAlmostEqual(player.y, 108)
        return peak - 108

    def test_short_medium_full_jump_heights(self):
        short = self.simulate(.016)
        medium = self.simulate(.1)
        full = self.simulate(.5)
        self.assertLess(short, medium)
        self.assertLess(medium, full)
        self.assertLess(short, 25)
        self.assertGreater(full, 100)

    def test_full_jump_feet_reach_near_screen_midpoint(self):
        rise = self.simulate(1.0)
        self.assertAlmostEqual(80 + rise, 540 / 2, delta=5)

    def test_release_during_descent_does_not_add_upward_speed(self):
        player = Player(120, 80, 960)
        player.jump()
        player.update(player.JUMP_SPEED / player.GRAVITY + .05)
        velocity = player.velocity_y
        self.assertLess(velocity, 0)
        player.cut_jump()
        self.assertEqual(player.velocity_y, velocity)
