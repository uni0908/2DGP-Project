"""수평으로 날아가 처음 닿은 낙서 하나만 제거하는 지우개."""

import pico2d
import game_world
from doodle import Doodle


class Eraser:
    WIDTH = 20
    HEIGHT = 12
    SPEED = 520.0
    MAX_DISTANCE = 700.0

    def __init__(self, x, y, direction, world_width):
        self.x, self.y = x, y
        self.direction = direction
        self.world_width = world_width
        self.travelled = 0.0

    def update(self, dt):
        distance = min(self.SPEED * max(0, dt), self.MAX_DISTANCE - self.travelled)
        next_x = self.x + self.direction * distance
        hits = []
        # 이동 구간 전체와 낙서 경계를 비교해 빠른 투척도 관통하지 않게 한다.
        for obj in game_world.objects(game_world.TERRAIN):
            if not isinstance(obj, Doodle):
                continue
            left, bottom, right, top = obj.get_bb()
            if self.y + self.HEIGHT / 2 < bottom or self.y - self.HEIGHT / 2 > top:
                continue
            low, high = left - self.WIDTH / 2, right + self.WIDTH / 2
            if max(min(self.x, next_x), low) <= min(max(self.x, next_x), high):
                entry = max(0, low - self.x) if self.direction > 0 else max(0, self.x - high)
                hits.append((entry, obj))
        if hits:
            target = min(hits, key=lambda hit: hit[0])[1]
            game_world.remove_object(target)
            game_world.remove_object(self)
            return
        self.x = next_x
        self.travelled += distance
        if (self.travelled >= self.MAX_DISTANCE or self.x + self.WIDTH / 2 < 0
                or self.x - self.WIDTH / 2 > self.world_width):
            game_world.remove_object(self)

    def draw(self):
        pico2d.draw_rectangle(self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                              self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2,
                              220, 100, 140, filled=True)
