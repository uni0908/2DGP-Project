"""플레이어의 위치와 이동을 관리한다."""

import pico2d
import game_world
from bullet import Bullet


class Player:
    WIDTH = 36
    HEIGHT = 56
    MOVE_SPEED = 260.0  # 임시 값: 초당 픽셀
    JUMP_SPEED = 620.0  # 임시 값: 초당 픽셀
    GRAVITY = 1800.0  # 임시 값: 초당 픽셀/초
    INITIAL_DOODLES = 10
    INITIAL_ERASERS = 10
    MAX_HP = 5
    FIRE_INTERVAL = 0.15
    team = 'player'

    def __init__(self, x, ground_y, world_width):
        self.x = x
        self.y = ground_y + self.HEIGHT / 2
        self.ground_y = ground_y
        self.world_width = world_width
        self.facing = 1
        self.pressed_keys = set()
        self.velocity_y = 0.0
        self.grounded = True
        self.doodle_count = self.INITIAL_DOODLES
        self.eraser_count = self.INITIAL_ERASERS
        self.hp = self.MAX_HP
        self.fire_timer = 0.0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.clear_input()

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN:
            if event.key == pico2d.SDLK_SPACE and event.key not in self.pressed_keys:
                self.jump()
            self.pressed_keys.add(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self.pressed_keys.discard(event.key)

    def clear_input(self):
        self.pressed_keys.clear()

    def jump(self):
        if self.grounded:
            self.velocity_y = self.JUMP_SPEED
            self.grounded = False

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    def update(self, dt):
        if self.hp <= 0:
            return
        direction = (pico2d.SDLK_RIGHT in self.pressed_keys) - (
            pico2d.SDLK_LEFT in self.pressed_keys
        )
        if direction:
            self.facing = direction
        # 얇은 낙서를 빠르게 통과하지 않도록 물리 계산을 작은 시간으로 나눈다.
        remaining = max(0.0, dt)
        terrain = game_world.objects(game_world.TERRAIN)
        while remaining > 0:
            step = min(remaining, 1 / 120)
            self._move(step, direction, terrain)
            remaining -= step
        self.fire_timer = max(0, self.fire_timer - max(0, dt))
        if pico2d.SDLK_z in self.pressed_keys and self.fire_timer <= 0:
            x = self.x + self.facing * (self.WIDTH / 2 + Bullet.WIDTH / 2)
            game_world.add_object(Bullet(x, self.y, self.facing, self.team,
                                         self.world_width), game_world.PROJECTILES)
            self.fire_timer = self.FIRE_INTERVAL

    def _move(self, dt, direction, terrain):
        old_left, bottom, old_right, top = self.get_bb()
        next_x = self.x + direction * self.MOVE_SPEED * dt
        for obj in terrain:
            left, low, right, high = obj.get_bb()
            if bottom < high and top > low:
                if direction > 0 and old_right <= left and next_x + self.WIDTH / 2 > left:
                    next_x = min(next_x, left - self.WIDTH / 2)
                elif direction < 0 and old_left >= right and next_x - self.WIDTH / 2 < right:
                    next_x = max(next_x, right + self.WIDTH / 2)
        self.x = next_x
        self.x = max(self.WIDTH / 2, min(self.x, self.world_width - self.WIDTH / 2))
        left, bottom, right, _ = self.get_bb()
        surfaces = [self.ground_y]
        surfaces.extend(obj.get_bb()[3] for obj in terrain
                        if left < obj.get_bb()[2] and right > obj.get_bb()[0])
        supported = any(abs(bottom - height) < 0.000001 for height in surfaces)
        self.grounded = self.velocity_y <= 0 and supported
        if self.grounded:
            self.velocity_y = 0.0
            return
        next_y = self.y + self.velocity_y * dt - 0.5 * self.GRAVITY * dt * dt
        self.velocity_y -= self.GRAVITY * dt
        next_bottom = next_y - self.HEIGHT / 2
        # 아래에서 올라가는 동안에는 윗면/아랫면 충돌을 적용하지 않는다.
        crossed = [height for height in surfaces
                   if next_bottom <= height <= bottom and self.velocity_y <= 0]
        if crossed:
            next_y = max(crossed) + self.HEIGHT / 2
            self.velocity_y = 0.0
            self.grounded = True
        self.y = next_y

    def draw(self):
        left = self.x - self.WIDTH / 2
        bottom = self.y - self.HEIGHT / 2
        pico2d.draw_rectangle(left, bottom, left + self.WIDTH,
                              bottom + self.HEIGHT, 40, 40, 40)
        eye_x = self.x + self.facing * 9
        pico2d.draw_rectangle(eye_x - 2, self.y + 8, eye_x + 2,
                              self.y + 12, 40, 40, 40)
