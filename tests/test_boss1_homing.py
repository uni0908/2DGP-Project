"""보스1 유도탄 패턴에서 단독 패링탄과 도약 여유를 검증한다."""

import unittest
from types import SimpleNamespace

import pico2d
import game_world
from boss1 import Boss1
from player import Player
from bullet import Bullet
from homing_missile import HomingMissile


class Boss1HomingTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(120, 80, 960)
        self.boss = Boss1(960, 540, 80)
        game_world.add_object(self.player, game_world.ACTORS)
        game_world.add_object(self.boss, game_world.ACTORS)
        self.boss.pattern = 'normal'
        self.boss.state = 'normal_parry'
        self.boss.normal_cycles = 1
        self.boss.advance_phase()

    def tearDown(self):
        game_world.clear()

    def resolve(self, obj):
        obj.active = False
        game_world.remove_object(obj)

    def reach_solo_parry(self):
        self.boss.update(1.5)
        self.assertEqual(self.boss.state, 'homing_wait')
        for obj in game_world.objects(game_world.PROJECTILES):
            self.resolve(obj)
        self.boss.update(.01)
        shots = game_world.objects(game_world.PROJECTILES)
        self.assertEqual(len(shots), 1)
        return shots[0]

    def test_two_normal_missiles_then_wait_without_timeout(self):
        self.boss.update(.01)
        self.assertEqual(self.boss.homing_shots, 1)
        self.boss.update(.7)
        self.assertEqual(self.boss.homing_shots, 2)
        self.boss.update(.8)
        self.assertEqual(self.boss.state, 'homing_wait')
        shots = game_world.objects(game_world.PROJECTILES)
        self.assertEqual(len(shots), 2)
        self.assertTrue(all(isinstance(obj, HomingMissile) and obj.parry_reward is None for obj in shots))
        self.boss.update(20)
        self.assertEqual(self.boss.state, 'homing_wait')
        self.assertEqual(game_world.objects(game_world.PROJECTILES), shots)

    def test_old_bullets_also_block_solo_parry_until_resolved(self):
        self.boss.state = 'homing_wait'
        old = Bullet(500, 400, -1, 'enemy', 960)
        game_world.add_object(old, game_world.PROJECTILES)
        self.boss.update(1)
        self.assertEqual(self.boss.state, 'homing_wait')
        self.resolve(old)
        self.boss.update(.01)
        shot = game_world.objects(game_world.PROJECTILES)[0]
        self.assertIsInstance(shot, HomingMissile)
        self.assertEqual(shot.parry_reward, 'doodle')

    def test_solo_parry_and_one_second_recovery_before_next_attack(self):
        missile = self.reach_solo_parry()
        self.assertEqual(missile.parry_reward, 'doodle')
        self.player.jump()
        self.player.update(.016)
        missile.x, missile.y = self.player.x + 30, self.player.y
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE))
        self.assertFalse(missile.active)
        self.assertEqual(self.player.doodle_count, 11)
        self.assertEqual(self.player.velocity_y, self.player.JUMP_SPEED)
        self.boss.update(.5)
        self.assertEqual(self.boss.state, 'homing_recover')
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.boss.update(.49)
        self.assertEqual(self.boss.state, 'homing_recover')
        self.boss.update(.02)
        self.assertEqual(self.boss.pattern, 'barrage')
        self.assertEqual(self.boss.burst_shots, 1)

    def test_next_homing_visit_uses_cyan_and_waits_for_resolution(self):
        first = self.reach_solo_parry()
        self.resolve(first)
        self.boss.update(.01)
        self.boss.pattern = 'homing'
        self.boss.state = 'homing_wait'
        self.boss.advance_phase()
        self.boss.update(.01)
        missile = game_world.objects(game_world.PROJECTILES)[0]
        self.assertEqual(missile.parry_reward, 'eraser')
        self.boss.update(10)
        self.assertEqual(self.boss.state, 'homing_parry')
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 1)
