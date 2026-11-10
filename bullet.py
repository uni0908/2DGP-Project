"""진영별 수평 총알과 이동 구간 충돌 판정."""

import pico2d
import game_world
from doodle import Doodle


class Bullet:
    WIDTH = 12
    HEIGHT = 6
    DAMAGE = 1

    def __init__(self, x, y, direction, team, world_width, parry_reward=None):
        self.x, self.y = x, y
        self.direction = direction
        self.team = team
        self.speed = 650 if team == 'player' else 240
        self.world_width = world_width
        self.active = True
        self.parry_reward = parry_reward if team == 'enemy' else None
        if self.parry_reward is not None:
            self.WIDTH, self.HEIGHT = 20, 14

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    def update(self, dt):
        if not self.active:
            return
        next_x = self.x + self.direction * self.speed * max(0, dt)
        hits = []
        targets = [obj for obj in game_world.objects(game_world.TERRAIN)
                   if isinstance(obj, Doodle)]
        targets.extend(obj for obj in game_world.objects(game_world.ACTORS)
                       if getattr(obj, 'team', None) not in (None, self.team)
                       and getattr(obj, 'hp', 0) > 0)
        for obj in targets:
            left, bottom, right, top = obj.get_bb()
            if self.y + self.HEIGHT / 2 < bottom or self.y - self.HEIGHT / 2 > top:
                continue
            low, high = left - self.WIDTH / 2, right + self.WIDTH / 2
            if max(min(self.x, next_x), low) <= min(max(self.x, next_x), high):
                distance = max(0, low - self.x) if self.direction > 0 else max(0, self.x - high)
                hits.append((distance, obj))
        if hits:
            target = min(hits, key=lambda hit: hit[0])[1]
            target.take_damage(self.DAMAGE)
            self.active = False
            game_world.remove_object(self)
            return
        self.x = next_x
        if self.x + self.WIDTH / 2 < 0 or self.x - self.WIDTH / 2 > self.world_width:
            self.active = False
            game_world.remove_object(self)

    def draw(self):
        color = (40, 100, 220) if self.team == 'player' else (220, 70, 40)
        if self.parry_reward == 'doodle':
            color = (240, 70, 160)
        elif self.parry_reward == 'eraser':
            color = (30, 180, 240)
        pico2d.draw_rectangle(self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                              self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2,
                              *color, filled=True)
