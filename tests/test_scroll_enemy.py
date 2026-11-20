"""문어 등장·착지·추적·총격과 공통 접촉 피해, 횡스크롤 사망 검사."""

import random
import unittest
from unittest.mock import patch

import game_world
import game_framework
import scroll_mode
from player import Player
from enemy import TestEnemy
from bullet import Bullet
from scroll_enemy import OctopusEnemy, OctopusSpawner
from octopus_sprite import OctopusDeath, OctopusSprite, DEATH_DURATION, SCALE, frame_bounds


class OctopusTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(384, 144, 3600)
        game_world.add_object(self.player, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def enemy(self, x=700):
        enemy = OctopusEnemy(x, self.player, 144)
        game_world.add_object(enemy, game_world.ACTORS)
        return enemy

    def test_falls_into_view_before_landing_and_only_then_tracks(self):
        enemy = self.enemy()
        self.assertEqual(enemy.get_bb()[1], 540)
        enemy.update(1)
        self.assertEqual(enemy.x, 700)
        self.assertLess(enemy.get_bb()[1], 540)
        self.assertFalse(enemy.grounded)
        enemy.update(3)
        self.assertTrue(enemy.grounded)
        self.assertEqual(enemy.get_bb()[1], 144)
        self.assertLess(enemy.x, 700)
        self.assertGreater(enemy.x, self.player.x)

    def test_ground_chase_turns_without_overshoot_and_is_slower_than_player(self):
        enemy = self.enemy()
        enemy.update(10)
        self.assertEqual(enemy.x, self.player.x)
        self.player.x = 900
        enemy.update(.5)
        self.assertEqual(enemy.x, 384 + enemy.MOVE_SPEED * .5)
        self.assertLess(enemy.MOVE_SPEED, self.player.MOVE_SPEED)

    def test_three_actual_bullets_remove_enemy(self):
        enemy = self.enemy()
        enemy.update(3)
        for remaining_hp in (2, 1, 0):
            bullet = Bullet(enemy.x - 100, enemy.y, 1, 'player', 3600)
            game_world.add_object(bullet, game_world.PROJECTILES)
            bullet.update(.2)
            self.assertFalse(bullet.active)
            self.assertEqual(enemy.hp, remaining_hp)
        self.assertNotIn(enemy, game_world.objects(game_world.ACTORS))
        effects = game_world.objects(game_world.EFFECTS)
        self.assertEqual(len(effects), 1)
        self.assertIsInstance(effects[0], OctopusDeath)
        enemy.take_damage(1)
        self.assertEqual(len(game_world.objects(game_world.EFFECTS)), 1)
        effects[0].update(DEATH_DURATION)
        self.assertFalse(game_world.objects(game_world.EFFECTS))

    def test_common_body_contact_respects_invincibility_and_dead_enemies(self):
        # 공통 경로가 보스의 부모 클래스인 기존 적에도 적용되는지 확인한다.
        enemy = TestEnemy(960, 540, 144)
        enemy.x, enemy.y = self.player.x, self.player.y
        enemy.fire_timer = 100
        game_world.add_object(enemy, game_world.ACTORS)
        game_world.update(.01)
        self.assertEqual(self.player.hp, 4)
        game_world.update(.01)
        self.assertEqual(self.player.hp, 4)
        enemy.take_damage(enemy.MAX_HP)
        game_world.update(1.1)
        self.assertEqual(self.player.hp, 4)

    def test_spawn_interval_camera_bounds_spacing_and_limit(self):
        spawner = OctopusSpawner(self.player, 144, rng=random.Random(5))
        spawner.update(2.9, 1416)
        self.assertEqual(len(game_world.objects(game_world.ACTORS)), 1)
        spawner.update(.11, 1416)
        first = game_world.objects(game_world.ACTORS)[1]
        self.assertGreaterEqual(first.get_bb()[0], 1416)
        self.assertLessEqual(first.get_bb()[2], 2376)
        spawner.update(3, 1416)
        second = game_world.objects(game_world.ACTORS)[2]
        self.assertGreaterEqual(abs(first.x - second.x), spawner.MIN_SPAWN_GAP)
        for _ in range(40):
            spawner.update(3, 1416)
        alive = [obj for obj in game_world.objects(game_world.ACTORS)
                 if isinstance(obj, OctopusEnemy)]
        self.assertLessEqual(len(alive), spawner.MAX_ALIVE)

    def test_dead_player_prevents_spawning_and_far_enemies_are_removed(self):
        enemy = self.enemy(100)
        spawner = OctopusSpawner(self.player, 144, rng=random.Random(2))
        spawner.update(.1, 1800)
        self.assertNotIn(enemy, game_world.objects(game_world.ACTORS))
        self.player.hp = 0
        spawner.update(100, 1800)
        self.assertEqual(game_world.objects(game_world.ACTORS), (self.player,))

    def test_draw_uses_camera_coordinates(self):
        enemy = self.enemy(1800)
        game_world.camera_x = 1400
        with patch('pico2d.load_image') as load, patch('pico2d.draw_rectangle'):
            enemy.draw()
            args = load.return_value.clip_draw.call_args.args
            self.assertEqual(args[:4], (16, 371, 245, 333))
            self.assertEqual(args[4], 400)
            self.assertAlmostEqual(args[5] - args[7] / 2 + 2 * SCALE, enemy.get_bb()[1])
            self.assertAlmostEqual(args[6] / args[7], 245 / 333)
            enemy.draw()
            load.assert_called_once()

    def test_move_animation_loops_without_changing_physics_and_death_does_not_loop(self):
        enemy = self.enemy()
        enemy.update(.125)
        self.assertEqual(frame_bounds(enemy.animation_time), (286, 74, 536, 347))
        self.assertFalse(enemy.grounded)
        self.assertEqual(frame_bounds(1), frame_bounds(0))
        self.assertEqual(frame_bounds(10, dying=True), (1825, 428, 2098, 665))

    def test_hit_flash_alternates_and_does_not_grant_enemy_invincibility(self):
        enemy = self.enemy()
        with patch.object(enemy.sprite, 'draw') as draw, patch('pico2d.draw_rectangle'):
            enemy.take_damage(1)
            enemy.draw()
            self.assertTrue(draw.call_args.kwargs['flash'])
            enemy.update(.07)
            enemy.draw()
            self.assertFalse(draw.call_args.kwargs['flash'])
            enemy.update(.06)
            enemy.draw()
            self.assertTrue(draw.call_args.kwargs['flash'])
            enemy.take_damage(1)
            self.assertEqual(enemy.hp, 1)
            enemy.update(enemy.HIT_DURATION)
            enemy.draw()
            self.assertFalse(draw.call_args.kwargs['flash'])

    def test_white_texture_reused_with_same_frame_and_death_uses_original(self):
        sprite = OctopusSprite()
        with patch('pico2d.load_image') as load, patch('octopus_sprite.white_silhouette') as white:
            sprite.draw(500, 144, .13)
            normal_args = load.return_value.clip_draw.call_args.args
            sprite.draw(500, 144, .13, flash=True)
            self.assertEqual(white.return_value.clip_draw.call_args.args, normal_args)
            sprite.draw(500, 144, .13, flash=True)
            white.assert_called_once()
            sprite.draw(500, 144, .13, dying=True, flash=True)
            self.assertEqual(white.return_value.clip_draw.call_count, 2)
            self.assertEqual(load.return_value.clip_draw.call_count, 2)


class ScrollEnemyIntegrationTests(unittest.TestCase):
    def tearDown(self):
        scroll_mode.exit()

    def test_mode_spawns_and_restart_resets_timer(self):
        scroll_mode.enter()
        scroll_mode.update(3.1)
        self.assertEqual(sum(isinstance(obj, OctopusEnemy)
                             for obj in game_world.objects(game_world.ACTORS)), 1)
        scroll_mode.enter()
        self.assertFalse(any(isinstance(obj, OctopusEnemy)
                             for obj in game_world.objects(game_world.ACTORS)))
        self.assertEqual(scroll_mode.spawner.timer, OctopusSpawner.SPAWN_INTERVAL)

    def test_lethal_contact_stops_spawning_and_prevents_boss_transition(self):
        scroll_mode.enter()
        player = scroll_mode.player
        player.x = 3582
        player.hp = 1
        enemy = OctopusEnemy(player.x, player, 144)
        enemy.y, enemy.grounded = 188, True
        game_world.add_object(enemy, game_world.ACTORS)
        with patch.object(game_framework, 'change_mode') as transition:
            scroll_mode.update(.01)
            self.assertTrue(scroll_mode.game_over)
            self.assertEqual(player.hp, 0)
            transition.assert_not_called()
        spawner = scroll_mode.spawner
        with patch.object(spawner, 'update') as spawn:
            scroll_mode.update(10)
            spawn.assert_not_called()
