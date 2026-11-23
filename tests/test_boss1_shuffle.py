"""일반 공격 시작·셔플 묶음·연속 중복 방지·재시작 검사."""

import random
import unittest

from core import game_world
from modes import play_mode
from actors.boss1 import Boss1
from projectiles.bullet import Bullet


class Boss1ShuffleTests(unittest.TestCase):
    def tearDown(self):
        play_mode.exit()

    def test_first_normal_and_each_bag_contains_all_four_without_repeat(self):
        expected = {'normal', 'barrage', 'homing', 'laser'}
        for seed in range(100):
            boss = Boss1(960, 540, 80, rng=random.Random(seed))
            sequence = [boss.pattern]
            for _ in range(63):
                boss.choose_next_pattern()
                sequence.append(boss.pattern)
            self.assertEqual(sequence[0], 'normal')
            self.assertTrue(all(a != b for a, b in zip(sequence, sequence[1:])))
            for i in range(0, len(sequence), 4):
                self.assertEqual(set(sequence[i:i + 4]), expected)

    def test_normal_finishes_both_cycles_before_consuming_next_pattern(self):
        boss = Boss1(960, 540, 80, rng=random.Random(3))
        queued = list(boss.pattern_queue)
        boss.state = 'normal_parry'
        boss.advance_phase()
        self.assertEqual(boss.pattern, 'normal')
        self.assertEqual(boss.pattern_queue, queued)
        boss.state = 'normal_parry'
        boss.advance_phase()
        self.assertEqual(boss.pattern, queued[0])
        self.assertEqual(boss.pattern_queue, queued[1:])

    def test_transition_resets_new_pattern_state_and_preserves_old_bullets(self):
        boss = Boss1(960, 540, 80)
        old = Bullet(300, 200, -1, 'enemy', 960)
        game_world.add_object(old, game_world.PROJECTILES)
        boss.pattern_queue = ['homing', 'laser', 'barrage']
        boss.state_time = 20
        boss.fire_timer = 3
        boss.homing_shots = 2
        boss.choose_next_pattern()
        self.assertEqual((boss.pattern, boss.state), ('homing', 'homing_launch'))
        self.assertEqual((boss.state_time, boss.fire_timer, boss.homing_shots), (0, 0, 0))
        self.assertIn(old, game_world.objects(game_world.PROJECTILES))
        self.assertTrue(old.active)

    def test_play_mode_test_flag_off_and_restart_starts_normal(self):
        self.assertFalse(play_mode.LASER_TEST_MODE)
        play_mode.enter()
        self.assertEqual(play_mode.enemy.pattern, 'normal')
        play_mode.enemy.choose_next_pattern()
        play_mode.enter()
        self.assertEqual(play_mode.enemy.pattern, 'normal')
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
