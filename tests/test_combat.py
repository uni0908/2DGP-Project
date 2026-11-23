"""총격, 엄폐물, 체력 및 테스트 적의 회귀 검사."""

import unittest

import pico2d
from core import game_world
from bullet import Bullet
from doodle import Doodle
from player import Player
from enemy import TestEnemy
from eraser import Eraser


class CombatTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(120, 80, 960)
        game_world.add_object(self.player, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def bullet(self, x, y, direction=-1, team='enemy'):
        bullet = Bullet(x, y, direction, team, 960)
        game_world.add_object(bullet, game_world.PROJECTILES)
        return bullet

    def test_hit_once_and_game_over_health(self):
        for _ in range(5):
            bullet = self.bullet(200, 108)
            bullet.update(.5)
            hp = self.player.hp
            bullet.update(.5)
            self.assertEqual(self.player.hp, hp)
            self.player.update(1.01)
        self.assertEqual(self.player.hp, 0)
        self.player.take_damage(1)
        self.assertEqual(self.player.hp, 0)

    def test_player_fire_does_not_consume_resources_or_hit_self(self):
        resources = (self.player.doodle_count, self.player.eraser_count)
        self.player.pressed_keys.add(pico2d.SDLK_a)
        self.player.update(.01)
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 1)
        self.player.update(.01)
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 1)
        game_world.objects(game_world.PROJECTILES)[0].update(.1)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(resources, (self.player.doodle_count, self.player.eraser_count))

    def test_both_teams_blocked_by_doodle_and_destroy_it(self):
        for team, x, direction in (('enemy', 400, -1), ('player', 120, 1)):
            with self.subTest(team=team):
                doodle = Doodle(250, 108)
                game_world.add_object(doodle, game_world.TERRAIN)
                for index in range(20):
                    bullet = self.bullet(x, 108, direction, team)
                    bullet.update(1)
                    self.assertFalse(bullet.active)
                    if index < 19:
                        self.assertIn(doodle, game_world.objects(game_world.TERRAIN))
                self.assertNotIn(doodle, game_world.objects(game_world.TERRAIN))
                self.assertEqual(self.player.hp, 5)

    def test_destroyed_support_causes_fall(self):
        doodle = Doodle(300, 160)
        game_world.add_object(doodle, game_world.TERRAIN)
        self.player.x, self.player.y = 300, 204
        for _ in range(20):
            self.bullet(450, 160).update(1)
        self.player.update(.05)
        self.assertLess(self.player.y, 204)
        self.assertFalse(self.player.grounded)

    def test_closest_target_wins_and_offscreen_bullet_expires(self):
        doodle = Doodle(250, 108)
        game_world.add_object(doodle, game_world.TERRAIN)
        self.bullet(500, 108).update(2)
        self.assertEqual(self.player.hp, 5)
        self.assertEqual(doodle.hp, 19)
        bullet = self.bullet(800, 500, 1, 'player')
        bullet.update(1)
        self.assertFalse(bullet.active)

    def test_enemy_is_fixed_and_fires_three_types_in_order(self):
        enemy = TestEnemy(960, 540, 80)
        self.assertEqual((enemy.WIDTH, enemy.HEIGHT), (Player.WIDTH * 4, Player.HEIGHT * 2))
        x = enemy.x
        heights = []
        for _ in range(300):
            enemy.update(.02)
            heights.append(enemy.y)
            self.assertEqual(enemy.x, x)
            self.assertGreaterEqual(enemy.y, enemy.min_y)
            self.assertLessEqual(enemy.y, enemy.max_y)
        self.assertEqual(max(heights), min(heights))
        shots = game_world.objects(game_world.PROJECTILES)
        self.assertEqual(len(shots), 5)
        self.assertEqual([shot.parry_reward for shot in shots],
                         [None, 'doodle', 'eraser', None, 'doodle'])
        self.assertTrue(all(shot.y == 170 for shot in shots))

    def test_invincibility_blocks_followup_hit_then_expires(self):
        self.bullet(200, 108).update(.5)
        self.assertEqual(self.player.hp, 4)
        followup = self.bullet(200, 108)
        followup.update(.5)
        self.assertEqual(self.player.hp, 4)
        self.assertFalse(followup.active)
        self.player.update(.9)
        self.bullet(200, 108).update(.5)
        self.assertEqual(self.player.hp, 4)
        self.player.update(.11)
        self.bullet(200, 108).update(.5)
        self.assertEqual(self.player.hp, 3)

    def test_player_bullet_damages_enemy_but_eraser_does_not(self):
        enemy = TestEnemy(960, 540, 80)
        game_world.add_object(enemy, game_world.ACTORS)
        eraser = Eraser(700, enemy.y, 1, 960)
        game_world.add_object(eraser, game_world.PROJECTILES)
        eraser.update(.4)
        self.assertEqual(enemy.hp, enemy.MAX_HP)
        self.assertIn(enemy, game_world.objects(game_world.ACTORS))
        self.bullet(700, enemy.y, 1, 'player').update(.4)
        self.assertEqual(enemy.hp, enemy.MAX_HP - 1)
        enemy.take_damage(enemy.hp)
        self.assertNotIn(enemy, game_world.objects(game_world.ACTORS))

    def test_game_over_freezes_world_and_restart_resets_state(self):
        import play_mode
        from types import SimpleNamespace
        from unittest.mock import patch
        play_mode.enter()
        try:
            play_mode.player.take_damage(5)
            play_mode.update(.02)
            self.assertTrue(play_mode.game_over)
            old_y = play_mode.enemy.y
            play_mode.update(1)
            self.assertEqual(play_mode.enemy.y, old_y)
            self.assertIsNone(play_mode.spawn_doodle())
            self.assertIsNone(play_mode.throw_eraser())
            events = [SimpleNamespace(type=pico2d.SDL_KEYDOWN, key=pico2d.SDLK_r)]
            with patch.object(pico2d, 'get_events', return_value=events):
                self.assertTrue(play_mode.handle_events())
            self.assertFalse(play_mode.game_over)
            self.assertEqual(play_mode.player.hp, 5)
            self.assertEqual(play_mode.enemy.hp, TestEnemy.MAX_HP)
            self.assertFalse(game_world.objects(game_world.PROJECTILES))
        finally:
            play_mode.exit()
