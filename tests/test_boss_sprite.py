import unittest
from unittest.mock import Mock, patch

import game_world
from boss1 import Boss1
from boss_sprite import DATA, BossDeath, animation_for, animation_frame
from doodle import Doodle


class BossSpriteTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.boss = Boss1(960, 540, 80, shuffle_patterns=False)
        game_world.add_object(self.boss, game_world.ACTORS)

    def tearDown(self):
        game_world.clear()

    def test_attack_states_select_supplied_animations(self):
        for state, expected in (
                ('attack', 'barrage_fire'), ('rest', 'rest_upper_fire'),
                ('normal_burst', 'normal_fire'), ('normal_pause', 'idle'),
                ('homing_launch', 'homing_launch'), ('homing_wait', 'idle'),
                ('laser_charge', 'laser_charge'), ('laser_sweep', 'laser_hold'),
                ('laser_recover', 'recover')):
            self.boss.state = state
            self.assertEqual(animation_for(self.boss), expected)
        self.boss.state = 'normal_parry'
        self.boss.state_time = .2
        self.assertEqual(animation_for(self.boss), 'idle')

    def test_hit_overlay_preserves_attack_state_and_phase_time(self):
        self.boss.state_time = .4
        self.boss.take_damage(1)
        self.assertEqual(self.boss.state_time, .4)
        self.assertEqual(self.boss.state, 'attack')
        self.assertEqual(self.boss.hit_elapsed, 0)
        self.boss.sprite.images = {key: Mock() for key in DATA['sheets']}
        with patch('pico2d.draw_rectangle'):
            self.boss.draw()
        self.boss.sprite.images['boss1-effects.png'].clip_composite_draw.assert_called_once()

    def test_death_visual_plays_once_and_does_not_fire_or_take_damage(self):
        self.boss.take_damage(30)
        self.boss.take_damage(1)
        self.assertNotIn(self.boss, game_world.objects(game_world.ACTORS))
        visuals = game_world.objects(game_world.EFFECTS)
        self.assertEqual(len(visuals), 1)
        self.assertIsInstance(visuals[0], BossDeath)
        visuals[0].update(2)
        last = DATA['frames'][DATA['animations']['death']['frames'][-1]]
        self.assertEqual(animation_frame('death', visuals[0].elapsed), last)
        self.assertFalse(game_world.objects(game_world.PROJECTILES))
        game_world.clear()
        self.assertFalse(game_world.objects(game_world.EFFECTS))

    def test_normal_projectile_art_and_parry_colors(self):
        self.boss.fire_normal_bullet()
        self.boss.fire_normal_bullet('eraser')
        normal, parry = game_world.objects(game_world.PROJECTILES)
        self.boss.sprite.draw_effect = Mock()
        normal.draw()
        self.assertEqual(self.boss.sprite.draw_effect.call_args.args[0], 'bullet')
        with patch('pico2d.draw_rectangle') as rectangle:
            parry.draw()
        self.assertEqual(rectangle.call_args.args[4:7], (30, 180, 240))

    def test_missile_impact_plays_temporary_explosion(self):
        missile = self.boss.fire_homing_missile()
        game_world.add_object(Doodle(missile.x - 40, missile.y), game_world.TERRAIN)
        missile.update(.5)
        self.assertFalse(missile.active)
        effects = game_world.objects(game_world.EFFECTS)
        self.assertEqual(len(effects), 1)
        effects[0].update(1)
        self.assertFalse(game_world.objects(game_world.EFFECTS))
