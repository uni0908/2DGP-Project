"""진영별 수평 총알과 이동 구간 충돌 판정."""

import math

import pico2d
from core import game_world
from doodle import Doodle


class Bullet:
    WIDTH = 12
    HEIGHT = 6
    DAMAGE = 1

    def __init__(self, x, y, direction, team, world_width, parry_reward=None,
                 direction_y=0, world_height=540):
        self.x, self.y = x, y
        self.direction = direction
        length = math.hypot(direction, direction_y) or 1
        self.velocity_x = direction / length
        self.velocity_y = direction_y / length
        self.world_height = world_height
        self.team = team
        self.speed = 650 if team == 'player' else 240
        self.world_width = world_width
        self.active = True
        self.sprite_bank = None
        self.animation_time = 0.0
        self.parry_reward = parry_reward if team == 'enemy' else None
        if self.parry_reward is not None:
            self.WIDTH, self.HEIGHT = 20, 14

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    def update(self, dt):
        if not self.active:
            return
        self.animation_time += max(0, dt)
        next_x = self.x + self.velocity_x * self.speed * max(0, dt)
        next_y = self.y + self.velocity_y * self.speed * max(0, dt)
        hits = []
        targets = [obj for obj in game_world.objects(game_world.TERRAIN)
                   if isinstance(obj, Doodle)]
        targets.extend(obj for obj in game_world.objects(game_world.ACTORS)
                       if getattr(obj, 'team', None) not in (None, self.team)
                       and getattr(obj, 'hp', 0) > 0
                       and getattr(obj, 'bullet_vulnerable', True))
        for obj in targets:
            left, bottom, right, top = obj.get_bb()
            if (self.parry_reward is not None and getattr(obj, 'parry_timer', 0) > 0
                    and not obj.grounded):
                left, bottom, right, top = obj.get_parry_bb()
            # Sweep the bullet center through the target expanded by bullet size.
            entry, exit_time = 0.0, 1.0
            for start, end, low, high in (
                    (self.x, next_x, left - self.WIDTH / 2, right + self.WIDTH / 2),
                    (self.y, next_y, bottom - self.HEIGHT / 2, top + self.HEIGHT / 2)):
                delta = end - start
                if delta == 0:
                    if not low <= start <= high:
                        entry = 2.0
                        break
                else:
                    near, far = sorted(((low - start) / delta, (high - start) / delta))
                    entry = max(entry, near)
                    exit_time = min(exit_time, far)
            if entry <= exit_time:
                hits.append((entry, obj))
        if hits:
            target = min(hits, key=lambda hit: hit[0])[1]
            if not (hasattr(target, 'try_parry') and target.try_parry(self, at_contact=True)):
                if hasattr(target, 'receive_bullet'):
                    target.receive_bullet(self)
                else:
                    target.take_damage(self.DAMAGE)
            self.active = False
            game_world.remove_object(self)
            return
        self.x = next_x
        self.y = next_y
        if (self.x + self.WIDTH / 2 < 0 or self.x - self.WIDTH / 2 > self.world_width
                or (self.velocity_y != 0 and
                    (self.y - self.HEIGHT / 2 > self.world_height
                     or self.y + self.HEIGHT / 2 < 0))):
            self.active = False
            game_world.remove_object(self)

    def draw(self):
        if self.sprite_bank is not None and self.parry_reward is None:
            self.sprite_bank.draw_effect('bullet', self.animation_time,
                                         self.x, self.y, self.WIDTH * 1.5, self.HEIGHT)
            return
        color = (40, 100, 220) if self.team == 'player' else (220, 70, 40)
        if self.parry_reward == 'doodle':
            color = (240, 70, 160)
        elif self.parry_reward == 'eraser':
            color = (30, 180, 240)
        screen_x = game_world.screen_x(self.x)
        pico2d.draw_rectangle(screen_x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                              screen_x + self.WIDTH / 2, self.y + self.HEIGHT / 2,
                              *color, filled=True)
