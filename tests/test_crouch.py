"""웅크리기의 발 위치, 천장 여유와 실제 탄환 판정 검사."""

import unittest
from types import SimpleNamespace

import pico2d
from core import game_world
from actors.player import Player
from items.doodle import Doodle
from projectiles.bullet import Bullet


class CrouchTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(120, 80, 960)
        game_world.add_object(self.player, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def down(self):
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN,
                                                 key=pico2d.SDLK_DOWN))

    def test_feet_stay_on_floor_and_release_stands(self):
        self.down()
        self.assertEqual(self.player.get_bb(), (102, 80, 138, 108))
        self.player.update(.1)
        self.player.clear_input()
        self.player.update(.01)
        self.assertFalse(self.player.crouching)
        self.assertEqual(self.player.get_bb(), (102, 80, 138, 136))

    def test_overhead_bullet_misses_crouching_body(self):
        self.down()
        bullet = Bullet(200, 125, -1, 'enemy', 960)
        bullet.update(.4)
        self.assertEqual(self.player.hp, 5)
        low = Bullet(200, 95, -1, 'enemy', 960)
        low.update(.4)
        self.assertEqual(self.player.hp, 4)

    def test_cannot_stand_under_doodle_then_stands_after_leaving(self):
        self.down()
        game_world.add_object(Doodle(120, 128), game_world.TERRAIN)
        self.player.clear_input()
        self.player.update(.01)
        self.assertTrue(self.player.crouching)
        self.player.pressed_keys.add(pico2d.SDLK_RIGHT)
        self.player.update(1)
        self.player.update(.01)
        self.assertFalse(self.player.crouching)
        self.assertEqual(self.player.get_bb()[1], 80)

    def test_crouch_moves_slower_and_blocks_jump(self):
        self.down()
        self.player.jump()
        self.assertTrue(self.player.grounded)
        self.player.pressed_keys.add(pico2d.SDLK_RIGHT)
        self.player.update(.1)
        self.assertAlmostEqual(self.player.x, 133)

    def test_air_down_does_not_change_shape_until_landing(self):
        self.player.jump()
        self.down()
        self.assertFalse(self.player.crouching)
        self.player.update(1)
        self.player.update(.01)
        self.assertTrue(self.player.crouching)
        self.assertEqual(self.player.get_bb()[1], 80)
