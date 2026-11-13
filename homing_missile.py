"""수명 제한 없이 완만하게 추적하고 충돌할 때만 소멸하는 유도탄."""

import math

import pico2d
import game_world
from bullet import Bullet
from doodle import Doodle


def segment_box_entry(x, y, dx, dy, bounds):
    """선분이 사각형에 처음 들어가는 비율. 대각선 관통을 방지한다."""
    near, far = 0.0, 1.0
    for start, delta, low, high in ((x, dx, bounds[0], bounds[2]),
                                    (y, dy, bounds[1], bounds[3])):
        if abs(delta) < 1e-9:
            if start < low or start > high:
                return None
            continue
        first, last = sorted(((low - start) / delta, (high - start) / delta))
        near, far = max(near, first), min(far, last)
        if near > far:
            return None
    return near


class HomingMissile(Bullet):
    def __init__(self, x, y, target, world_width, parry_reward=None):
        super().__init__(x, y, -1, 'enemy', world_width, parry_reward)
        self.WIDTH = 24 if parry_reward else 20
        self.HEIGHT = 18 if parry_reward else 12
        self.target = target
        self.angle = math.pi
        self.speed = 120.0 if parry_reward else 150.0
        self.turn_speed = math.radians(90 if parry_reward else 110)

    def update(self, dt):
        remaining = max(0, dt)
        while self.active and remaining > 0:
            step = min(remaining, 1 / 120)
            self.move_step(step)
            remaining -= step

    def move_step(self, dt):
        if self.target is not None and getattr(self.target, 'hp', 0) > 0:
            desired = math.atan2(self.target.y - self.y, self.target.x - self.x)
            difference = (desired - self.angle + math.pi) % math.tau - math.pi
            turn = self.turn_speed * dt
            self.angle += max(-turn, min(difference, turn))
        dx = math.cos(self.angle) * self.speed * dt
        dy = math.sin(self.angle) * self.speed * dt
        hits = []
        targets = [obj for obj in game_world.objects(game_world.TERRAIN)
                   if isinstance(obj, Doodle)]
        targets.extend(obj for obj in game_world.objects(game_world.ACTORS)
                       if getattr(obj, 'team', None) == 'player' and obj.hp > 0)
        for obj in targets:
            bounds = obj.get_bb()
            if self.parry_reward and getattr(obj, 'parry_timer', 0) > 0 and not obj.grounded:
                bounds = obj.get_parry_bb()
            left, bottom, right, top = bounds
            expanded = (left - self.WIDTH / 2, bottom - self.HEIGHT / 2,
                        right + self.WIDTH / 2, top + self.HEIGHT / 2)
            entry = segment_box_entry(self.x, self.y, dx, dy, expanded)
            if entry is not None:
                hits.append((entry, obj))
        if hits:
            entry, target = min(hits, key=lambda hit: hit[0])
            self.x += dx * entry
            self.y += dy * entry
            if not (hasattr(target, 'try_parry') and target.try_parry(self, at_contact=True)):
                target.take_damage(self.DAMAGE)
            self.active = False
            game_world.remove_object(self)
        else:
            self.x += dx
            self.y += dy
        # 시간 제한이나 화면 밖 이탈로는 삭제하지 않는다.

    def draw(self):
        color = (230, 120, 30)
        if self.parry_reward == 'doodle':
            color = (240, 70, 160)
        elif self.parry_reward == 'eraser':
            color = (30, 180, 240)
        pico2d.draw_rectangle(*self.get_bb(), *color, filled=True)
        nose_x = self.x + math.cos(self.angle) * 18
        nose_y = self.y + math.sin(self.angle) * 18
        pico2d.draw_line(self.x, self.y, nose_x, nose_y, *color)
