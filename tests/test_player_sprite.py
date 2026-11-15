import unittest
from unittest.mock import Mock, patch

import pico2d
import game_world
import play_mode
from player import Player
from player_sprite import DATA, PlayerSprite


class PlayerSpriteTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.player = Player(300, 80, 960)

    def tearDown(self):
        game_world.clear()

    def test_movement_and_aim_states(self):
        player = self.player
        for keys, expected in (
                ((), 'idle_lowered'),
                ((pico2d.SDLK_a,), 'idle_horizontal'),
                ((pico2d.SDLK_a, pico2d.SDLK_UP), 'idle_up'),
                ((pico2d.SDLK_RIGHT,), 'run_lowered'),
                ((pico2d.SDLK_a, pico2d.SDLK_LEFT, pico2d.SDLK_UP), 'run_diagonal')):
            player.pressed_keys = set(keys)
            self.assertEqual(PlayerSprite.state(player), expected)
        player.grounded = False
        player.velocity_y = 100
        self.assertEqual(PlayerSprite.state(player), 'jump_rise_diagonal')
        player.velocity_y = -100
        self.assertEqual(PlayerSprite.state(player), 'fall_diagonal')

    def test_anchors_mirror_around_player_and_follow_camera(self):
        player = self.player
        player.pressed_keys.add(pico2d.SDLK_a)
        frame = player.sprite.current_frame(player)
        self.assertEqual(player.sprite.point(player, frame, frame['foot_anchor']), (300, 80))
        right = player.sprite.muzzle(player)
        player.facing = -1
        left = player.sprite.muzzle(player)
        self.assertAlmostEqual(right[0] + left[0], 600)
        self.assertEqual(right[1], left[1])
        image = Mock()
        game_world.camera_x = 150
        player.sprite.draw_frame(image, player, frame)
        args = image.clip_composite_draw.call_args.args
        self.assertEqual(args[5], 'h')
        self.assertAlmostEqual(args[6], 150)

    def test_death_finishes_even_after_boss_game_over(self):
        player = self.player
        player.take_damage(5)
        with patch.object(play_mode, 'player', player), patch.object(play_mode, 'game_over', True):
            play_mode.update(.01)
            play_mode.update(2)
        self.assertEqual(player.sprite.name, 'death')
        self.assertEqual(player.sprite.current_frame(player), DATA['animations']['death']['frames'][-1])

    def test_parry_and_effect_frames_render_without_loading_canvas(self):
        player = self.player
        player.sprite.image = Mock()
        player.sprite.effect_image = Mock()
        player.parry_timer = .12
        self.assertEqual(PlayerSprite.state(player), 'parry_attempt')
        player.sprite.draw(player)
        player.parry_feedback_timer = .75
        self.assertEqual(PlayerSprite.state(player), 'parry_success_launch')
        player.sprite.draw(player)
        self.assertEqual(player.sprite.effect_image.clip_composite_draw.call_count, 2)
