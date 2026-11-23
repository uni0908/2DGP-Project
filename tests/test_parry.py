import unittest
from types import SimpleNamespace

import pico2d
from core import game_world
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
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_SPACE))

    def release(self):
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYUP, key=pico2d.SDLK_SPACE))

    def incoming(self, reward='doodle', x=150, y=None):
        bullet = Bullet(x, self.player.y if y is None else y, -1, 'enemy', 960, parry_reward=reward)
        game_world.add_object(bullet, game_world.PROJECTILES)
        return bullet

    def arm(self):
        self.press()
        self.player.update(.016)
        self.release()
        self.press()

    def test_first_jump_alone_cannot_parry(self):
        bullet = self.incoming()
        self.press()
        self.assertEqual(self.player.parry_timer, 0)
        bullet.update(.2)
        self.assertEqual(self.player.hp, 4)
        self.assertEqual(self.player.doodle_count, 10)

    def test_air_reinput_rewards_once_and_bounces(self):
        self.arm()
        bullet = self.incoming('eraser')
        self.player.attempt_parry()
        self.assertFalse(bullet.active)
        self.assertEqual(self.player.eraser_count, 11)
        self.assertEqual(self.player.velocity_y, self.player.JUMP_SPEED)
        self.assertEqual(self.player.parry_timer, 0)
        bullet.update(.5)
        self.assertEqual(self.player.eraser_count, 11)
        self.release()
        self.assertEqual(self.player.velocity_y, self.player.JUMP_SPEED)

    def test_bullet_arrives_during_short_window(self):
        self.arm()
        bullet = self.incoming(x=180)
        self.player.attempt_parry()
        self.assertTrue(bullet.active)
        bullet.update(.15)
        self.assertFalse(bullet.active)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(self.player.doodle_count, 11)

    def test_expired_window_contact_causes_damage(self):
        self.arm()
        self.player.update(.17)
        self.assertEqual(self.player.parry_timer, 0)
        self.incoming().update(.2)
        self.assertEqual(self.player.hp, 4)
        self.assertEqual(self.player.doodle_count, 10)

    def test_jump_without_air_reinput_takes_damage(self):
        self.press()
        self.player.update(.1)
        self.incoming().update(.2)
        self.assertEqual(self.player.hp, 4)
        self.assertEqual(self.player.doodle_count, 10)

    def test_normal_bullet_still_damages_during_parry(self):
        self.arm()
        self.incoming(None).update(.2)
        self.assertEqual(self.player.hp, 4)
        self.assertEqual(self.player.parry_timer, 0)

    def test_held_key_does_not_refresh_window(self):
        self.arm()
        self.player.update(.05)
        remaining = self.player.parry_timer
        self.press()
        self.assertEqual(self.player.parry_timer, remaining)
        self.player.update(.12)
        self.press()
        self.assertEqual(self.player.parry_timer, 0)

    def test_repeated_success_requires_reinput(self):
        self.arm()
        self.incoming()
        self.player.attempt_parry()
        second = self.incoming('eraser')
        self.press()
        self.assertTrue(second.active)
        self.release()
        self.press()
        self.assertFalse(second.active)
        self.assertEqual((self.player.doodle_count, self.player.eraser_count), (11, 11))

    def test_short_hop_can_parry_bullet_directly_above(self):
        bullet = self.incoming(x=134, y=170)
        self.press()
        self.player.update(.016)
        self.assertTrue(bullet.active)
        self.release()
        self.assertEqual(self.player.velocity_y, self.player.SHORT_JUMP_SPEED)
        self.press()
        self.assertFalse(bullet.active)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(self.player.doodle_count, 11)

    def test_failed_air_press_does_not_give_double_jump(self):
        self.press()
        self.player.update(.08)
        self.release()
        velocity = self.player.velocity_y
        self.press()
        self.assertEqual(self.player.velocity_y, velocity)
        self.assertGreater(self.player.parry_timer, 0)

    def test_doodle_blocks_colored_bullet(self):
        platform = Doodle(200, 108)
        game_world.add_object(platform, game_world.TERRAIN)
        self.arm()
        self.incoming(x=300, y=108).update(1)
        self.assertEqual(platform.hp, 19)
        self.assertEqual(self.player.doodle_count, 10)

    def test_landing_and_focus_loss_cancel_window(self):
        self.arm()
        self.player.clear_input()
        self.assertEqual(self.player.parry_timer, 0)
        self.player.y = 108
        self.player.velocity_y = -1
        self.player.grounded = False
        self.player.parry_timer = .16
        self.player.update(.008)
        self.assertTrue(self.player.grounded)
        self.assertEqual(self.player.parry_timer, 0)
