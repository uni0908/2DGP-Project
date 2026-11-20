"""개구리 잠복·접근·왕복 점프와 실제 총격·접촉 검사."""

import unittest
from unittest.mock import patch

import pico2d
import game_world
import scroll_mode
from bullet import Bullet
from player import Player
from frog_enemy import FrogEnemy


class FrogTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(200, 144, 3600)
        self.frog = FrogEnemy(680, 960, self.player, 144)
        game_world.add_object(self.player, game_world.ACTORS)
        game_world.add_object(self.frog, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def shoot(self, y):
        bullet = Bullet(self.frog.x - 80, y, 1, 'player', 3600)
        game_world.add_object(bullet, game_world.PROJECTILES)
        bullet.update(.2)
        return bullet

    def test_hidden_frog_ignores_even_low_bullet_and_does_not_block_target_behind(self):
        other = FrogEnemy(900, 1000, self.player, 144)
        other.state = 'idle'
        game_world.add_object(other, game_world.ACTORS)
        bullet = self.shoot(152)
        self.assertTrue(bullet.active)
        self.assertEqual(self.frog.hp, 1)
        bullet.update(.3)
        self.assertEqual(other.hp, 0)
        self.assertEqual(self.frog.hp, 1)

    def test_approach_exposes_frog_and_one_bullet_kills(self):
        self.player.x = self.frog.x - self.frog.ACTIVE_DISTANCE
        self.frog.update(.01)
        self.assertTrue(self.frog.bullet_vulnerable)
        self.assertEqual(self.frog.get_bb()[3] - self.frog.get_bb()[1], 44)
        self.assertFalse(self.shoot(176).active)
        self.assertEqual(self.frog.hp, 0)
        self.assertNotIn(self.frog, game_world.objects(game_world.ACTORS))

    def test_actual_standing_player_shot_can_hit_awake_frog(self):
        self.player.x = self.frog.x - 180
        self.frog.update(.01)
        self.player.pressed_keys.add(pico2d.SDLK_a)
        self.player.update(.01)
        shot = game_world.objects(game_world.PROJECTILES)[0]
        shot.update(.3)
        self.assertEqual(self.frog.hp, 0)

    def test_hops_stay_in_patrol_reverse_at_edges_and_return_to_ground(self):
        self.player.x = self.frog.x
        directions, max_bottom = set(), 144
        for _ in range(1200):
            self.frog.update(1 / 120)
            directions.add(self.frog.direction)
            max_bottom = max(max_bottom, self.frog.bottom)
            self.assertGreaterEqual(self.frog.x, 680)
            self.assertLessEqual(self.frog.x, 960)
            self.assertGreaterEqual(self.frog.bottom, 144)
        self.assertEqual(directions, {-1, 1})
        self.assertAlmostEqual(max_bottom - 144, 37.5, delta=.1)

    def test_leaving_range_finishes_current_hop_before_hiding(self):
        self.player.x = self.frog.x
        self.frog.update(.5)
        self.assertEqual(self.frog.state, 'hop')
        self.player.x = 0
        self.frog.update(1)
        self.assertEqual(self.frog.state, 'hidden')
        self.assertEqual(self.frog.bottom, 144)

    def test_body_contact_uses_player_invincibility(self):
        self.player.x = self.frog.x
        game_world.update(.01)
        self.assertEqual(self.player.hp, 4)
        game_world.update(.01)
        self.assertEqual(self.player.hp, 4)

    def test_restart_restores_patrols_and_mode_exit_clears_frogs(self):
        scroll_mode.enter()
        frogs = [obj for obj in game_world.objects(game_world.ACTORS) if isinstance(obj, FrogEnemy)]
        self.assertEqual(len(frogs), 3)
        frogs[0].state = 'idle'
        frogs[0].take_damage(1)
        scroll_mode.enter()
        self.assertEqual(sum(isinstance(obj, FrogEnemy)
                             for obj in game_world.objects(game_world.ACTORS)), 3)
        scroll_mode.exit()
        self.assertFalse(game_world.objects(game_world.ACTORS))

    def prepare_attack(self, direction=-1):
        self.player.x = self.frog.x + direction * 120
        self.frog.update(.01)
        self.frog.attack_cooldown = 0
        self.frog.update(.01)
        self.assertEqual(self.frog.state, 'windup')

    def test_tongue_warns_then_hits_both_directions_and_respects_invincibility(self):
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                self.player.hp = 5
                self.player.invincibility_timer = 0
                self.frog.state = 'hidden'
                self.prepare_attack(direction)
                self.frog.update(.39)
                self.assertEqual(self.player.hp, 5)
                self.assertIsNone(self.frog.tongue_bb())
                self.frog.update(.16)
                self.assertEqual(self.player.hp, 4)
                self.frog.update(.05)
                self.assertEqual(self.player.hp, 4)
                self.frog.update(.5)
                self.assertEqual(self.frog.state, 'recover')
                self.assertIsNone(self.frog.tongue_bb())

    def test_tongue_direction_locks_and_jump_or_crouch_avoids_it(self):
        self.prepare_attack(-1)
        self.player.y += 100
        self.frog.update(.55)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(self.frog.attack_direction, -1)
        self.player.x = self.frog.x + 120
        self.player.y = 144 + self.player.HEIGHT / 2
        self.frog.update(.05)
        self.assertEqual(self.player.hp, 5)
        self.player.x = self.frog.x - 120
        self.player.height = self.player.CROUCH_HEIGHT
        self.player.y = 144 + self.player.height / 2
        self.frog.update(.02)
        self.assertEqual(self.player.hp, 5)

    def test_tongue_retracts_and_dying_cancels_attack(self):
        self.prepare_attack()
        self.frog.update(.55)
        bounds = self.frog.tongue_bb()
        self.assertIsNotNone(bounds)
        self.assertAlmostEqual(bounds[2] - bounds[0], self.frog.TONGUE_LENGTH)
        self.frog.update(.12)
        shorter = self.frog.tongue_bb()
        self.assertLess(shorter[2] - shorter[0], self.frog.TONGUE_LENGTH)
        self.frog.take_damage(1)
        self.assertIsNone(self.frog.tongue_bb())
        hp = self.player.hp
        self.frog.update(2)
        self.assertEqual(self.player.hp, hp)

    def test_tongue_draw_uses_world_to_screen_conversion(self):
        self.prepare_attack()
        self.frog.update(.55)
        game_world.camera_x = 400
        with patch('pico2d.draw_rectangle') as draw:
            self.frog.draw()
        self.assertEqual(draw.call_args.args[:4], game_world.screen_bb(self.frog.tongue_bb()))
