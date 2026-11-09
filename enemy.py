"""오른쪽에 고정된 채 상하 왕복하며 연사하는 테스트 적."""

import pico2d
import game_world
from bullet import Bullet


class TestEnemy:
    WIDTH = 144
    HEIGHT = 112
    MAX_HP = 30
    FIRE_INTERVAL = 0.35
    MOVE_SPEED = 90.0
    team = 'enemy'

    def __init__(self, world_width, world_height, ground_y):
        self.world_width = world_width
        self.x = world_width - self.WIDTH / 2 - 24
        self.min_y = ground_y + self.HEIGHT / 2
        self.max_y = world_height - self.HEIGHT / 2 - 100
        self.y = self.min_y
        self.phase = 0.0
        self.hp = self.MAX_HP
        self.fire_timer = 0.0

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            game_world.remove_object(self)

    def update(self, dt):
        if self.hp <= 0:
            return
        span = self.max_y - self.min_y
        self.phase = (self.phase + self.MOVE_SPEED * max(0, dt)) % (2 * span)
        self.y = self.min_y + span - abs(span - self.phase)
        self.fire_timer -= max(0, dt)
        if self.fire_timer <= 0:
            # 낮은 총구를 사용해 바닥의 플레이어에게도 탄이 도달하게 한다.
            x = self.x - self.WIDTH / 2 - Bullet.WIDTH / 2
            y = self.y - self.HEIGHT / 2 + 28
            game_world.add_object(Bullet(x, y, -1, self.team, self.world_width),
                                  game_world.PROJECTILES)
            self.fire_timer = self.FIRE_INTERVAL

    def draw(self):
        pico2d.draw_rectangle(*self.get_bb(), 150, 60, 80)
        pico2d.draw_rectangle(self.x - 45, self.y + 25, self.x - 25,
                              self.y + 45, 150, 60, 80, filled=True)
        left, _, right, top = self.get_bb()
        pico2d.draw_rectangle(left, top + 8,
                              left + (right - left) * self.hp / self.MAX_HP,
                              top + 14, 180, 40, 40, filled=True)
