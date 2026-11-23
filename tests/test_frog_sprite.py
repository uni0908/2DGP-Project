"""개구리 시트의 자세·반전·발 정렬과 죽기 수명 검사."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core import game_world
from graphics.frog_sprite import (FrogSprite, FrogDeath, pose_for, SCALE, HIDDEN_BOUNDS,
                         HOP_BOUNDS, DEATH_BOUNDS, DEATH_DURATION)


class FrogSpriteTests(unittest.TestCase):
    def tearDown(self):
        game_world.clear()

    def test_hidden_loops_and_jump_pose_tracks_vertical_motion(self):
        frog = SimpleNamespace(state='hidden', state_time=0, velocity_y=400)
        self.assertEqual(pose_for(frog), HIDDEN_BOUNDS[0])
        frog.state_time = 1
        self.assertEqual(pose_for(frog), HIDDEN_BOUNDS[0])
        frog.state = 'hop'
        self.assertEqual(pose_for(frog), HOP_BOUNDS[2])
        frog.velocity_y = 0
        self.assertEqual(pose_for(frog), HOP_BOUNDS[3])
        frog.velocity_y = -300
        self.assertEqual(pose_for(frog), HOP_BOUNDS[4])
        frog.state = 'windup'
        self.assertEqual(pose_for(frog), HOP_BOUNDS[1])

    def test_body_preserves_scale_feet_and_camera_on_both_sides(self):
        sprite = FrogSprite()
        game_world.camera_x = 400
        with patch('pico2d.load_image') as load:
            for direction in (-1, 1):
                sprite.draw_body(HOP_BOUNDS[0], 820, 144, direction)
                args = load.return_value.clip_composite_draw.call_args.args
                self.assertEqual(args[5], 'h' if direction < 0 else '')
                self.assertEqual(args[6], 420)
                self.assertAlmostEqual(args[7] - args[9] / 2 + 2 * SCALE, 144)
                self.assertAlmostEqual(args[9], 158 * SCALE)
            load.assert_called_once()

    def test_death_plays_last_frame_without_looping_then_is_removed(self):
        sprite = Mock()
        death = FrogDeath(sprite, 820, 200, -1)
        game_world.add_object(death, game_world.EFFECTS)
        death.elapsed = DEATH_DURATION - .01
        death.draw()
        self.assertEqual(sprite.draw_body.call_args.args[0], DEATH_BOUNDS[-1])
        death.update(.02)
        self.assertNotIn(death, game_world.objects(game_world.EFFECTS))
