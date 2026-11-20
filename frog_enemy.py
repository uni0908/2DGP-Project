"""통나무 배치 전 고정 구간을 왕복하는 개구리 프로토타입."""

import pico2d
import game_world


class FrogEnemy:
    WIDTH, HEIGHT = 36, 44
    HIDDEN_HEIGHT = 16
    MAX_HP = 1
    ACTIVE_DISTANCE = 240
    MOVE_SPEED = 120.0
    JUMP_SPEED = 300.0
    GRAVITY = 1200.0
    HOP_PAUSE = 0.4
    team = 'enemy'

    def __init__(self, patrol_left, patrol_right, player, ground_y):
        self.patrol_left, self.patrol_right = patrol_left, patrol_right
        self.player = player
        self.ground_y = ground_y
        self.x = (patrol_left + patrol_right) / 2
        self.bottom = ground_y
        self.hp = self.MAX_HP
        self.direction = -1
        self.velocity_y = 0.0
        self.state = 'hidden'
        self.state_time = 0.0

    @property
    def bullet_vulnerable(self):
        return self.state != 'hidden'

    def get_bb(self):
        height = self.HIDDEN_HEIGHT if self.state == 'hidden' else self.HEIGHT
        return (self.x - self.WIDTH / 2, self.bottom,
                self.x + self.WIDTH / 2, self.bottom + height)

    def take_damage(self, amount):
        if not self.bullet_vulnerable or self.hp <= 0 or amount <= 0:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            game_world.remove_object(self)

    def set_state(self, state):
        self.state, self.state_time = state, 0.0

    def update(self, dt):
        if self.hp <= 0 or self.player.hp <= 0:
            return
        # 독립 호출에서도 착지와 구간 반전을 건너뛰지 않는다.
        remaining = max(0, dt)
        while remaining > 0:
            step = min(remaining, 1 / 120)
            self.update_step(step)
            remaining -= step

    def update_step(self, dt):
        nearby = abs(self.player.x - self.x) <= self.ACTIVE_DISTANCE
        self.state_time += dt
        if self.state == 'hop':
            self.x += self.direction * self.MOVE_SPEED * dt
            if self.x <= self.patrol_left:
                self.x, self.direction = self.patrol_left, 1
            elif self.x >= self.patrol_right:
                self.x, self.direction = self.patrol_right, -1
            self.bottom += self.velocity_y * dt - .5 * self.GRAVITY * dt * dt
            self.velocity_y -= self.GRAVITY * dt
            if self.bottom <= self.ground_y:
                self.bottom, self.velocity_y = self.ground_y, 0.0
                self.set_state('idle' if nearby else 'hidden')
            return
        if not nearby:
            self.set_state('hidden')
        elif self.state == 'hidden':
            self.set_state('idle')
        elif self.state_time >= self.HOP_PAUSE:
            self.velocity_y = self.JUMP_SPEED
            self.set_state('hop')

    def draw(self):
        left, bottom, right, top = game_world.screen_bb(self.get_bb())
        color = (75, 115, 70) if self.state == 'hidden' else (75, 175, 85)
        pico2d.draw_rectangle(left, bottom, right, top, *color, filled=True)
        # 몸의 낮은 모양과 올라온 눈으로 잠복/활성 상태를 구분한다.
        for x in (left + 5, right - 11):
            pico2d.draw_rectangle(x, top - 8, x + 6, top - 2, 25, 40, 25, filled=True)
