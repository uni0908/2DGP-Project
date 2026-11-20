"""고양이 로봇의 고정 배치·50발 체력·접촉과 재시작 검사."""

import unittest
from unittest.mock import patch

import game_world
import scroll_mode
from player import Player
from bullet import Bullet
from cat_robot import CatRobot


class CatRobotTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(3000, 144, 3600)
        self.robot = CatRobot(3420, self.player, 144)
        game_world.add_object(self.player, game_world.ACTORS)
        game_world.add_object(self.robot, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def test_fifty_actual_player_bullets_destroy_robot(self):
        for count in range(1, 51):
            bullet = Bullet(self.robot.x - 100, 144 + 41.5, 1, 'player', 3600)
            game_world.add_object(bullet, game_world.PROJECTILES)
            bullet.update(.2)
            self.assertFalse(bullet.active)
            self.assertEqual(self.robot.hp, 50 - count)
            self.assertEqual(self.robot in game_world.objects(game_world.ACTORS), count < 50)
        self.robot.take_damage(1)
        self.assertEqual(self.robot.hp, 0)

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
        robots[0].take_damage(50)
        scroll_mode.enter()
        robots = [obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, CatRobot)]
        self.assertEqual(len(robots), 1)
        self.assertEqual((robots[0].x, robots[0].hp), (3420, 50))
        scroll_mode.exit()
        self.assertFalse(game_world.objects(game_world.ACTORS))

    def test_draw_uses_camera_coordinates(self):
        game_world.camera_x = 2640
        with patch('pico2d.draw_rectangle') as draw:
            self.robot.draw()
        self.assertEqual(draw.call_args_list[0].args[0], 3420 - 48 - 2640 + 8)
