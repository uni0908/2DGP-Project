"""Animation selection and rendering for the boss1 asset package."""

import json
from pathlib import Path

import pico2d
import game_world


ASSET_DIR = Path(__file__).resolve().parent / 'output' / 'boss1-sprites-v1'
DATA = json.loads((ASSET_DIR / 'boss1-animations.json').read_text(encoding='utf-8-sig'))


def animation_frame(name, elapsed):
    animation = DATA['animations'][name]
    index = int(max(0, elapsed) * animation['fps'])
    frames = animation['frames']
    index = index % len(frames) if animation['loop'] else min(index, len(frames) - 1)
    return DATA['frames'][frames[index]]


def animation_for(boss):
    if boss.state == 'normal_parry':
        return 'normal_fire' if boss.state_time < .18 else 'idle'
    if boss.state == 'homing_parry':
        return 'homing_launch' if boss.state_time < .7 else 'idle'
    return {
        'attack': 'barrage_fire', 'rest': 'rest_upper_fire',
        'normal_burst': 'normal_fire', 'normal_pause': 'idle',
        'homing_launch': 'homing_launch', 'homing_wait': 'idle',
        'homing_recover': 'recover', 'laser_charge': 'laser_charge',
        'laser_sweep': 'laser_hold', 'laser_recover': 'recover',
    }[boss.state]


class BossSprite:
    def __init__(self):
        self.images = {}

    def image(self, name):
        if name not in self.images:
            self.images[name] = pico2d.load_image(str(ASSET_DIR / name))
        return self.images[name]

    def draw_body(self, name, elapsed, bounds):
        frame = animation_frame(name, elapsed)
        left, bottom, right, top = bounds
        reference = DATA['frames']['idle_00']['bounds_top_left']
        scale = min((right - left) / (reference[2] - reference[0]),
                    (top - bottom) / (reference[3] - reference[1]))
        width, height = DATA['cell_size']
        center_x = (left + right) / 2 + (width / 2 - (reference[0] + reference[2]) / 2) * scale
        center_y = bottom + (reference[3] - height / 2) * scale
        self.image(frame['sheet']).clip_draw(
            *frame['rect_pico2d'], game_world.screen_x(center_x), center_y,
            width * scale, height * scale)
