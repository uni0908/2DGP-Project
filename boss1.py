"""보스1 전용 행동과 공격 패턴."""

import random

import pico2d
import game_world
from bullet import Bullet
from enemy import TestEnemy


class Boss1(TestEnemy):
    NAME = '보스1'
    BARRAGE_ATTACK_NAME = '탄막 공격'
    NORMAL_ATTACK_NAME = '일반 공격'
    BARRAGE_HEIGHTS = (8, 24, 40, 56, 72, 88)
    REST_HEIGHT = TestEnemy.HEIGHT / 2
    FIRE_INTERVAL = 0.45
    VOLLEYS_PER_BURST = 6
    PHASE_DURATIONS = {'attack': FIRE_INTERVAL * VOLLEYS_PER_BURST, 'rest': 4.0}
    BULLET_SPEED = 200.0
    REST_MIN_HEIGHT = 72
    REST_MAX_HEIGHT = 152
    REST_INTERVAL_RANGE = (0.08, 0.14)
    REST_BULLET_SPEED = 300.0

    def __init__(self, world_width, world_height, ground_y, rng=None):
        super().__init__(world_width, world_height, ground_y)
        self.ground_y = ground_y
        self.y = ground_y + self.HEIGHT / 2
        self.state = 'attack'
        self.state_time = 0.0
        self.fire_timer = 0.0
        self.volley_index = 0
        self.burst_shots = 0
        self.rest_shots = 0
        self.rng = rng if rng is not None else random.Random()

    @property
    def body_height(self):
        return self.REST_HEIGHT if self.state == 'rest' else self.HEIGHT

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.ground_y,
                self.x + self.WIDTH / 2, self.ground_y + self.body_height)

    def advance_phase(self):
        self.state = 'rest' if self.state == 'attack' else 'attack'
        self.y = self.ground_y + self.body_height / 2
        self.state_time = 0.0
        self.fire_timer = 0.0
        if self.state == 'attack':
            self.burst_shots = 0
        elif self.state == 'rest':
            self.rest_shots = 0

    def fire_volley(self):
        self.fire_rows(self.BARRAGE_HEIGHTS, self.BULLET_SPEED)
        self.volley_index += 1

    def fire_rest_volley(self):
        height = self.rng.uniform(self.REST_MIN_HEIGHT, self.REST_MAX_HEIGHT)
        self.fire_rows((height,), self.REST_BULLET_SPEED)
        self.rest_shots += 1

    def fire_rows(self, heights, speed):
        for height in heights:
            bullet = Bullet(self.x - self.WIDTH / 2 - Bullet.WIDTH / 2,
                            self.ground_y + height, -1, self.team,
                            self.world_width)
            bullet.HEIGHT = 14
            bullet.speed = speed
            game_world.add_object(bullet, game_world.PROJECTILES)

    def update(self, dt):
        if self.hp <= 0:
            return
        remaining = max(0, dt)
        while remaining > 0:
            duration = self.PHASE_DURATIONS[self.state]
            step = min(remaining, duration - self.state_time)
            if self.state == 'attack':
                self.fire_timer -= step
                while self.fire_timer <= 0 and self.burst_shots < self.VOLLEYS_PER_BURST:
                    self.fire_volley()
                    self.burst_shots += 1
                    self.fire_timer += self.FIRE_INTERVAL
            elif self.state == 'rest':
                self.fire_timer -= step
                while self.fire_timer <= 0:
                    self.fire_rest_volley()
                    self.fire_timer += self.rng.uniform(*self.REST_INTERVAL_RANGE)
            self.state_time += step
            remaining -= step
            if self.state_time >= duration:
                self.advance_phase()

    def draw(self):
        left, bottom, right, top = self.get_bb()
        color = (100, 75, 160) if self.state == 'rest' else (150, 60, 80)
        pico2d.draw_rectangle(left, bottom, right, top, *color)
        pico2d.draw_rectangle(left + 20, top - 30, left + 36, top - 14,
                              *color, filled=True)
        pico2d.draw_rectangle(left, top + 8,
                              left + self.WIDTH * self.hp / self.MAX_HP,
                              top + 14, 180, 40, 40, filled=True)
        if self.state == 'rest':
            # 낮게 웅크린 몸 주위의 안쪽 사각형으로 기를 모으는 상태를 표시한다.
            inset = 5 + int(self.state_time * 8) % 8
            pico2d.draw_rectangle(left - inset, bottom, right + inset, top + inset,
                                  160, 110, 210)
