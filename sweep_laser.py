"""낙서를 보존하며 통과하고 플레이어에게만 피해를 주는 왕복 레이저."""

import pico2d
import game_world


class SweepLaser:
    THICKNESS = 16
    SPEED = 180.0
    SAFE_EDGE = 48
    DAMAGE = 1

    def __init__(self, world_width, world_height, ground_y):
        self.left = self.SAFE_EDGE
        self.right = world_width
        self.bottom_y = ground_y - self.THICKNESS / 2
        self.top_y = world_height + self.THICKNESS / 2
        self.y = self.bottom_y
        self.direction = 1
        self.active = True

    def update(self, dt):
        remaining = max(0, dt)
        while self.active and remaining > 0:
            destination = self.top_y if self.direction > 0 else self.bottom_y
            duration = abs(destination - self.y) / self.SPEED
            step = min(remaining, duration)
            next_y = self.y + self.direction * self.SPEED * step
            self.sweep_collisions(self.y, next_y)
            self.y = next_y
            remaining -= step
            if step >= duration:
                self.y = destination
                if self.direction > 0:
                    self.direction = -1
                else:
                    self.active = False
                    game_world.remove_object(self)

    def sweep_collisions(self, old_y, new_y):
        low = min(old_y, new_y) - self.THICKNESS / 2
        high = max(old_y, new_y) + self.THICKNESS / 2
        # 낙서는 레이저를 막지도, 레이저에 피해를 받지도 않는다.
        for obj in game_world.objects(game_world.ACTORS):
            if getattr(obj, 'team', None) != 'player' or obj.hp <= 0:
                continue
            left, bottom, right, top = obj.get_bb()
            if left < self.right and right > self.left and bottom <= high and top >= low:
                obj.take_damage(self.DAMAGE)

    def draw(self):
        if not self.active:
            return
        pico2d.draw_rectangle(self.left, self.y - self.THICKNESS / 2,
                              self.right, self.y + self.THICKNESS / 2,
                              30, 210, 230, filled=True)
        pico2d.draw_line(self.left, self.y, self.right, self.y, 230, 255, 255)
