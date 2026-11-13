"""보스1 일반 공격의 이동·연사·단독 패링탄·패턴 전환 검사."""

import unittest

import game_world
from boss1 import Boss1
from bullet import Bullet


class Boss1NormalTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.boss = Boss1(960, 540, 80)
        game_world.add_object(self.boss, game_world.ACTORS)
        self.boss.state = 'rest'
        self.boss.advance_phase()

    def tearDown(self):
        game_world.clear()

    def test_names_and_vertical_movement_without_horizontal_drift(self):
        self.assertEqual(self.boss.NAME, '보스1')
        self.assertEqual(self.boss.attack_name, '일반 공격')
        heights = []
        for _ in range(700):
            self.boss.update(.01)
            heights.append(self.boss.y)
            self.assertEqual(self.boss.x, 864)
            self.assertGreaterEqual(self.boss.y, self.boss.min_y)
            self.assertLessEqual(self.boss.y, self.boss.max_y)
        self.assertGreater(max(heights) - min(heights), 200)

    def test_three_shots_then_single_color_bullet_and_recovery_gap(self):
        emissions = []
        known = set()
        for step in range(780):
            self.boss.update(.01)
            for obj in game_world.objects(game_world.PROJECTILES):
                if obj not in known:
                    emissions.append((step * .01, obj))
                    known.add(obj)
        self.assertEqual([obj.parry_reward for _, obj in emissions],
                         [None, None, None, 'doodle', None, None, None, 'eraser'])
        self.assertGreaterEqual(emissions[4][0] - emissions[3][0], 2.49)
        self.assertGreaterEqual(emissions[3][0] - emissions[2][0], 1.0)
        for _, obj in emissions:
            self.assertEqual(obj.direction, -1)
            if obj.parry_reward:
                self.assertGreaterEqual(obj.y, 170)
                self.assertLessEqual(obj.y, 210)

    def test_returns_to_barrage_and_keeps_existing_bullets(self):
        old = Bullet(500, 100, -1, 'enemy', 960)
        game_world.add_object(old, game_world.PROJECTILES)
        duration = sum(self.boss.NORMAL_PHASE_DURATIONS.values()) * self.boss.NORMAL_CYCLES
        self.boss.update(duration + .02)
        self.assertEqual(self.boss.attack_name, '탄막 공격')
        self.assertEqual(self.boss.state, 'attack')
        self.assertEqual(self.boss.burst_shots, 1)
        self.assertIn(old, game_world.objects(game_world.PROJECTILES))
        self.assertTrue(old.active)

    def test_moving_body_hitbox_matches_visible_position(self):
        self.boss.update(.5)
        left, bottom, right, top = self.boss.get_bb()
        self.assertEqual((bottom + top) / 2, self.boss.y)
        shot = Bullet(left - 50, self.boss.y, 1, 'player', 960)
        shot.update(.2)
        self.assertEqual(self.boss.hp, 29)
