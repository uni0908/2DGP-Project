"""장면 전환 순서·종료 정리와 카메라 경계를 검증한다."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pico2d
import game_framework
from camera import Camera


class FrameworkTests(unittest.TestCase):
    def mode(self, name, log, stop=False):
        return SimpleNamespace(
            enter=lambda: log.append((name, 'enter')),
            exit=lambda: log.append((name, 'exit')),
            handle_events=lambda events: False if stop else log.append((name, 'input')),
            update=lambda dt: log.append((name, 'update')),
            draw=lambda: log.append((name, 'draw')))

    def test_switch_exits_old_before_entering_new_and_cleans_up_on_quit(self):
        log = []
        first, second = self.mode('first', log), self.mode('second', log)
        events = [[], [SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_F2)],
                  [SimpleNamespace(type=pico2d.SDL_QUIT)]]
        with patch.object(pico2d, 'get_events', side_effect=events), patch.object(pico2d, 'delay'):
            game_framework.run(first, {pico2d.SDLK_F2: second})
        self.assertLess(log.index(('first', 'exit')), log.index(('second', 'enter')))
        self.assertEqual(log.count(('first', 'update')), 1)
        self.assertEqual(log.count(('second', 'update')), 1)
        self.assertEqual(log[-1], ('second', 'exit'))
        self.assertIsNone(game_framework.current_mode)

    def test_mode_requested_exit_does_not_update_after_quitting(self):
        log = []
        with patch.object(pico2d, 'get_events', return_value=[]):
            game_framework.run(self.mode('stop', log, stop=True))
        self.assertEqual(log, [('stop', 'enter'), ('stop', 'exit')])

    def test_camera_clamps_at_both_map_edges_and_small_world(self):
        camera = Camera(960, 3600)
        camera.follow(120)
        self.assertEqual(camera.x, 0)
        camera.follow(1500)
        self.assertEqual(camera.x, 1116)
        camera.follow(3600)
        self.assertEqual(camera.x, 2640)
        small = Camera(960, 600)
        small.follow(500)
        self.assertEqual(small.x, 0)
