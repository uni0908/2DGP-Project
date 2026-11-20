"""사용자 개구리 시트를 현재 행동·발 위치·혀 판정에 맞춰 표시한다."""

from pathlib import Path

import pico2d
import game_world


IMAGE_PATH = Path(__file__).resolve().parent / 'output' / 'basic-enemy' / 'outputs' / 'frog-animationsheet.png'
SHEET_HEIGHT = 836
DISPLAY_HEIGHT = 56.0
SCALE = DISPLAY_HEIGHT / 154
DEATH_FPS = 10
DEATH_DURATION = 6 / DEATH_FPS
HIDDEN_BOUNDS = (
    (67, 36, 243, 183), (383, 33, 557, 183), (697, 28, 875, 183),
    (1010, 33, 1188, 182), (1323, 42, 1500, 183), (1636, 42, 1816, 183),
)
HOP_BOUNDS = (
    (65, 244, 243, 398), (378, 263, 555, 398), (674, 233, 876, 388),
    (1001, 223, 1190, 352), (1324, 252, 1502, 396), (1636, 248, 1815, 398),
)
ATTACK_BODY = (57, 450, 228, 598)
RECOVER_BODY = (1624, 450, 1795, 598)
# 긴 혀 부분만 분리해 몸 배율과 독립적으로 현재 판정 길이에 맞춘다.
TONGUE_RECT = (1048, 836 - 564, 226, 32)
DEATH_BOUNDS = (
    (66, 657, 237, 809), (349, 676, 580, 812), (657, 638, 897, 815),
    (987, 656, 1200, 805), (1307, 660, 1511, 805), (1623, 662, 1813, 803),
)


def pose_for(frog):
    if frog.state == 'hidden':
        return HIDDEN_BOUNDS[int(frog.state_time * 6) % len(HIDDEN_BOUNDS)]
    if frog.state == 'hop':
        index = 2 if frog.velocity_y > 80 else 4 if frog.velocity_y < -80 else 3
        return HOP_BOUNDS[index]
    if frog.state == 'windup':
        return HOP_BOUNDS[1]
    if frog.state == 'tongue':
        return ATTACK_BODY
    if frog.state == 'recover':
        return RECOVER_BODY
    return HOP_BOUNDS[5 if frog.state_time < .12 else 0]


class FrogSprite:
    def __init__(self):
        self.image = None

    def image_ready(self):
        if self.image is None:
            self.image = pico2d.load_image(str(IMAGE_PATH))
        return self.image

    def draw_body(self, bounds, x, bottom, direction, baseline=None):
        left, top, right, base = bounds
        width, height = right - left + 4, base - top + 4
        baseline = base if baseline is None else baseline
        self.image_ready().clip_composite_draw(
            left - 2, SHEET_HEIGHT - base - 2, width, height,
            0, 'h' if direction < 0 else '', game_world.screen_x(x),
            bottom + (baseline - top + 2 - height / 2) * SCALE,
            width * SCALE, height * SCALE)

    def draw(self, frog):
        direction = (frog.attack_direction if frog.state in ('windup', 'tongue', 'recover')
                     else frog.direction)
        self.draw_body(pose_for(frog), frog.x, frog.bottom, direction)
        bounds = frog.tongue_bb()
        if bounds is not None:
            left, bottom, right, top = bounds
            self.image_ready().clip_composite_draw(
                *TONGUE_RECT, 0, 'h' if direction < 0 else '',
                game_world.screen_x((left + right) / 2), (bottom + top) / 2,
                right - left, top - bottom)


class FrogDeath:
    def __init__(self, sprite, x, bottom, direction):
        self.sprite, self.x, self.bottom, self.direction = sprite, x, bottom, direction
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += max(0, dt)
        if self.elapsed >= DEATH_DURATION:
            game_world.remove_object(self)

    def draw(self):
        index = min(int(self.elapsed * DEATH_FPS), len(DEATH_BOUNDS) - 1)
        self.sprite.draw_body(DEATH_BOUNDS[index], self.x, self.bottom, self.direction, baseline=809)
