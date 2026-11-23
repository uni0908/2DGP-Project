"""낙하 중 아래+S로 발판을 만들고 착지하는 동작 검사."""

import unittest

import pico2d
from core import game_world
import play_mode
from doodle import Doodle


class UnderfootTests(unittest.TestCase):
    def setUp(self):
        play_mode.enter()
        game_world.remove_object(play_mode.enemy)
        self.player = play_mode.player
        self.player.pressed_keys.add(pico2d.SDLK_DOWN)

    def tearDown(self):
        play_mode.exit()

    def test_underfoot_spawn_catches_fast_fall(self):
        player = self.player
        player.x, player.y = 400, 350
        player.grounded = False
        player.velocity_y = -1000
        before = player.doodle_count
        feet = player.get_bb()[1]
        platform = play_mode.spawn_doodle()
        self.assertIsNotNone(platform)
        self.assertEqual(platform.x, player.x)
        self.assertEqual(platform.get_bb()[3], feet - Doodle.UNDERFOOT_GAP)
        self.assertEqual(player.doodle_count, before - 1)
        player.update(.05)
        self.assertTrue(player.grounded)
        self.assertAlmostEqual(player.get_bb()[1], platform.get_bb()[3])
        self.assertEqual(player.velocity_y, 0)

    def test_ground_has_no_room_and_does_not_consume_resource(self):
        self.player.update(.01)
        self.assertTrue(self.player.crouching)
        before = self.player.doodle_count
        self.assertIsNone(play_mode.spawn_doodle())
        self.assertEqual(self.player.doodle_count, before)

    def test_existing_platform_overlap_does_not_consume_resource(self):
        self.player.x, self.player.y = 400, 300
        first = play_mode.spawn_doodle()
        self.assertIsNotNone(first)
        before = self.player.doodle_count
        self.assertIsNone(play_mode.spawn_doodle())
        self.assertEqual(self.player.doodle_count, before)

    def test_upward_spawn_stays_fixed_and_can_be_landed_on(self):
        player = self.player
        player.x, player.y = 400, 300
        player.grounded = False
        player.velocity_y = 300
        platform = play_mode.spawn_doodle()
        original_y = platform.y
        for _ in range(100):
            game_world.update(.01)
        self.assertEqual(platform.y, original_y)
        self.assertTrue(player.grounded)
        self.assertAlmostEqual(player.get_bb()[1], platform.get_bb()[3])
