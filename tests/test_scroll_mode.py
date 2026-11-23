"""빈 횡스크롤 맵·카메라·자동 보스 진입·플레이어 상태 유지 검사."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d
from core import game_framework
from core import game_world
import scroll_mode
import play_mode
from doodle import Doodle
from bullet import Bullet
from frog_enemy import FrogEnemy
from cat_robot import CatRobot


class ScrollModeTests(unittest.TestCase):
    def setUp(self):
        game_framework.current_mode = None
        game_framework.next_mode = None
        game_framework.next_arguments = {}
        scroll_mode.enter()

    def tearDown(self):
        scroll_mode.exit()
        play_mode.exit()
        game_framework.current_mode = game_framework.next_mode = None
        game_framework.next_arguments = {}

    def event(self, key):
        return SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=key)

    def test_map_initially_contains_player_hidden_frogs_and_continuous_floor(self):
        actors = game_world.objects(game_world.ACTORS)
        self.assertIs(actors[0], scroll_mode.player)
        self.assertEqual(len(actors), 5)
        self.assertTrue(all(isinstance(obj, FrogEnemy) and obj.state == 'hidden'
                            for obj in actors[1:4]))
        self.assertIsInstance(actors[4], CatRobot)
        self.assertFalse(game_world.objects(game_world.TERRAIN))
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.assertEqual(scroll_mode.player.world_width, 3600)
        self.assertEqual(scroll_mode.player.get_bb()[1], scroll_mode.GROUND_Y)

    def test_walking_to_actual_right_boundary_requests_boss_once(self):
        # 이동·구간 전환 검사는 새 로봇의 공격과 분리한다.
        for obj in game_world.objects(game_world.ACTORS):
            if isinstance(obj, CatRobot):
                game_world.remove_object(obj)
        scroll_mode.handle_events([self.event(pico2d.SDLK_RIGHT)])
        with patch.object(game_framework, 'change_mode') as transition, \
                patch.object(scroll_mode.spawner, 'update'):
            for _ in range(300):
                scroll_mode.update(.05)
            self.assertAlmostEqual(scroll_mode.player.x, 3582)
            self.assertEqual(scroll_mode.camera.x, 2640)
            self.assertEqual(transition.call_count, 1)
            self.assertIs(transition.call_args.args[0], play_mode)

    def test_scroll_world_coordinates_and_items_cannot_be_used(self):
        scroll_mode.player.x = 1800
        scroll_mode.update(.01)
        self.assertEqual(game_world.camera_x, 1416)
        player = scroll_mode.player
        before = (player.doodle_count, player.eraser_count)
        for keys in ((pico2d.SDLK_s, pico2d.SDLK_d),
                     (pico2d.SDLK_DOWN, pico2d.SDLK_s, pico2d.SDLK_d)):
            player.clear_input()
            scroll_mode.handle_events([self.event(key) for key in keys])
            self.assertFalse(game_world.objects(game_world.TERRAIN))
            self.assertFalse(game_world.objects(game_world.PROJECTILES))
            self.assertEqual((player.doodle_count, player.eraser_count), before)

    def test_boss_transition_preserves_hp_inventory_and_clears_old_world(self):
        robot = next(obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, CatRobot))
        game_world.camera_x = 2640
        robot.take_damage(robot.MAX_HP)
        player = scroll_mode.player
        player.x, player.hp = 3582, 3
        player.doodle_count, player.eraser_count = 7, 4
        old = Doodle(1800, 108)
        game_world.add_object(old, game_world.TERRAIN)
        game_world.add_object(Bullet(1900, 108, 1, 'player', 3600), game_world.PROJECTILES)
        game_framework.current_mode = scroll_mode
        scroll_mode.update(.01)
        self.assertIs(game_framework.next_mode, play_mode)
        game_framework.apply_mode_change()
        self.assertIs(game_framework.current_mode, play_mode)
        self.assertEqual((play_mode.player.hp, play_mode.player.doodle_count, play_mode.player.eraser_count), (3, 7, 4))
        self.assertEqual(play_mode.player.x, 120)
        self.assertEqual(game_world.camera_x, 0)
        self.assertFalse(game_world.objects(game_world.TERRAIN))
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.assertEqual(play_mode.enemy.pattern, 'normal')

    def test_living_robot_blocks_only_boss_transition_at_right_edge(self):
        scroll_mode.player.x = 3582
        scroll_mode.update(.01)
        self.assertEqual(scroll_mode.player.x, 3582)
        self.assertTrue(scroll_mode.robot_is_alive())
        self.assertIsNone(game_framework.next_mode)
        self.assertFalse(scroll_mode.transition_requested)
        robot = next(obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, CatRobot))
        robot.take_damage(robot.MAX_HP)
        scroll_mode.update(.01)
        self.assertIs(game_framework.next_mode, play_mode)
        self.assertTrue(scroll_mode.transition_requested)

    def test_player_can_still_walk_through_robot_while_taking_contact_damage(self):
        robot = next(obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, CatRobot))
        scroll_mode.player.x = robot.x - 40
        scroll_mode.handle_events([self.event(pico2d.SDLK_RIGHT)])
        scroll_mode.update(.6)
        self.assertGreater(scroll_mode.player.get_bb()[0], robot.get_bb()[2])
        self.assertEqual(scroll_mode.player.hp, 4)
        self.assertEqual(robot.hp, 100)

    def test_restart_restores_robot_boss_entry_requirement(self):
        robot = next(obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, CatRobot))
        game_world.camera_x = 2640
        robot.take_damage(robot.MAX_HP)
        self.assertFalse(scroll_mode.robot_is_alive())
        scroll_mode.enter()
        scroll_mode.player.x = 3582
        scroll_mode.update(.01)
        self.assertTrue(scroll_mode.robot_is_alive())
        self.assertIsNone(game_framework.next_mode)

    def test_restart_clears_camera_and_constructed_objects(self):
        scroll_mode.player.x = 1800
        scroll_mode.update(.01)
        scroll_mode.handle_events([self.event(pico2d.SDLK_s)])
        scroll_mode.handle_events([self.event(pico2d.SDLK_r)])
        self.assertEqual(scroll_mode.player.x, scroll_mode.PLAYER_START_X)
        self.assertEqual(game_world.camera_x, 0)
        self.assertFalse(game_world.objects(game_world.TERRAIN))

    def test_focus_loss_stops_movement(self):
        scroll_mode.handle_events([self.event(pico2d.SDLK_RIGHT)])
        scroll_mode.handle_events([SimpleNamespace(type=pico2d.SDL_WINDOWEVENT,
                                                   event=pico2d.SDL_WINDOWEVENT_FOCUS_LOST)])
        x = scroll_mode.player.x
        scroll_mode.update(.1)
        self.assertEqual(scroll_mode.player.x, x)

    def test_map_layers_keep_camera_alignment_and_foreground_order(self):
        order = []
        images = []
        for name in scroll_mode.MAP_LAYERS:
            image = Mock()
            image.clip_draw.side_effect = lambda *args, layer=name: order.append(layer)
            images.append(image)
        scroll_mode.player.x = 1800
        scroll_mode.update(0)
        with patch.object(scroll_mode, 'map_images', tuple(images)), \
                patch.object(scroll_mode.health_bar, 'draw'), \
                patch.object(scroll_mode, 'font', Mock()), \
                patch.object(game_world, 'draw', side_effect=lambda: order.append('actors')), \
                patch('pico2d.clear_canvas'), patch('pico2d.draw_rectangle'), \
                patch('pico2d.update_canvas'):
            scroll_mode.draw()
        self.assertEqual(order, [*scroll_mode.MAP_LAYERS[:-1], 'actors', 'foreground.png'])
        for image in images:
            self.assertEqual(image.clip_draw.call_args.args[:4], (1416, 0, 960, 540))
