"""입력 시간, 색상별 보상과 실패·중복 처리 회귀 검사."""

import unittest
from types import SimpleNamespace

import pico2d
import game_world
from player import Player
from bullet import Bullet
from doodle import Doodle


class ParryTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(120, 80, 960)
        game_world.add_object(self.player, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def press(self):
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN,
                                                 key=pico2d.SDLK_SPACE))

    def release(self):
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYUP,
                                                 key=pico2d.SDLK_SPACE))

    def hit(self, reward='doodle', y=None, dt=.2):
        bullet = Bullet(160, self.player.y if y is None else y, -1,
                        'enemy', 960, parry_reward=reward)
        game_world.add_object(bullet, game_world.PROJECTILES)
        bullet.update(dt)
        return bullet

    def test_first_jump_rewards_doodle_once_without_damage(self):
        self.press()
        self.assertFalse(self.player.grounded)
        bullet = self.hit()
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(self.player.doodle_count, 11)
        self.assertEqual(self.player.eraser_count, 10)
        self.assertFalse(bullet.active)
        bullet.update(.2)
        self.assertEqual(self.player.doodle_count, 11)

    def test_air_reinput_rewards_eraser_and_bounces_repeatedly(self):
        self.player.jump()
        self.player.update(.3)
        self.assertLess(self.player.velocity_y, self.player.JUMP_SPEED)
        for _ in range(2):
            self.release()
            self.press()
            self.hit('eraser')
            self.assertEqual(self.player.velocity_y, self.player.JUMP_SPEED)
            self.assertFalse(self.player.grounded)
            self.player.update(.05)
        self.assertEqual(self.player.eraser_count, 12)
        self.assertEqual(self.player.hp, 5)

    def test_touch_without_input_and_expired_window_take_damage(self):
        self.hit()
        self.assertEqual(self.player.hp, 4)
        self.player.update(1.1)
        self.press()
        self.player.update(self.player.PARRY_WINDOW + .01)
        self.hit('eraser')
        self.assertEqual(self.player.hp, 3)
        self.assertEqual(self.player.eraser_count, 10)

    def test_normal_attack_cannot_be_parried(self):
        self.press()
        self.hit(None)
        self.assertEqual(self.player.hp, 4)
        self.assertEqual(self.player.doodle_count, 10)

    def test_holding_space_does_not_refresh_or_auto_parry_second_bullet(self):
        self.press()
        self.player.update(.1)
        remaining = self.player.parry_timer
        self.press()
        self.assertEqual(self.player.parry_timer, remaining)
        self.hit()
        self.hit('eraser')
        self.assertEqual(self.player.doodle_count, 11)
        self.assertEqual(self.player.eraser_count, 10)
        self.assertEqual(self.player.hp, 4)

    def test_parry_margin_only_applies_to_colored_bullets(self):
        self.press()
        self.hit('doodle', y=self.player.get_bb()[3] + 10)
        self.assertEqual(self.player.doodle_count, 11)
        self.release()
        self.press()
        ordinary = self.hit(None, y=self.player.get_bb()[3] + 10)
        self.assertTrue(ordinary.active)
        self.assertEqual(self.player.hp, 5)

    def test_doodle_blocks_colored_bullet_before_player(self):
        platform = Doodle(200, 108)
        game_world.add_object(platform, game_world.TERRAIN)
        self.press()
        bullet = Bullet(300, 108, -1, 'enemy', 960, parry_reward='doodle')
        bullet.update(1)
        self.assertEqual(platform.hp, 19)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(self.player.doodle_count, 10)

    def test_focus_loss_cancels_window_and_crouch_does_not_arm_it(self):
        self.press()
        self.player.clear_input()
        self.assertEqual(self.player.parry_timer, 0)
        self.player.update(1)
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN,
                                                 key=pico2d.SDLK_DOWN))
        self.press()
        self.assertTrue(self.player.crouching)
        self.assertEqual(self.player.parry_timer, 0)
