"""수량 소비와 지우개 충돌 회귀 검사."""

import unittest

import game_world
import play_mode
from doodle import Doodle
from eraser import Eraser


class ItemTests(unittest.TestCase):
    def setUp(self):
        play_mode.enter()
        # 자원·지우개 단위 검사는 자동 사격하는 적과 분리한다.
        game_world.remove_object(play_mode.enemy)

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

    def test_eraser_consumption_and_zero(self):
        player = play_mode.player
        player.eraser_count = 1
        self.assertIsNotNone(play_mode.throw_eraser())
        self.assertIsNone(play_mode.throw_eraser())
        self.assertEqual(player.eraser_count, 0)

    def test_first_hit_in_both_directions_even_when_added_out_of_order(self):
        for direction in (1, -1):
            with self.subTest(direction=direction):
                game_world.clear()
                near = Doodle(500 + direction * 100, 200)
                far = Doodle(500 + direction * 250, 200)
                for obj in (far, near):
                    game_world.add_object(obj, game_world.TERRAIN)
                eraser = Eraser(500, 200, direction, 960)
                game_world.add_object(eraser, game_world.PROJECTILES)
                eraser.update(1)
                self.assertEqual(game_world.objects(game_world.TERRAIN), (far,))
                self.assertFalse(game_world.objects(game_world.PROJECTILES))

    def test_wrong_height_is_not_erased_and_miss_expires(self):
        platform = Doodle(300, 300)
        game_world.add_object(platform, game_world.TERRAIN)
        eraser = play_mode.throw_eraser()
        eraser.update(2)
        self.assertEqual(game_world.objects(game_world.TERRAIN), (platform,))
        self.assertFalse(game_world.objects(game_world.PROJECTILES))

    def test_erased_support_causes_fall(self):
        platform = Doodle(300, 160)
        game_world.add_object(platform, game_world.TERRAIN)
        player = play_mode.player
        player.x, player.y = 300, 204
        eraser = Eraser(100, 160, 1, 960)
        game_world.add_object(eraser, game_world.PROJECTILES)
        eraser.update(.4)
        player.update(.05)
        self.assertLess(player.y, 204)
        self.assertFalse(player.grounded)
        player.update(1)
        self.assertAlmostEqual(player.y, 108)

    def test_other_actors_and_non_doodle_terrain_are_not_damaged(self):
        class Target:
            hp = 10
            def get_bb(self):
                return (180, 90, 220, 130)
        enemy, boss = Target(), Target()
        game_world.add_object(enemy, game_world.ACTORS)
        game_world.add_object(boss, game_world.ACTORS)
        game_world.add_object(Target(), game_world.TERRAIN)
        eraser = play_mode.throw_eraser()
        eraser.update(.3)
        self.assertEqual((enemy.hp, boss.hp), (10, 10))
        self.assertIn(enemy, game_world.objects(game_world.ACTORS))
        self.assertEqual(len(game_world.objects(game_world.TERRAIN)), 1)

    def test_removing_multiple_projectiles_during_world_update_is_safe(self):
        for _ in range(3):
            play_mode.throw_eraser()
        game_world.update(2)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
