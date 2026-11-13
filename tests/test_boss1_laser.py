"""4번 레이저 패턴과 기존 공격 순서의 연결 검사."""

import unittest

import game_world
from boss1 import Boss1
from doodle import Doodle
from sweep_laser import SweepLaser


class Boss1LaserTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.boss = Boss1(960, 540, 80, shuffle_patterns=False)
        game_world.add_object(self.boss, game_world.ACTORS)
        self.boss.pattern = 'homing'
        self.boss.state = 'homing_recover'
        self.boss.advance_phase()

    def tearDown(self):
        game_world.clear()

    def test_charge_then_single_laser_and_return_after_round_trip(self):
        self.assertEqual(self.boss.pattern, 'laser')
        self.assertEqual(self.boss.attack_name, '레이저 공격')
        self.boss.update(self.boss.LASER_PHASE_DURATIONS['laser_charge'] - .01)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.boss.update(.02)
        self.assertEqual(self.boss.state, 'laser_sweep')
        shots = game_world.objects(game_world.PROJECTILES)
        self.assertEqual(len(shots), 1)
        self.assertIsInstance(shots[0], SweepLaser)
        self.boss.update(10)
        self.assertEqual(self.boss.state, 'laser_sweep')
        self.assertEqual(game_world.objects(game_world.PROJECTILES), shots)
        shots[0].update(6)
        self.boss.update(.5)
        self.assertEqual(self.boss.state, 'laser_recover')
        self.boss.update(.51)
        self.assertEqual(self.boss.pattern, 'barrage')
        self.assertEqual(self.boss.burst_shots, 1)

    def test_existing_laser_keeps_sweeping_after_boss_defeat(self):
        self.boss.update(self.boss.LASER_PHASE_DURATIONS['laser_charge'] + .01)
        laser = self.boss.laser
        platform = Doodle(250, 300)
        game_world.add_object(platform, game_world.TERRAIN)
        self.boss.take_damage(30)
        self.assertTrue(laser.active)
        laser.update(2)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.assertEqual(platform.hp, 20)

    def test_laser_only_mode_starts_and_repeats_without_other_attacks(self):
        game_world.clear()
        boss = Boss1(960, 540, 80, laser_only=True)
        for _ in range(2):
            self.assertEqual((boss.pattern, boss.state), ('laser', 'laser_charge'))
            boss.update(boss.LASER_PHASE_DURATIONS['laser_charge'] + .01)
            self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 1)
            self.assertIsInstance(boss.laser, SweepLaser)
            boss.laser.update(6)
            boss.update(1.01)
            self.assertFalse(game_world.objects(game_world.PROJECTILES))
            self.assertEqual(boss.volley_index, 0)
