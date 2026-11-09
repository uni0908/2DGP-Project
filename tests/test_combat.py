"""총격, 엄폐물, 체력 및 테스트 적의 회귀 검사."""

import unittest

import pico2d
import game_world
from bullet import Bullet
from doodle import Doodle
from player import Player


class CombatTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(120, 80, 960)
        game_world.add_object(self.player, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def bullet(self, x, y, direction=-1, team='enemy'):
        bullet = Bullet(x, y, direction, team, 960)
        game_world.add_object(bullet, game_world.PROJECTILES)
        return bullet

    def test_hit_once_and_game_over_health(self):
        for _ in range(5):
            bullet = self.bullet(200, 108)
            bullet.update(.5)
            hp = self.player.hp
            bullet.update(.5)
            self.assertEqual(self.player.hp, hp)
        self.assertEqual(self.player.hp, 0)
        self.player.take_damage(1)
        self.assertEqual(self.player.hp, 0)

    def test_player_fire_does_not_consume_resources_or_hit_self(self):
        resources = (self.player.doodle_count, self.player.eraser_count)
        self.player.pressed_keys.add(pico2d.SDLK_z)
        self.player.update(.01)
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 1)
        self.player.update(.01)
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 1)
        game_world.objects(game_world.PROJECTILES)[0].update(.1)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(resources, (self.player.doodle_count, self.player.eraser_count))

    def test_both_teams_blocked_by_doodle_and_destroy_it(self):
        for team, x, direction in (('enemy', 400, -1), ('player', 120, 1)):
            with self.subTest(team=team):
                doodle = Doodle(250, 108)
                game_world.add_object(doodle, game_world.TERRAIN)
                for _ in range(3):
                    bullet = self.bullet(x, 108, direction, team)
                    bullet.update(1)
                    self.assertFalse(bullet.active)
                self.assertNotIn(doodle, game_world.objects(game_world.TERRAIN))
                self.assertEqual(self.player.hp, 5)

    def test_destroyed_support_causes_fall(self):
        doodle = Doodle(300, 160)
        game_world.add_object(doodle, game_world.TERRAIN)
        self.player.x, self.player.y = 300, 204
        for _ in range(3):
            self.bullet(450, 160).update(1)
        self.player.update(.05)
        self.assertLess(self.player.y, 204)
        self.assertFalse(self.player.grounded)

    def test_closest_target_wins_and_offscreen_bullet_expires(self):
        doodle = Doodle(250, 108)
        game_world.add_object(doodle, game_world.TERRAIN)
        self.bullet(500, 108).update(2)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(doodle.hp, 2)
        bullet = self.bullet(800, 500, 1, 'player')
        bullet.update(1)
        self.assertFalse(bullet.active)
