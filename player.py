"""플레이어의 위치와 이동을 관리한다."""

import pico2d
import game_world
from bullet import Bullet
from doodle import overlaps


class Player:
    WIDTH = 36
    HEIGHT = 56
    CROUCH_HEIGHT = 28
    CROUCH_SPEED = 130.0
    MOVE_SPEED = 260.0  # 임시 값: 초당 픽셀
    JUMP_SPEED = 620.0  # 임시 값: 초당 픽셀
    GRAVITY = 1800.0  # 임시 값: 초당 픽셀/초
    INITIAL_DOODLES = 10
    INITIAL_ERASERS = 10
    MAX_HP = 5
    FIRE_INTERVAL = 0.15
    INVINCIBILITY_TIME = 1.0
    PARRY_WINDOW = 0.22
    PARRY_MARGIN = 12
    PARRY_REWARD = 1
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
        self.invincibility_timer = 0.0
        self.height = self.HEIGHT
        self.crouching = False
        self.parry_timer = 0.0
        self.parry_feedback_timer = 0.0
        self.last_parry_reward = None

    def take_damage(self, amount):
        if self.hp <= 0 or self.invincibility_timer > 0 or amount <= 0:
            return
        self.hp = max(0, self.hp - amount)
        self.invincibility_timer = self.INVINCIBILITY_TIME
        if self.hp == 0:
            self.clear_input()

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN:
            if event.key == pico2d.SDLK_DOWN and self.grounded:
                self._set_crouching(True)
            if event.key == pico2d.SDLK_SPACE and event.key not in self.pressed_keys:
                if self.hp > 0 and not self.crouching:
                    self.jump()
                    self.parry_timer = self.PARRY_WINDOW
            self.pressed_keys.add(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self.pressed_keys.discard(event.key)

    def clear_input(self):
        self.pressed_keys.clear()
        self.parry_timer = 0.0

    def get_parry_bb(self):
        left, bottom, right, top = self.get_bb()
        return (left - self.PARRY_MARGIN, bottom - self.PARRY_MARGIN,
                right + self.PARRY_MARGIN, top + self.PARRY_MARGIN)

    def try_parry(self, bullet):
        if (self.hp <= 0 or self.crouching or self.parry_timer <= 0
                or not bullet.active or bullet.team != 'enemy'
                or bullet.parry_reward not in ('doodle', 'eraser')):
            return False
        if bullet.parry_reward == 'doodle':
            self.doodle_count += self.PARRY_REWARD
        else:
            self.eraser_count += self.PARRY_REWARD
        # 입력 한 번에 한 발만 패링하며 연속 성공하려면 다시 눌러야 한다.
        self.parry_timer = 0.0
        self.velocity_y = self.JUMP_SPEED
        self.grounded = False
        self.last_parry_reward = bullet.parry_reward
        self.parry_feedback_timer = 0.8
        return True

    def jump(self):
        if self.grounded and not self.crouching:
            self.velocity_y = self.JUMP_SPEED
            self.grounded = False

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.y - self.height / 2,
                self.x + self.WIDTH / 2, self.y + self.height / 2)

    def _set_crouching(self, crouching):
        bottom = self.y - self.height / 2
        height = self.CROUCH_HEIGHT if crouching else self.HEIGHT
        if not crouching:
            standing_box = (self.x - self.WIDTH / 2, bottom,
                            self.x + self.WIDTH / 2, bottom + height)
            if any(overlaps(standing_box, obj.get_bb())
                   for obj in game_world.objects(game_world.TERRAIN)):
                return  # 머리 위 공간이 확보될 때까지 웅크린 상태 유지
        self.height = height
        self.y = bottom + height / 2
        self.crouching = crouching

    def update(self, dt):
        if self.hp <= 0:
            return
        self.invincibility_timer = max(0.0, self.invincibility_timer - max(0, dt))
        self.parry_timer = max(0.0, self.parry_timer - max(0, dt))
        self.parry_feedback_timer = max(0.0, self.parry_feedback_timer - max(0, dt))
        if pico2d.SDLK_DOWN in self.pressed_keys:
            if self.grounded:
                self._set_crouching(True)
        elif self.crouching:
            self._set_crouching(False)
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
        if pico2d.SDLK_a in self.pressed_keys and self.fire_timer <= 0:
            x = self.x + self.facing * (self.WIDTH / 2 + Bullet.WIDTH / 2)
            game_world.add_object(Bullet(x, self.y, self.facing, self.team,
                                         self.world_width), game_world.PROJECTILES)
            self.fire_timer = self.FIRE_INTERVAL

    def _move(self, dt, direction, terrain):
        old_left, bottom, old_right, top = self.get_bb()
        speed = self.CROUCH_SPEED if self.crouching else self.MOVE_SPEED
        next_x = self.x + direction * speed * dt
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
        next_bottom = next_y - self.height / 2
        # 아래에서 올라가는 동안에는 윗면/아랫면 충돌을 적용하지 않는다.
        crossed = [height for height in surfaces
                   if next_bottom <= height <= bottom and self.velocity_y <= 0]
        if crossed:
            next_y = max(crossed) + self.height / 2
            self.velocity_y = 0.0
            self.grounded = True
        self.y = next_y

    def draw(self):
        if self.parry_timer > 0:
            pico2d.draw_rectangle(*self.get_parry_bb(), 240, 70, 160)
        if self.invincibility_timer > 0 and int(self.invincibility_timer * 10) % 2 == 0:
            return
        left = self.x - self.WIDTH / 2
        bottom = self.y - self.height / 2
        pico2d.draw_rectangle(left, bottom, left + self.WIDTH,
                              bottom + self.height, 40, 40, 40)
        eye_x = self.x + self.facing * 9
        pico2d.draw_rectangle(eye_x - 2, self.y + 8, eye_x + 2,
                              self.y + 12, 40, 40, 40)
