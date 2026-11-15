"""Frame selection and rendering for the generated player asset pack."""

import json
from pathlib import Path

import pico2d
import game_world


ASSET_DIR = Path(__file__).resolve().parent / 'output' / 'player-sprites-v1'
DATA = json.loads((ASSET_DIR / 'player-sprites.json').read_text(encoding='utf-8-sig'))
DISPLAY_HEIGHT = 80.0
RENDER_SCALE = DISPLAY_HEIGHT / DATA['render_reference']['standing_source_height']
CHARACTER_IMAGE = 'player-character-refined.png'


class PlayerSprite:
    def __init__(self):
        self.name = 'idle_lowered'
        self.elapsed = 0.0
        self.image = None
        self.effect_image = None

    def update(self, player, dt):
        name = self.state(player)
        if name != self.name:
            self.name, self.elapsed = name, 0.0
        else:
            self.elapsed += max(0.0, dt)

    @staticmethod
    def state(player):
        if player.hp <= 0:
            return 'death'
        if player.hurt_timer > 0:
            return 'hurt'
        if player.parry_feedback_timer > .65:
            return 'parry_success_launch'
        if player.parry_timer > 0:
            return 'parry_attempt'
        keys = player.pressed_keys
        moving = (pico2d.SDLK_RIGHT in keys) != (pico2d.SDLK_LEFT in keys)
        firing = pico2d.SDLK_a in keys
        aim = 'lowered'
        if firing:
            aim = ('diagonal' if moving else 'up') if pico2d.SDLK_UP in keys else 'horizontal'
        if player.crouching:
            return ('crouch_walk_' if moving else 'crouch_') + ('horizontal' if firing else 'lowered')
        if not player.grounded:
            return ('jump_rise_' if player.velocity_y > 0 else 'fall_') + aim
        return ('run_' if moving else 'idle_') + aim

    @staticmethod
    def frame(animation, elapsed):
        frames = animation['frames']
        total = sum(frame['duration_seconds'] for frame in frames)
        time = elapsed % total if animation['loop'] else min(elapsed, total)
        for frame in frames:
            time -= frame['duration_seconds']
            if time < 0:
                return frame
        return frames[-1]

    def current_frame(self, player):
        name = self.state(player)
        return self.frame(DATA['animations'][name], self.elapsed if name == self.name else 0)

    @staticmethod
    def point(player, frame, point):
        scale = RENDER_SCALE
        ax, ay = frame.get('foot_anchor', DATA['render_reference']['foot_anchor'])
        return (player.x + player.facing * (point[0] - ax) * scale,
                player.y - player.height / 2 + (ay - point[1]) * scale)

    def muzzle(self, player):
        if player.crouching and pico2d.SDLK_UP in player.pressed_keys:
            # No upward crouch pose exists; keep the existing shot origin.
            return None
        frame = self.current_frame(player)
        if frame.get('muzzle') is not None:
            return self.point(player, frame, frame['muzzle'])
        return None

    def draw_frame(self, image, player, frame):
        width, height = DATA['cell_size']
        center_x, center_y = self.point(player, frame, (width / 2, height / 2))
        scale = RENDER_SCALE
        image.clip_composite_draw(*frame['pico2d_clip_rect'], 0,
                                  'h' if player.facing < 0 else '',
                                  game_world.screen_x(center_x), center_y,
                                  width * scale, height * scale)

    def draw(self, player):
        # Load textures only with a live canvas, never during physics tests.
        if self.image is None:
            self.image = pico2d.load_image(str(ASSET_DIR / CHARACTER_IMAGE))
            self.effect_image = pico2d.load_image(str(ASSET_DIR / DATA['effect_image']))
        self.draw_frame(self.image, player, self.current_frame(player))
        effect = None
        elapsed = 0.0
        if player.parry_feedback_timer > .65:
            effect = 'parry_success_flash'
            elapsed = .8 - player.parry_feedback_timer
        elif player.parry_timer > 0:
            effect = 'parry_attempt_trail'
            elapsed = player.PARRY_WINDOW - player.parry_timer
        if effect:
            animation = DATA['effects'][effect]
            frame = self.frame(animation, elapsed)
            body_frame = self.current_frame(player)
            scale = RENDER_SCALE
            attach_x, attach_y = self.point(player, body_frame, frame['character_attachment'])
            ax, ay = frame['attachment_anchor']
            width, height = DATA['cell_size']
            self.effect_image.clip_composite_draw(
                *frame['pico2d_clip_rect'], 0, 'h' if player.facing < 0 else '',
                game_world.screen_x(attach_x + player.facing * (width / 2 - ax) * scale),
                attach_y + (ay - height / 2) * scale, width * scale, height * scale)
