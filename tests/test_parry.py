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
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN,key=pico2d.SDLK_SPACE))
    def release(self):
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYUP,key=pico2d.SDLK_SPACE))
    def incoming(self, reward='doodle', x=150, y=None):
        b=Bullet(x,self.player.y if y is None else y,-1,'enemy',960,parry_reward=reward)
        game_world.add_object(b,game_world.PROJECTILES)
        return b
    def test_first_jump_parries_only_bullet_already_in_range(self):
        b=self.incoming(); self.press()
        self.assertFalse(self.player.grounded)
        self.assertFalse(b.active)
        self.assertEqual(self.player.doodle_count,11)
        b.update(.5)
        self.assertEqual(self.player.hp,5)
        self.assertEqual(self.player.doodle_count,11)
    def test_air_reinput_rewards_and_bounces_repeatedly(self):
        self.player.jump(); self.player.update(.3)
        for _ in range(2):
            self.release(); self.incoming('eraser'); self.press()
            self.assertEqual(self.player.velocity_y,self.player.JUMP_SPEED)
            self.assertFalse(self.player.grounded)
            self.player.update(.05)
        self.assertEqual(self.player.eraser_count,12)
        self.assertEqual(self.player.hp,5)
    def test_early_press_never_arms_future_contact(self):
        b=self.incoming(x=200); self.press(); b.update(.4)
        self.assertEqual(self.player.doodle_count,10)
        self.assertEqual(self.player.hp,4)
    def test_airborne_contact_without_new_press_takes_damage(self):
        self.press(); self.player.update(.1)
        self.assertFalse(self.player.grounded)
        self.incoming().update(.2)
        self.assertEqual(self.player.hp,4)
        self.assertEqual(self.player.doodle_count,10)
    def test_normal_attack_cannot_be_parried(self):
        b=self.incoming(None); self.press()
        self.assertTrue(b.active)
        b.update(.2); self.assertEqual(self.player.hp,4)
    def test_held_space_and_one_press_cannot_parry_second_bullet(self):
        self.incoming(); second=self.incoming('eraser',x=152)
        self.press(); self.press()
        self.assertEqual(self.player.doodle_count,11)
        self.assertEqual(self.player.eraser_count,10)
        second.update(.2); self.assertEqual(self.player.hp,4)
    def test_far_or_wrong_height_bullet_is_not_parried(self):
        far=self.incoming(x=300); high=self.incoming('eraser',y=200)
        self.press()
        self.assertTrue(far.active); self.assertTrue(high.active)
        self.assertEqual(self.player.doodle_count,10)
        self.assertEqual(self.player.eraser_count,10)
    def test_doodle_blocks_colored_bullet_and_crouch_blocks_parry(self):
        platform=Doodle(200,108); game_world.add_object(platform,game_world.TERRAIN)
        self.incoming(x=300).update(1)
        self.assertEqual(platform.hp,19); self.assertEqual(self.player.hp,5)
        self.player.handle_event(SimpleNamespace(type=pico2d.SDL_KEYDOWN,key=pico2d.SDLK_DOWN))
        b=self.incoming(); self.press()
        self.assertTrue(b.active); self.assertEqual(self.player.doodle_count,10)
