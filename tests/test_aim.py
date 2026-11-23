import math
import unittest

import pico2d
from core import game_world
from projectiles.bullet import Bullet
from items.doodle import Doodle
from actors.player import Player


class AimTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(300, 80, 960)
        game_world.add_object(self.player, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def test_up_requires_attack_and_preserves_facing(self):
        self.player.facing = -1
        self.player.pressed_keys.add(pico2d.SDLK_UP)
        self.player.update(.01)
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 0)
        self.player.pressed_keys.add(pico2d.SDLK_a)
        self.player.update(.01)
        shot = game_world.objects(game_world.PROJECTILES)[0]
        self.assertEqual(self.player.x, 300)
        self.assertEqual(self.player.facing, -1)
        x = shot.x
        shot.update(.1)
        self.assertEqual(shot.x, x)
        self.assertGreater(shot.y, self.player.y)
        self.player.pressed_keys.remove(pico2d.SDLK_UP)
        self.player.update(.2)
        self.assertEqual(game_world.objects(game_world.PROJECTILES)[-1].direction, -1)

    def test_diagonal_moves_and_keeps_bullet_speed(self):
        for key, sign in ((pico2d.SDLK_LEFT, -1), (pico2d.SDLK_RIGHT, 1)):
            with self.subTest(sign=sign):
                game_world.clear()
                player = Player(300, 80, 960)
                player.pressed_keys.update((pico2d.SDLK_a, pico2d.SDLK_UP, key))
                player.update(.1)
                self.assertAlmostEqual(player.x, 300 + sign * player.MOVE_SPEED * .1)
                shot = game_world.objects(game_world.PROJECTILES)[0]
                x, y = shot.x, shot.y
                shot.update(.1)
                self.assertGreater((shot.x - x) * sign, 0)
                self.assertGreater(shot.y, y)
                self.assertAlmostEqual(math.hypot(shot.x - x, shot.y - y), 65)

    def test_upward_sweep_hits_nearest_target(self):
        near, far = Doodle(300, 240), Doodle(300, 340)
        for obj in (far, near):
            game_world.add_object(obj, game_world.TERRAIN)
        shot = Bullet(300, 140, 0, 'player', 960, direction_y=1)
        shot.update(.5)
        self.assertFalse(shot.active)
        self.assertEqual(near.hp, 19)
        self.assertEqual(far.hp, 20)

    def test_diagonal_sweep_hits_target_on_path(self):
        target = Doodle(300, 300)
        game_world.add_object(target, game_world.TERRAIN)
        shot = Bullet(100, 100, 1, 'player', 960, direction_y=1)
        shot.update(.6)
        self.assertFalse(shot.active)
        self.assertEqual(target.hp, 19)

    def test_diagonal_sweep_misses_target_outside_path(self):
        target = Doodle(300, 160)
        game_world.add_object(target, game_world.TERRAIN)
        shot = Bullet(100, 100, 1, 'player', 960, direction_y=1)
        shot.update(.6)
        self.assertTrue(shot.active)
        self.assertEqual(target.hp, 20)

    def test_upward_bullet_expires_above_screen(self):
        shot = Bullet(300, 500, 0, 'player', 960, direction_y=1)
        shot.update(.2)
        self.assertFalse(shot.active)
