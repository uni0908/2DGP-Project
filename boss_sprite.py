"""Animation selection and rendering for the boss1 asset package."""

import json
from pathlib import Path

import pico2d
import game_world


ASSET_DIR = Path(__file__).resolve().parent / 'output' / 'boss1-sprites-v2'
DATA = json.loads((ASSET_DIR / 'boss1-animations.json').read_text(encoding='utf-8-sig'))


def animation_frame(name, elapsed):
    animation = DATA['animations'][name]
    index = int(max(0, elapsed) * animation['fps'])
    frames = animation['frames']
    index = index % len(frames) if animation['loop'] else min(index, len(frames) - 1)
    return DATA['frames'][frames[index]]


def rest_pose(boss):
    enter_duration = DATA['animations']['crouch_enter']['duration_seconds']
    exit_start = boss.PHASE_DURATIONS['rest'] - DATA['animations']['crouch_exit']['duration_seconds']
    if boss.state_time < enter_duration:
        return 'crouch_enter', boss.state_time
    if boss.state_time >= exit_start:
        return 'crouch_exit', boss.state_time - exit_start
    return 'crouch_idle', boss.state_time - enter_duration


def animation_for(boss):
    if boss.state == 'rest':
        return rest_pose(boss)[0]
    if boss.state == 'normal_parry':
        return 'normal_fire' if boss.state_time < .18 else 'idle'
    if boss.state == 'homing_parry':
        return 'homing_launch' if boss.state_time < .7 else 'idle'
    return {
        'attack': 'barrage_fire',
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
        baseline = frame['bounds_top_left'][3] if name.startswith('crouch_') else reference[3]
        center_y = bottom + (baseline - height / 2) * scale
        self.image(frame['sheet']).clip_draw(
            *frame['rect_pico2d'], game_world.screen_x(center_x), center_y,
            width * scale, height * scale)

    def draw_effect(self, name, elapsed, x, y, width, height, angle=0):
        frame = animation_frame(name, elapsed)
        animation = DATA['animations'][name]
        rectangles = [DATA['frames'][key]['bounds_top_left'] for key in animation['frames']]
        left = min(rect[0] for rect in rectangles)
        top = min(rect[1] for rect in rectangles)
        right = max(rect[2] for rect in rectangles)
        bottom = max(rect[3] for rect in rectangles)
        if name == 'laser_tile':
            # The third tile includes a stray mark below the actual beam.
            left, top, right, bottom = 24, 105, 229, 144
        cell_x, cell_y, _, cell_h = frame['rect_pico2d']
        self.image(frame['sheet']).clip_composite_draw(
            cell_x + left, cell_y + cell_h - bottom, right - left, bottom - top,
            angle, '', game_world.screen_x(x), y, width, height)


class BossDeath:
    def __init__(self, sprite, bounds):
        self.sprite = sprite
        self.bounds = bounds
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += max(0, dt)

    def draw(self):
        self.sprite.draw_body('death', self.elapsed, self.bounds)


class BossEffect:
    def __init__(self, sprite, name, x, y, width, height):
        self.sprite, self.name = sprite, name
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += max(0, dt)
        animation = DATA['animations'][self.name]
        if self.elapsed >= len(animation['frames']) / animation['fps']:
            game_world.remove_object(self)

    def draw(self):
        self.sprite.draw_effect(self.name, self.elapsed, self.x, self.y,
                                self.width, self.height)
