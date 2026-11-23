"""유도탄의 추적·수명·충돌·패링 회귀 검사."""

import math
import unittest
from types import SimpleNamespace

import pico2d
from core import game_world
from actors.player import Player
from items.doodle import Doodle
from projectiles.homing_missile import HomingMissile, segment_box_entry


class HomingMissileTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()

    def tearDown(self):
        game_world.clear()

    def test_turns_toward_target_with_limited_turn_rate(self):
        target = SimpleNamespace(x=100, y=400, hp=5)
        missile = HomingMissile(500, 200, target, 960)
        missile.update(.2)
        self.assertLess(missile.x, 500)
        self.assertGreater(missile.y, 200)
        self.assertLessEqual(abs(missile.angle - math.pi), missile.turn_speed * .2 + 1e-8)

    def test_no_timeout_or_offscreen_removal(self):
        missile = HomingMissile(100, 300, None, 960)
        game_world.add_object(missile, game_world.PROJECTILES)
        missile.update(20)
        self.assertTrue(missile.active)
        self.assertLess(missile.x, 0)
        self.assertIn(missile, game_world.objects(game_world.PROJECTILES))

    def test_doodle_blocks_missile_before_player(self):
        player = Player(120, 80, 960)
        cover = Doodle(250, 108)
        game_world.add_object(player, game_world.ACTORS)
        game_world.add_object(cover, game_world.TERRAIN)
        missile = HomingMissile(700, 108, player, 960)
        missile.update(5)
        self.assertFalse(missile.active)
        self.assertEqual(cover.hp, 19)
        self.assertEqual(player.hp, 5)
        missile.update(1)
        self.assertEqual(cover.hp, 19)

    def test_diagonal_motion_does_not_tunnel_through_doodle(self):
        cover = Doodle(200, 200)
        game_world.add_object(cover, game_world.TERRAIN)
        missile = HomingMissile(300, 300, None, 960)
        missile.angle = -3 * math.pi / 4
        missile.speed = 2000
        missile.update(.2)
        self.assertFalse(missile.active)
        self.assertEqual(cover.hp, 19)
        self.assertIsNone(segment_box_entry(0, 0, 200, 0, (100, 100, 120, 120)))

    def test_color_missile_parry_rewards_once_and_normal_missile_hurts(self):
        for reward in ('doodle', 'eraser', None):
            with self.subTest(reward=reward):
                game_world.clear()
                player = Player(120, 80, 960)
                game_world.add_object(player, game_world.ACTORS)
                player.jump()
                player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE))
                missile = HomingMissile(155, player.y, player, 960, parry_reward=reward)
                game_world.add_object(missile, game_world.PROJECTILES)
                missile.update(.3)
                self.assertFalse(missile.active)
                self.assertEqual(player.hp, 4 if reward is None else 5)
                expected = (11, 10) if reward == 'doodle' else (10, 11) if reward else (10, 10)
                self.assertEqual((player.doodle_count, player.eraser_count), expected)
                missile.update(1)
                self.assertEqual((player.doodle_count, player.eraser_count), expected)
