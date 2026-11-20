"""고양이 로봇의 고정 배치·화면 내 100발 체력·폭탄 검사."""

import unittest
from unittest.mock import patch

import game_world
import scroll_mode
from player import Player
from bullet import Bullet
from cat_robot import CatRobot
from enemy_bomb import ArcBomb, BombExplosion


class CatRobotTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(3000, 144, 3600)
        self.robot = CatRobot(3420, self.player, 144)
        game_world.add_object(self.player, game_world.ACTORS)
        game_world.add_object(self.robot, game_world.ACTORS)
        game_world.camera_x = 2640

    def tearDown(self):
        game_world.clear()

    def test_hundred_actual_player_bullets_destroy_visible_robot(self):
        for count in range(1, 101):
            bullet = Bullet(self.robot.x - 100, 144 + 41.5, 1, 'player', 3600)
            game_world.add_object(bullet, game_world.PROJECTILES)
            bullet.update(.2)
            self.assertFalse(bullet.active)
            self.assertEqual(self.robot.hp, 100 - count)
            self.assertEqual(self.robot in game_world.objects(game_world.ACTORS), count < 100)
        self.robot.take_damage(1)
        self.assertEqual(self.robot.hp, 0)

    def test_offscreen_bullets_pass_without_damage_then_visible_hits_count(self):
        game_world.camera_x = 0
        for _ in range(5):
            bullet = Bullet(self.robot.x - 100, 185.5, 1, 'player', 3600)
            bullet.update(.2)
            self.assertTrue(bullet.active)
        self.robot.take_damage(100)
        self.assertEqual(self.robot.hp, 100)
        game_world.camera_x = 2640
        bullet = Bullet(self.robot.x - 100, 185.5, 1, 'player', 3600)
        bullet.update(.2)
        self.assertFalse(bullet.active)
        self.assertEqual(self.robot.hp, 99)
        game_world.camera_x = 0
        self.robot.take_damage(1)
        self.assertEqual(self.robot.hp, 99)

    def test_visibility_requires_body_overlap_with_current_view(self):
        left, _, right, _ = self.robot.get_bb()
        game_world.camera_x = left - 960
        self.assertFalse(self.robot.bullet_vulnerable)
        game_world.camera_x += 1
        self.assertTrue(self.robot.bullet_vulnerable)
        game_world.camera_x = right
        self.assertFalse(self.robot.bullet_vulnerable)

    def test_stays_still_and_body_contact_respects_invincibility(self):
        self.player.x = self.robot.x
        for _ in range(2):
            game_world.update(.01)
        self.assertEqual(self.robot.x, 3420)
        self.assertEqual(self.robot.get_bb()[1], 144)
        self.assertEqual(self.player.hp, 4)

    def test_only_one_robot_is_reset_on_restart_and_cleared_on_exit(self):
        scroll_mode.enter()
        robots = [obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, CatRobot)]
        self.assertEqual(len(robots), 1)
        game_world.camera_x = 2640
        robots[0].take_damage(100)
        scroll_mode.enter()
        robots = [obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, CatRobot)]
        self.assertEqual(len(robots), 1)
        self.assertEqual((robots[0].x, robots[0].hp), (3420, 100))
        self.assertFalse(robots[0].bullet_vulnerable)
        scroll_mode.exit()
        self.assertFalse(game_world.objects(game_world.ACTORS))

    def test_draw_uses_camera_coordinates(self):
        game_world.camera_x = 2640
        with patch('pico2d.draw_rectangle') as draw:
            self.robot.draw()
        self.assertEqual(draw.call_args_list[0].args[0], 3420 - 48 - 2640 + 8)

    def test_distance_activation_first_shot_and_interval(self):
        self.player.x = 2000
        self.robot.update(10)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.player.x = 3000
        self.robot.update(.79)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.robot.update(.02)
        bombs = game_world.objects(game_world.PROJECTILES)
        self.assertEqual(len(bombs), 1)
        self.assertIsInstance(bombs[0], ArcBomb)
        self.robot.update(2.4)
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 2)

    def test_destruction_stops_new_shots_but_existing_bombs_remain(self):
        self.robot.update(.81)
        bomb = game_world.objects(game_world.PROJECTILES)[0]
        self.robot.take_damage(100)
        self.robot.update(10)
        self.assertEqual(game_world.objects(game_world.PROJECTILES), (bomb,))

    def test_death_prevents_new_shots_and_restart_clears_bombs(self):
        self.player.hp = 0
        self.robot.update(10)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        scroll_mode.enter()
        scroll_mode.player.x = 3000
        robot = next(obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, CatRobot))
        robot.update(.81)
        self.assertTrue(game_world.objects(game_world.PROJECTILES))
        scroll_mode.enter()
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.assertFalse(game_world.objects(game_world.EFFECTS))
        scroll_mode.exit()


class BombTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(2500, 144, 3600)
        game_world.add_object(self.player, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def test_bomb_rises_and_lands_at_locked_target_in_both_directions(self):
        for target in (3000, 3550):
            with self.subTest(target=target):
                bomb = ArcBomb(3358, 224, target, self.player, 144)
                game_world.add_object(bomb, game_world.PROJECTILES)
                bomb.update(.3)
                self.assertGreater(bomb.y, 224)
                self.player.x = 2400  # 발사 후 플레이어 이동을 추적하지 않는다.
                bomb.update(1.1)
                self.assertFalse(bomb.active)
                self.assertAlmostEqual(bomb.x, target)
                self.assertAlmostEqual(bomb.y, 154)
                self.assertEqual(bomb.target_x, target)

    def test_flying_bomb_contact_explodes_once(self):
        bomb = ArcBomb(3358, 224, 3000, self.player, 144)
        game_world.add_object(bomb, game_world.PROJECTILES)
        bomb.update(.3)
        self.player.x, self.player.y = bomb.x, bomb.y
        bomb.update(.01)
        self.assertFalse(bomb.active)
        self.assertEqual(len(game_world.objects(game_world.EFFECTS)), 1)
        bomb.update(1)
        bomb.explode()
        self.assertEqual(len(game_world.objects(game_world.EFFECTS)), 1)
        game_world.objects(game_world.EFFECTS)[0].update(.01)
        self.assertEqual(self.player.hp, 4)

    def test_explosion_damage_shared_invincibility_and_removal(self):
        explosion = BombExplosion(self.player.x, 154, self.player)
        game_world.add_object(explosion, game_world.EFFECTS)
        explosion.update(.01)
        self.assertEqual(self.player.hp, 4)
        explosion.update(.01)
        self.assertEqual(self.player.hp, 4)
        explosion.update(.3)
        self.assertNotIn(explosion, game_world.objects(game_world.EFFECTS))
        self.player.invincibility_timer = 0
        explosion.update(1)
        self.assertEqual(self.player.hp, 4)

    def test_move_or_jump_outside_blast_avoids_damage(self):
        explosion = BombExplosion(3000, 154, self.player)
        self.player.x = 3100
        explosion.update(.01)
        self.assertEqual(self.player.hp, 5)
        self.player.x, self.player.y = 3000, 144 + 80 + 28
        explosion.update(.01)
        self.assertEqual(self.player.hp, 5)

    def test_target_marker_tracks_camera_but_not_player(self):
        bomb = ArcBomb(3358, 224, 3000, self.player, 144)
        game_world.camera_x = 2640
        with patch('pico2d.draw_rectangle') as draw:
            bomb.draw()
        self.assertEqual(draw.call_args_list[0].args[:4], (304, 145, 416, 148))
