"""개구리 잠복·접근·왕복 점프와 실제 총격·접촉 검사."""

import unittest

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
