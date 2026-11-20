"""통나무 배치 전 고정 구간을 왕복하는 개구리 프로토타입."""

import math

import game_world
from doodle import overlaps
from frog_sprite import FrogSprite, FrogDeath


class FrogEnemy:
    WIDTH, HEIGHT = 36, 44
    HIDDEN_HEIGHT = 16
    MAX_HP = 1
    ACTIVE_DISTANCE = 240
    MOVE_SPEED = 120.0
    GRAVITY = 1200.0
    JUMP_HEIGHT = 80.0  # 주인공의 서 있는 표시 높이만큼 도약한다.
    JUMP_SPEED = math.sqrt(2 * GRAVITY * JUMP_HEIGHT)
    WAKE_PROTECTION = 0.5
    HOP_PAUSE = 0.4
    ATTACK_DISTANCE = 180
    WINDUP_TIME = 0.4
    TONGUE_TIME = 0.3
    RECOVER_TIME = 0.45
    ATTACK_COOLDOWN = 1.4
    TONGUE_LENGTH = 160
    TONGUE_HEIGHT = 8
    MOUTH_HEIGHT = 20  # 새 그림의 입 위치를 발에서 약 20px에 맞춘다.
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
        self.attack_direction = self.direction
        self.attack_cooldown = 0.7
        self.wake_timer = 0.0
        self.sprite = FrogSprite()

    @property
    def bullet_vulnerable(self):
        return self.state != 'hidden' and self.wake_timer <= 0

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
            direction = (self.attack_direction if self.state in ('windup', 'tongue', 'recover')
                         else self.direction)
            game_world.add_object(FrogDeath(self.sprite, self.x, self.bottom, direction),
                                  game_world.EFFECTS)

    def set_state(self, state):
        self.state, self.state_time = state, 0.0

    def tongue_bb(self):
        if self.hp <= 0 or self.state != 'tongue':
            return None
        progress = self.state_time / self.TONGUE_TIME
        # 처음 1/3은 뻗기, 가운데는 유지, 마지막 1/3은 회수한다.
        length = self.TONGUE_LENGTH * max(0, min(1, progress * 3, (1 - progress) * 3))
        if length <= 0:
            return None
        mouth_x = self.x + self.attack_direction * self.WIDTH / 2
        end_x = mouth_x + self.attack_direction * length
        mouth_y = self.bottom + self.MOUTH_HEIGHT
        return (min(mouth_x, end_x), mouth_y - self.TONGUE_HEIGHT / 2,
                max(mouth_x, end_x), mouth_y + self.TONGUE_HEIGHT / 2)

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
        self.wake_timer = max(0, self.wake_timer - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.state_time += dt
        if self.state == 'windup':
            if self.state_time >= self.WINDUP_TIME:
                self.set_state('tongue')
            return
        if self.state == 'tongue':
            bounds = self.tongue_bb()
            if bounds is not None and overlaps(bounds, self.player.get_bb()):
                self.player.take_damage(1)
            if self.state_time >= self.TONGUE_TIME:
                self.set_state('recover')
            return
        if self.state == 'recover':
            if self.state_time >= self.RECOVER_TIME:
                self.attack_cooldown = self.ATTACK_COOLDOWN
                self.set_state('idle' if nearby else 'hidden')
            return
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
            if self.state != 'hidden':
                self.set_state('hidden')
        elif self.state == 'hidden':
            self.wake_timer = self.WAKE_PROTECTION
            self.velocity_y = self.JUMP_SPEED
            self.set_state('hop')
        elif (abs(self.player.x - self.x) <= self.ATTACK_DISTANCE
              and self.attack_cooldown <= 0):
            self.attack_direction = 1 if self.player.x > self.x else -1
            self.set_state('windup')
        elif self.state_time >= self.HOP_PAUSE:
            self.velocity_y = self.JUMP_SPEED
            self.set_state('hop')

    def draw(self):
        self.sprite.draw(self)
