"""고양이 로봇 대기·반동과 3행을 제외한 4행 죽기 검사."""

import unittest
from unittest.mock import Mock, patch

from core import game_world
from graphics.cat_robot_sprite import (CatRobotSprite, CatRobotDeath, frame_for,
                              IDLE_BOUNDS, FIRE_BOUNDS, DEATH_BOUNDS, DEATH_TOTAL_DURATION, SCALE)


class RobotSpriteTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def test_idle_loops_recoil_holds_last_and_third_row_is_never_used(self):
        self.assertEqual(frame_for('idle', 8 / 6)[1], IDLE_BOUNDS[0])
        self.assertEqual(frame_for('fire', 10)[1], FIRE_BOUNDS[-1])
        self.assertEqual(frame_for('death', 10)[1], DEATH_BOUNDS[-1])
        self.assertTrue(all(bounds[1] >= 665 for bounds in DEATH_BOUNDS))
        self.assertEqual(len(DEATH_BOUNDS), 7)

    def test_render_preserves_feet_scale_camera_and_body_pivot_when_flipped(self):
        sprite = CatRobotSprite()
        game_world.camera_x = 2640
        with patch('pico2d.load_image') as load:
            positions = []
            for direction in (-1, 1):
                sprite.draw('idle', 0, 3420, 144, direction)
                args = load.return_value.clip_composite_draw.call_args.args
                self.assertEqual(args[:4], (27, 688, 189, 176))
                self.assertEqual(args[5], 'h' if direction < 0 else '')
                self.assertAlmostEqual(args[7] - args[9] / 2 + 2 * SCALE, 144)
                positions.append(args[6])
            self.assertAlmostEqual(sum(positions) / 2, 780)
            load.assert_called_once()

    def test_fourth_row_explosion_runs_once_and_is_removed(self):
        sprite = Mock()
        effect = CatRobotDeath(sprite, 3420, 200, -1)
        game_world.add_object(effect, game_world.EFFECTS)
        effect.draw()
        self.assertEqual(sprite.draw.call_args.args[:2], ('death', 0))
        effect.update(DEATH_TOTAL_DURATION)
        self.assertNotIn(effect, game_world.objects(game_world.EFFECTS))

    def test_three_original_size_explosions_overlap_with_staggered_starts(self):
        sprite = Mock()
        effect = CatRobotDeath(sprite, 3420, 200, -1)
        effect.elapsed = .25
        effect.draw()
        self.assertEqual(sprite.draw.call_count, 3)
        calls = sprite.draw.call_args_list
        for call, elapsed in zip(calls, (.25, .13, .01)):
            self.assertAlmostEqual(call.args[1], elapsed)
            self.assertEqual(call.kwargs['scale_factor'], 1)
        self.assertEqual([call.args[2:4] for call in calls],
                         [(3382, 200), (3458, 200), (3420, 236)])

    def test_hit_draws_original_with_twenty_percent_white_overlay(self):
        sprite = CatRobotSprite()
        with patch('pico2d.load_image') as load, patch('graphics.cat_robot_sprite.white_silhouette') as white:
            sprite.draw('idle', 0, 3420, 144, -1, flash=True)
            load.return_value.clip_composite_draw.assert_called_once()
            self.assertEqual(white.return_value.clip_composite_draw.call_args,
                             load.return_value.clip_composite_draw.call_args)
            self.assertEqual([call.args[0] for call in white.return_value.opacify.call_args_list],
                             [.2, 1.0])
            sprite.draw('death', 0, 3420, 200, -1, flash=True)
            self.assertEqual(white.return_value.clip_composite_draw.call_count, 1)
