"""방어용 낙서가 반격을 막는 보스 패턴 검사."""

import unittest
import random

import game_world
from boss import Boss
from bullet import Bullet
from doodle import Doodle
from eraser import Eraser


class BossTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.boss = Boss(960, 540, 80, rng=random.Random(17))
        game_world.add_object(self.boss, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def shoot(self, y=108):
        bullet = Bullet(120, y, 1, 'player', 960)
        bullet.update(2)

    def test_phases_repeat_without_warning_or_erasing_existing_bullets(self):
        self.boss.update(.01)
        self.assertEqual(self.boss.state, 'attack')
        self.assertEqual(len(game_world.objects(game_world.PROJECTILES)), 6)
        self.boss.update(self.boss.PHASE_DURATIONS['attack'])
        self.assertEqual(self.boss.state, 'rest')
        self.assertEqual(self.boss.burst_shots, 6)
        self.assertEqual(self.boss.volley_index, 6)
        self.assertGreaterEqual(len(game_world.objects(game_world.PROJECTILES)), 36)
        before = game_world.objects(game_world.PROJECTILES)
        self.boss.update(.5)
        self.assertTrue(all(obj in game_world.objects(game_world.PROJECTILES) for obj in before))
        self.boss.update(3.5)
        self.assertEqual(self.boss.state, 'normal_burst')

    def test_rest_fires_random_single_shots_without_warning(self):
        self.boss.state = 'attack'
        self.boss.advance_phase()
        self.boss.update(.001)
        self.assertEqual(self.boss.rest_shots, 1)
        shots = game_world.objects(game_world.PROJECTILES)
        self.assertEqual(len(shots), 1)
        self.boss.update(1)
        shots = game_world.objects(game_world.PROJECTILES)
        self.assertTrue(all(152 <= shot.y <= 232 and shot.parry_reward is None for shot in shots))
        self.assertGreaterEqual(len(shots), 8)
        self.assertLessEqual(len(shots), 14)
        self.assertGreater(len({round(shot.y) for shot in shots}), 4)

    def test_upper_rest_bullets_miss_floor_but_hit_platform_height(self):
        from player import Player
        for center_y, expected_hp in ((108, 5), (152, 4), (216, 4)):
            with self.subTest(center_y=center_y):
                game_world.clear()
                player = Player(120, 80, 960)
                player.y = center_y
                game_world.add_object(player, game_world.ACTORS)
                for _ in range(60):
                    self.boss.fire_rest_volley()
                for shot in game_world.objects(game_world.PROJECTILES):
                    shot.update(3)
                self.assertEqual(player.hp, expected_hp)

    def test_rest_transition_preserves_own_shots_and_erasers(self):
        friendly = Bullet(400, 108, 1, 'player', 960)
        eraser = Eraser(200, 108, 1, 960)
        game_world.add_object(friendly, game_world.PROJECTILES)
        game_world.add_object(eraser, game_world.PROJECTILES)
        self.boss.fire_volley()
        self.boss.state = 'attack'
        self.boss.advance_phase()
        self.assertIn(friendly, game_world.objects(game_world.PROJECTILES))
        self.assertIn(eraser, game_world.objects(game_world.PROJECTILES))
        hostile = [obj for obj in game_world.objects(game_world.PROJECTILES)
                   if isinstance(obj, Bullet) and obj.team == 'enemy']
        self.assertEqual(len(hostile), 6)
        self.assertTrue(all(obj.active for obj in hostile))
        low = min(hostile, key=lambda obj: obj.y)
        x = low.x
        low.update(.1)
        self.assertLess(low.x, x)

    def test_whole_body_takes_damage_during_every_phase(self):
        expected_hp = 30
        for phase in ('attack', 'rest'):
            self.boss.state = phase
            heights = (90, 108, 130) if phase == 'rest' else (90, 136, 185)
            for height in heights:
                with self.subTest(phase=phase, height=height):
                    self.shoot(height)
                    expected_hp -= 1
                    self.assertEqual(self.boss.hp, expected_hp)

    def test_each_attack_restarts_fixed_volley_count(self):
        cycle = sum(self.boss.PHASE_DURATIONS.values())
        cycle += sum(self.boss.NORMAL_PHASE_DURATIONS.values()) * self.boss.NORMAL_CYCLES
        self.boss.update(cycle + .02)
        self.assertEqual(self.boss.pattern, 'homing')
        self.boss.state = 'homing_recover'
        self.boss.advance_phase()
        self.assertEqual(self.boss.pattern, 'laser')
        self.boss.state = 'laser_recover'
        self.boss.advance_phase()
        self.boss.update(.02)
        self.assertEqual(self.boss.state, 'attack')
        self.assertEqual(self.boss.burst_shots, 1)
        self.assertEqual(self.boss.volley_index, 7)

    def test_cover_blocks_attack_and_own_shot_until_erased(self):
        cover = Doodle(250, 108)
        game_world.add_object(cover, game_world.TERRAIN)
        Bullet(700, 108, -1, 'enemy', 960).update(2)
        self.assertEqual(cover.hp, 19)
        self.boss.state = 'rest'
        self.shoot()
        self.assertEqual(self.boss.hp, 30)
        self.assertEqual(cover.hp, 18)
        eraser = Eraser(120, 108, 1, 960)
        eraser.update(.5)
        self.assertNotIn(cover, game_world.objects(game_world.TERRAIN))
        self.shoot()
        self.assertEqual(self.boss.hp, 29)

    def test_eraser_cannot_remove_or_damage_boss(self):
        self.boss.state = 'rest'
        Eraser(700, 108, 1, 960).update(.5)
        self.assertEqual(self.boss.hp, 30)
        self.assertIn(self.boss, game_world.objects(game_world.ACTORS))

    def test_defeat_stops_firing_but_bullets_fly_until_offscreen(self):
        self.boss.fire_volley()
        self.boss.state = 'rest'
        self.boss.take_damage(30)
        bullets = game_world.objects(game_world.PROJECTILES)
        self.assertEqual(len(bullets), 6)
        self.assertNotIn(self.boss, game_world.objects(game_world.ACTORS))
        self.boss.update(20)
        self.assertEqual(game_world.objects(game_world.PROJECTILES), bullets)
        for bullet in bullets:
            bullet.update(5)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))

    def test_attack_volley_contains_only_normal_bullets(self):
        self.boss.fire_volley()
        bullets = game_world.objects(game_world.PROJECTILES)
        self.assertEqual(len(bullets), 6)
        self.assertTrue(all(bullet.parry_reward is None for bullet in bullets))

    def test_one_layer_leaks_but_two_layers_protect_standing_player(self):
        from player import Player
        for layers, expected_hp in ((1, 4), (2, 5)):
            with self.subTest(layers=layers):
                game_world.clear()
                player = Player(120, 80, 960)
                game_world.add_object(player, game_world.ACTORS)
                for i in range(layers):
                    game_world.add_object(Doodle(250, 108 + i * 32), game_world.TERRAIN)
                self.boss.fire_volley()
                for bullet in game_world.objects(game_world.PROJECTILES):
                    bullet.update(4)
                self.assertEqual(player.hp, expected_hp)

    def test_three_layers_protect_player_at_raised_height(self):
        from player import Player
        for layers, expected_hp in ((2, 4), (3, 5)):
            game_world.clear()
            player = Player(120, 80, 960)
            player.y = 140
            game_world.add_object(player, game_world.ACTORS)
            for i in range(layers):
                game_world.add_object(Doodle(250, 108 + i * 32), game_world.TERRAIN)
            self.boss.fire_volley()
            for bullet in game_world.objects(game_world.PROJECTILES):
                bullet.update(4)
            self.assertEqual(player.hp, expected_hp)

    def test_rest_halves_height_with_feet_fixed_and_restores_afterwards(self):
        self.assertEqual(self.boss.get_bb()[3] - self.boss.get_bb()[1], 112)
        self.boss.state = 'attack'
        self.boss.advance_phase()
        self.assertEqual(self.boss.state, 'rest')
        self.assertEqual(self.boss.get_bb()[1], 80)
        self.assertEqual(self.boss.get_bb()[3], 136)
        self.assertEqual(self.boss.y, 108)
        self.shoot(170)
        self.assertEqual(self.boss.hp, 30)
        self.shoot(108)
        self.assertEqual(self.boss.hp, 29)
        self.boss.advance_phase()
        self.assertEqual(self.boss.state, 'normal_burst')
        self.assertEqual(self.boss.get_bb()[3], 192)
