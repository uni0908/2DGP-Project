"""방어용 낙서가 반격을 막는 보스 패턴 검사."""

import unittest

import game_world
from boss import Boss
from bullet import Bullet
from doodle import Doodle
from eraser import Eraser


class BossTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.boss = Boss(960, 540, 80)
        game_world.add_object(self.boss, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def shoot(self, y=108):
        bullet = Bullet(120, y, 1, 'player', 960)
        bullet.update(2)

    def test_phases_repeat_and_only_attack_fires(self):
        self.boss.update(1)
        self.assertEqual(self.boss.state, 'warning')
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.boss.update(.21)
        self.assertEqual(self.boss.state, 'attack')
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 3)
        self.boss.update(4)
        self.assertEqual(self.boss.state, 'rest')
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.boss.update(4)
        self.assertEqual(self.boss.state, 'warning')

    def test_only_low_weak_point_during_rest_takes_damage(self):
        self.shoot()
        self.assertEqual(self.boss.hp, 30)
        self.boss.state = 'attack'
        self.shoot()
        self.assertEqual(self.boss.hp, 30)
        self.boss.state = 'rest'
        self.shoot(170)
        self.assertEqual(self.boss.hp, 30)
        self.shoot()
        self.assertEqual(self.boss.hp, 29)

    def test_cover_blocks_attack_and_own_shot_until_erased(self):
        cover = Doodle(250, 108)
        game_world.add_object(cover, game_world.TERRAIN)
        Bullet(700, 108, -1, 'enemy', 960).update(2)
        self.assertEqual(cover.hp, 19)
        self.boss.state = 'rest'
        self.shoot()
        self.assertEqual(self.boss.hp, 30)
        self.assertEqual(cover.hp, 18)
        eraser = Eraser(120, 108, 1, 960)
        eraser.update(.5)
        self.assertNotIn(cover, game_world.objects(game_world.TERRAIN))
        self.shoot()
        self.assertEqual(self.boss.hp, 29)

    def test_eraser_cannot_remove_or_damage_boss(self):
        self.boss.state = 'rest'
        Eraser(700, 108, 1, 960).update(.5)
        self.assertEqual(self.boss.hp, 30)
        self.assertIn(self.boss, game_world.objects(game_world.ACTORS))

    def test_defeat_cleans_hostile_bullets_and_stops_pattern(self):
        self.boss.fire_volley()
        self.boss.state = 'rest'
        self.boss.take_damage(30)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.assertNotIn(self.boss, game_world.objects(game_world.ACTORS))
        self.boss.update(20)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
