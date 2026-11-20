"""고양이 로봇 시트의 1·2·4행만 사용한다. 3행은 미적용이다."""

from pathlib import Path

import pico2d
import game_world


IMAGE_PATH = Path(__file__).resolve().parent / 'output' / 'basic-enemy' / 'outputs' / 'robotcat-animationsheet.png'
SHEET_HEIGHT = 887
DISPLAY_HEIGHT = 112.0
SCALE = DISPLAY_HEIGHT / 172
IDLE_FPS = 6
FIRE_FPS = 16
FIRE_DURATION = 8 / FIRE_FPS
DEATH_FPS = 12
DEATH_DURATION = 7 / DEATH_FPS
ORIGINS = (0, 222, 444, 665, 887, 1109, 1330, 1552)
IDLE_BOUNDS = (
    (29, 25, 214, 197), (253, 20, 436, 195), (474, 30, 659, 197),
    (697, 23, 879, 196), (919, 21, 1101, 195), (1140, 32, 1323, 197),
    (1363, 25, 1545, 197), (1585, 25, 1766, 196),
)
FIRE_BOUNDS = (
    (31, 249, 215, 420), (241, 267, 446, 415), (461, 276, 673, 414),
    (708, 243, 876, 425), (939, 229, 1092, 434), (1154, 242, 1321, 425),
    (1363, 250, 1545, 417), (1584, 250, 1766, 420),
)
# 4행의 첫 칸은 비어 있으므로 두 번째 칸부터 사용한다.
DEATH_BOUNDS = (
    (249, 699, 420, 849), (454, 680, 656, 867), (670, 667, 884, 877),
    (901, 680, 1099, 867), (1125, 693, 1306, 857),
    (1358, 706, 1523, 850), (1596, 721, 1732, 848),
)


def frame_for(name, elapsed):
    frames, fps = {'idle': (IDLE_BOUNDS, IDLE_FPS),
                   'fire': (FIRE_BOUNDS, FIRE_FPS),
                   'death': (DEATH_BOUNDS, DEATH_FPS)}[name]
    index = int(max(0, elapsed) * fps)
    index = index % len(frames) if name == 'idle' else min(index, len(frames) - 1)
    return index, frames[index]


class CatRobotSprite:
    def __init__(self):
        self.image = None

    def draw(self, name, elapsed, x, baseline_y, direction):
        if self.image is None:
            self.image = pico2d.load_image(str(IMAGE_PATH))
        index, (left, top, right, base) = frame_for(name, elapsed)
        origin = ORIGINS[index + 1 if name == 'death' else index]
        source_x = origin + 110  # 포신을 제외한 몸 중심을 고정한다.
        source_y = 776 if name == 'death' else base
        width, height = right - left + 4, base - top + 4
        center_x = x + direction * ((left + right) / 2 - source_x) * SCALE
        center_y = baseline_y + (source_y - (top + base) / 2) * SCALE
        self.image.clip_composite_draw(
            left - 2, SHEET_HEIGHT - base - 2, width, height, 0,
            'h' if direction < 0 else '', game_world.screen_x(center_x), center_y,
            width * SCALE, height * SCALE)
        return baseline_y + (source_y - top) * SCALE


class CatRobotDeath:
    def __init__(self, sprite, x, y, direction):
        self.sprite, self.x, self.y, self.direction = sprite, x, y, direction
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += max(0, dt)
        if self.elapsed >= DEATH_DURATION:
            game_world.remove_object(self)

    def draw(self):
        self.sprite.draw('death', self.elapsed, self.x, self.y, self.direction)
