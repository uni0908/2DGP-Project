"""맵 끝에 고정 배치하는 고양이 폭탄 로봇 프로토타입."""

import pico2d
import game_world
from enemy_bomb import ArcBomb


class CatRobot:
    WIDTH, HEIGHT = 96, 112
    MAX_HP = 50
    ACTIVE_DISTANCE = 600
    FIRST_SHOT_DELAY = 0.8
    FIRE_INTERVAL = 2.4
    CHARGE_TIME = 0.45
    team = 'enemy'

    def __init__(self, x, player, ground_y):
        self.x, self.player, self.ground_y = x, player, ground_y
        self.hp = self.MAX_HP
        self.fire_timer = self.FIRST_SHOT_DELAY
        self.engaged = False

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.ground_y,
                self.x + self.WIDTH / 2, self.ground_y + self.HEIGHT)

    def take_damage(self, amount):
        if self.hp <= 0 or amount <= 0:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            game_world.remove_object(self)

    def update(self, dt):
        if self.hp <= 0 or self.player.hp <= 0:
            return
        self.engaged = abs(self.player.x - self.x) <= self.ACTIVE_DISTANCE
        if not self.engaged:
            self.fire_timer = self.FIRST_SHOT_DELAY
            return
        self.fire_timer -= max(0, dt)
        while self.fire_timer <= 0:
            direction = -1 if self.player.x < self.x else 1
            bomb = ArcBomb(self.x + direction * (self.WIDTH / 2 + ArcBomb.WIDTH / 2 + 4),
                           self.ground_y + 66, self.player.x, self.player, self.ground_y)
            game_world.add_object(bomb, game_world.PROJECTILES)
            self.fire_timer += self.FIRE_INTERVAL

    def draw(self):
        left, bottom, right, top = game_world.screen_bb(self.get_bb())
        x = game_world.screen_x(self.x)
        direction = -1 if self.player.x < self.x else 1
        pico2d.draw_rectangle(left + 8, bottom + 14, right - 8, bottom + 80,
                              100, 110, 130, filled=True)
        for foot_x in (left + 5, right - 31):
            pico2d.draw_rectangle(foot_x, bottom, foot_x + 26, bottom + 18,
                                  55, 65, 85, filled=True)
        cannon_x = x + direction * (self.WIDTH / 2 + 12)
        cannon_color = ((225, 140, 45) if self.engaged and self.fire_timer <= self.CHARGE_TIME
                        else (65, 75, 95))
        pico2d.draw_rectangle(min(x, cannon_x), bottom + 58,
                              max(x, cannon_x), bottom + 74, *cannon_color, filled=True)
        # 로봇 위 고양이 얼굴과 귀. 정식 에셋 적용 전 임시 도형이다.
        pico2d.draw_rectangle(x - 18, bottom + 82, x + 18, bottom + 106,
                              205, 145, 85, filled=True)
        for ear_x in (x - 18, x + 10):
            pico2d.draw_rectangle(ear_x, bottom + 104, ear_x + 8, top,
                                  205, 145, 85, filled=True)
        for eye_x in (x - 10, x + 5):
            pico2d.draw_rectangle(eye_x, bottom + 94, eye_x + 5, bottom + 99,
                                  35, 35, 45, filled=True)
        pico2d.draw_rectangle(left, top + 10, right, top + 16, 75, 75, 75, filled=True)
        pico2d.draw_rectangle(left, top + 10, left + self.WIDTH * self.hp / self.MAX_HP,
                              top + 16, 200, 65, 50, filled=True)
