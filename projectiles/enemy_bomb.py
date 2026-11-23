"""발사 순간의 플레이어 위치로 날아가는 적 폭탄과 짧은 폭발."""

import pico2d
from core import game_world
from items.doodle import overlaps


class BombExplosion:
    RADIUS = 56
    DURATION = 0.3

    def __init__(self, x, y, player):
        self.x, self.y, self.player = x, y, player
        self.elapsed = 0.0
        self.active = True

    def update(self, dt):
        if not self.active:
            return
        left, bottom, right, top = self.player.get_bb()
        nearest_x = max(left, min(self.x, right))
        nearest_y = max(bottom, min(self.y, top))
        if (self.x - nearest_x) ** 2 + (self.y - nearest_y) ** 2 <= self.RADIUS ** 2:
            self.player.take_damage(1)
        self.elapsed += max(0, dt)
        if self.elapsed >= self.DURATION:
            self.active = False
            game_world.remove_object(self)

    def draw(self):
        x = game_world.screen_x(self.x)
        radius = self.RADIUS * (1 - .4 * self.elapsed / self.DURATION)
        pico2d.draw_rectangle(x - radius, self.y - radius, x + radius, self.y + radius,
                              235, 125, 40)
        pico2d.draw_rectangle(x - radius / 2, self.y - radius / 2,
                              x + radius / 2, self.y + radius / 2,
                              250, 195, 70, filled=True)


class ArcBomb:
    WIDTH = HEIGHT = 20
    GRAVITY = 950.0
    FLIGHT_TIME = 1.3
    team = 'enemy'

    def __init__(self, x, y, target_x, player, ground_y):
        self.x, self.y = x, y
        self.start_x, self.start_y = x, y
        self.target_x = target_x
        self.target_y = ground_y + self.HEIGHT / 2
        self.ground_y, self.player = ground_y, player
        self.velocity_x = (target_x - x) / self.FLIGHT_TIME
        self.velocity_y = ((self.target_y - y) / self.FLIGHT_TIME
                           + .5 * self.GRAVITY * self.FLIGHT_TIME)
        self.age = 0.0
        self.active = True

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    def explode(self):
        if not self.active:
            return
        self.active = False
        game_world.remove_object(self)
        game_world.add_object(BombExplosion(self.x, self.y, self.player), game_world.EFFECTS)

    def update(self, dt):
        if not self.active or self.player.hp <= 0:
            return
        remaining = max(0, dt)
        while remaining > 0 and self.active:
            step = min(remaining, 1 / 120)
            self.age = min(self.FLIGHT_TIME, self.age + step)
            self.x = self.start_x + self.velocity_x * self.age
            self.y = self.start_y + self.velocity_y * self.age - .5 * self.GRAVITY * self.age ** 2
            if self.age >= self.FLIGHT_TIME:
                self.x, self.y = self.target_x, self.target_y
                self.explode()
            elif overlaps(self.get_bb(), self.player.get_bb()):
                self.explode()
            remaining -= step

    def draw(self):
        # 착탄 범위를 바닥에 미리 표시하고 발사 이후에는 위치를 바꾸지 않는다.
        target = game_world.screen_x(self.target_x)
        pico2d.draw_rectangle(target - BombExplosion.RADIUS, self.ground_y + 1,
                              target + BombExplosion.RADIUS, self.ground_y + 4,
                              200, 85, 45, filled=True)
        pico2d.draw_rectangle(target - 3, self.ground_y + 1, target + 3,
                              self.ground_y + 12, 200, 85, 45, filled=True)
        left, bottom, right, top = game_world.screen_bb(self.get_bb())
        pico2d.draw_rectangle(left, bottom, right, top, 65, 60, 80, filled=True)
        pico2d.draw_rectangle(left + 8, top, left + 12, top + 6,
                              240, 145, 45, filled=True)
