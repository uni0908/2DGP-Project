"""맵 끝에 고정 배치하는 고양이 폭탄 로봇 프로토타입."""

import pico2d
import game_world
from enemy_bomb import ArcBomb
from cat_robot_sprite import CatRobotSprite, CatRobotDeath, FIRE_DURATION


class CatRobot:
    WIDTH, HEIGHT = 96, 112
    MAX_HP = 100
    ACTIVE_DISTANCE = 600
    FIRST_SHOT_DELAY = 0.8
    FIRE_INTERVAL = 2.4
    CHARGE_TIME = 0.45
    HIT_DURATION = 0.03
    HIT_BLINK_INTERVAL = 0.03
    team = 'enemy'

    def __init__(self, x, player, ground_y, view_width=960):
        self.x, self.player, self.ground_y = x, player, ground_y
        self.hp = self.MAX_HP
        self.fire_timer = self.FIRST_SHOT_DELAY
        self.engaged = False
        self.view_width = view_width
        self.sprite = CatRobotSprite()
        self.animation_time = 0.0
        self.shot_elapsed = FIRE_DURATION
        self.shot_direction = -1
        self.hit_elapsed = self.HIT_DURATION

    @property
    def bullet_vulnerable(self):
        left, _, right, _ = self.get_bb()
        return (self.hp > 0 and right > game_world.camera_x
                and left < game_world.camera_x + self.view_width)

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.ground_y,
                self.x + self.WIDTH / 2, self.ground_y + self.HEIGHT)

    def take_damage(self, amount):
        if not self.bullet_vulnerable or amount <= 0:
            return
        self.hp = max(0, self.hp - amount)
        self.hit_elapsed = 0.0
        if self.hp == 0:
            game_world.remove_object(self)
            direction = (self.shot_direction if self.shot_elapsed < FIRE_DURATION
                         else -1 if self.player.x < self.x else 1)
            game_world.add_object(CatRobotDeath(self.sprite, self.x,
                                               self.ground_y + self.HEIGHT / 2, direction),
                                  game_world.EFFECTS)

    def update(self, dt):
        if self.hp <= 0 or self.player.hp <= 0:
            return
        self.animation_time += max(0, dt)
        self.shot_elapsed += max(0, dt)
        self.hit_elapsed += max(0, dt)
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
            self.shot_elapsed = 0.0
            self.shot_direction = direction
            self.fire_timer += self.FIRE_INTERVAL

    def draw(self):
        left, bottom, right, top = game_world.screen_bb(self.get_bb())
        firing = self.shot_elapsed < FIRE_DURATION
        direction = self.shot_direction if firing else -1 if self.player.x < self.x else 1
        flash = (self.hit_elapsed < self.HIT_DURATION
                 and int(self.hit_elapsed / self.HIT_BLINK_INTERVAL) % 2 == 0)
        drawn_top = self.sprite.draw('fire' if firing else 'idle',
                                     self.shot_elapsed if firing else self.animation_time,
                                     self.x, bottom, direction, flash=flash)
        top = max(top, drawn_top)
        if self.engaged and self.fire_timer <= self.CHARGE_TIME:
            muzzle_x = game_world.screen_x(self.x + direction * 60)
            pico2d.draw_rectangle(muzzle_x - 4, bottom + 62, muzzle_x + 4, bottom + 70,
                                  235, 155, 45, filled=True)
        pico2d.draw_rectangle(left, top + 10, right, top + 16, 75, 75, 75, filled=True)
        pico2d.draw_rectangle(left, top + 10, left + self.WIDTH * self.hp / self.MAX_HP,
                              top + 16, 200, 65, 50, filled=True)
