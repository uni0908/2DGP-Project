"""빈 횡스크롤 맵·카메라·자동 보스 진입·플레이어 상태 유지 검사."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pico2d
import game_framework
import game_world
import scroll_mode
import play_mode
from doodle import Doodle
from bullet import Bullet


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

    def test_map_initially_contains_only_player_and_continuous_floor(self):
        self.assertEqual(game_world.objects(game_world.ACTORS), (scroll_mode.player,))
        self.assertFalse(game_world.objects(game_world.TERRAIN))
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        self.assertEqual(scroll_mode.player.world_width, 3600)
        self.assertEqual(scroll_mode.player.get_bb()[1], scroll_mode.GROUND_Y)

    def test_walking_to_actual_right_boundary_requests_boss_once(self):
        scroll_mode.handle_events([self.event(pico2d.SDLK_RIGHT)])
        with patch.object(game_framework, 'change_mode') as transition:
            for _ in range(300):
                scroll_mode.update(.05)
            self.assertAlmostEqual(scroll_mode.player.x, 3582)
            self.assertEqual(scroll_mode.camera.x, 2640)
            self.assertEqual(transition.call_count, 1)
            self.assertIs(transition.call_args.args[0], play_mode)

    def test_scroll_world_coordinates_and_doodle_creation(self):
        scroll_mode.player.x = 1800
        scroll_mode.update(.01)
        self.assertEqual(game_world.camera_x, 1416)
        scroll_mode.handle_events([self.event(pico2d.SDLK_s)])
        platform = game_world.objects(game_world.TERRAIN)[0]
        self.assertIsInstance(platform, Doodle)
        self.assertEqual(platform.x, 1874)
        self.assertEqual(game_world.screen_x(platform.x), 458)

    def test_boss_transition_preserves_hp_inventory_and_clears_old_world(self):
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
                patch.object(scroll_mode, 'font', Mock()), \
                patch.object(game_world, 'draw', side_effect=lambda: order.append('actors')), \
                patch('pico2d.clear_canvas'), patch('pico2d.draw_rectangle'), \
                patch('pico2d.update_canvas'):
            scroll_mode.draw()
        self.assertEqual(order, [*scroll_mode.MAP_LAYERS[:-1], 'actors', 'foreground.png'])
        for image in images:
            self.assertEqual(image.clip_draw.call_args.args[:4], (1416, 0, 960, 540))
