"""횡스크롤 문어의 하강·지상 추적과 화면 기준 등장."""

import random
from pathlib import Path

import pico2d
import game_world


class OctopusEnemy:
    WIDTH, HEIGHT = 48, 88
    IMAGE_PATH = Path(__file__).resolve().parent / 'output' / 'boss1-sprites-v1' / 'boss1-body.png'
    # JSON의 idle_00(첫 행·첫 열) bounds_top_left=(80, 16, 227, 227).
    # 시트 높이 2304에서 pico2d의 왼쪽 아래 기준으로 변환한 실제 그림 영역.
    FRAME_RECT = (80, 2077, 147, 211)
    DISPLAY_HEIGHT = 88
    MAX_HP = 3
    FALL_SPEED = 160.0
    MOVE_SPEED = 110.0
    team = 'enemy'

    def __init__(self, x, player, ground_y, world_height=540):
        self.x = x
        self.y = world_height + self.HEIGHT / 2
        self.player = player
        self.ground_y = ground_y
        self.hp = self.MAX_HP
        self.grounded = False
        self.image = None

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - max(0, amount))
        if self.hp == 0:
            game_world.remove_object(self)

    def update(self, dt):
        if self.hp <= 0 or self.player.hp <= 0:
            return
        dt = max(0, dt)
        if not self.grounded:
            floor = self.ground_y + self.HEIGHT / 2
            fall_time = max(0, (self.y - floor) / self.FALL_SPEED)
            self.y = max(floor, self.y - self.FALL_SPEED * dt)
            self.grounded = self.y <= floor
            dt = max(0, dt - fall_time)
        if self.grounded:
            distance = self.player.x - self.x
            self.x += max(-self.MOVE_SPEED * dt, min(distance, self.MOVE_SPEED * dt))
            self.x = max(self.WIDTH / 2,
                         min(self.x, self.player.world_width - self.WIDTH / 2))

    def draw(self):
        left, bottom, right, top = game_world.screen_bb(self.get_bb())
        if self.image is None:
            self.image = pico2d.load_image(str(self.IMAGE_PATH))
        width = self.FRAME_RECT[2] * self.DISPLAY_HEIGHT / self.FRAME_RECT[3]
        self.image.clip_draw(*self.FRAME_RECT, game_world.screen_x(self.x),
                             bottom + self.DISPLAY_HEIGHT / 2, width, self.DISPLAY_HEIGHT)
        pico2d.draw_rectangle(left, top + 6,
                              left + self.WIDTH * self.hp / self.MAX_HP,
                              top + 10, 180, 40, 40, filled=True)


class OctopusSpawner:
    SPAWN_INTERVAL = 3.0
    MAX_ALIVE = 4
    SCREEN_MARGIN = 64
    MIN_SPAWN_GAP = 160
    DESPAWN_MARGIN = 480

    def __init__(self, player, ground_y, screen_width=960, screen_height=540, rng=None):
        self.player = player
        self.ground_y = ground_y
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rng = rng if rng is not None else random.Random()
        self.timer = self.SPAWN_INTERVAL
        self.last_spawn_x = None

    def update(self, dt, camera_x):
        if self.player.hp <= 0:
            return
        enemies = [obj for obj in game_world.objects(game_world.ACTORS)
                   if isinstance(obj, OctopusEnemy) and obj.hp > 0]
        for enemy in enemies[:]:
            left, _, right, _ = enemy.get_bb()
            if (right < camera_x - self.DESPAWN_MARGIN
                    or left > camera_x + self.screen_width + self.DESPAWN_MARGIN):
                game_world.remove_object(enemy)
                enemies.remove(enemy)
        self.timer -= max(0, dt)
        if self.timer > 0:
            return
        # 상한에서 시간이 쌓여 빈자리가 생기자마자 몰려 나오는 것을 막는다.
        self.timer = self.SPAWN_INTERVAL
        if len(enemies) >= self.MAX_ALIVE:
            return
        low = camera_x + self.SCREEN_MARGIN
        high = camera_x + self.screen_width - self.SCREEN_MARGIN
        for _ in range(24):
            x = self.rng.uniform(low, high)
            if self.last_spawn_x is not None and abs(x - self.last_spawn_x) < self.MIN_SPAWN_GAP:
                continue
            if any(abs(x - enemy.x) < self.MIN_SPAWN_GAP for enemy in enemies):
                continue
            game_world.add_object(OctopusEnemy(x, self.player, self.ground_y,
                                               self.screen_height), game_world.ACTORS)
            self.last_spawn_x = x
            return
