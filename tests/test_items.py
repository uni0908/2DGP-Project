"""수량 소비와 지우개 충돌 회귀 검사."""

import unittest

import game_world
import play_mode


class ItemTests(unittest.TestCase):
    def setUp(self):
        play_mode.enter()

    def tearDown(self):
        play_mode.exit()

    def test_doodle_consumed_only_on_valid_spawn(self):
        player = play_mode.player
        count = player.doodle_count
        self.assertIsNotNone(play_mode.spawn_doodle())
        self.assertEqual(player.doodle_count, count - 1)
        self.assertIsNone(play_mode.spawn_doodle())
        self.assertEqual(player.doodle_count, count - 1)
        player.x = 942
        self.assertIsNone(play_mode.spawn_doodle())
        self.assertEqual(player.doodle_count, count - 1)

    def test_no_doodle_spawn_at_zero(self):
        play_mode.player.doodle_count = 0
        for _ in range(3):
            self.assertIsNone(play_mode.spawn_doodle())
        self.assertEqual(play_mode.player.doodle_count, 0)
        self.assertFalse(game_world.objects(game_world.TERRAIN))
