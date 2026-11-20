"""사용자 문어 v2 시트의 이동·죽기 프레임. 원본 픽셀은 변경하지 않는다."""

from pathlib import Path

import pico2d
import game_world


IMAGE_PATH = Path(__file__).resolve().parent / 'output' / 'basic-enemy' / 'outputs' / 'octopus_v2.png'
SHEET_HEIGHT = 724
DISPLAY_HEIGHT = 96.0
SCALE = DISPLAY_HEIGHT / 329
MOVE_FPS = 8
DEATH_FPS = 8
# 왼쪽 위 기준 실제 불투명 그림 범위. 죽기 행은 균등 격자가 아니다.
MOVE_BOUNDS = (
    (18, 22, 259, 351), (286, 74, 536, 347),
    (550, 11, 804, 347), (824, 72, 1077, 349),
    (1094, 11, 1351, 352), (1376, 82, 1625, 341),
    (1638, 37, 1895, 352), (1920, 28, 2157, 348),
)
DEATH_BOUNDS = (
    (38, 399, 285, 706), (315, 469, 643, 699),
    (674, 390, 1009, 707), (1042, 398, 1391, 699),
    (1448, 416, 1769, 677), (1825, 428, 2098, 665),
)
DEATH_DURATION = len(DEATH_BOUNDS) / DEATH_FPS


def frame_bounds(elapsed, dying=False):
    frames = DEATH_BOUNDS if dying else MOVE_BOUNDS
    index = int(max(0, elapsed) * (DEATH_FPS if dying else MOVE_FPS))
    return frames[min(index, len(frames) - 1) if dying else index % len(frames)]


class OctopusSprite:
    def __init__(self):
        self.image = None

    def draw(self, x, bottom, elapsed, dying=False):
        if self.image is None:
            self.image = pico2d.load_image(str(IMAGE_PATH))
        left, top, right, base = frame_bounds(elapsed, dying)
        # 선 가장자리 여유 2px. 모든 프레임은 같은 배율로 꿈틀거림을 유지한다.
        clip_left, clip_top = left - 2, top - 2
        width, height = right - left + 4, base - top + 4
        baseline = 706 if dying else base
        self.image.clip_draw(clip_left, SHEET_HEIGHT - clip_top - height, width, height,
                             game_world.screen_x(x),
                             bottom + (baseline - clip_top - height / 2) * SCALE,
                             width * SCALE, height * SCALE)


class OctopusDeath:
    def __init__(self, sprite, x, bottom):
        self.sprite, self.x, self.bottom = sprite, x, bottom
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += max(0, dt)
        if self.elapsed >= DEATH_DURATION:
            game_world.remove_object(self)

    def draw(self):
        self.sprite.draw(self.x, self.bottom, self.elapsed, dying=True)
