"""생성 위치에 고정되는 낙서 지형. 현재 그림은 임시 선 표현이다."""

import math

import pico2d
import game_world


class Doodle:
    WIDTH = 88
    HEIGHT = 32
    SPAWN_GAP = 12
    UNDERFOOT_GAP = 4
    MAX_HP = 20

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = self.MAX_HP

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            game_world.remove_object(self)

    def get_bb(self):
        return (self.x - self.WIDTH / 2, self.y - self.HEIGHT / 2,
                self.x + self.WIDTH / 2, self.y + self.HEIGHT / 2)

    def update(self, dt):
        pass  # 낙서는 중력 없이 생성 위치를 유지한다.

    def draw(self):
        screen_x = game_world.screen_x(self.x)
        # 결정적인 궤적을 사용해 프레임마다 무늬가 바뀌지 않도록 한다.
        for phase in (0, 1.7, 3.4):
            previous = None
            for i in range(65):
                angle = i * math.tau / 64
                x = screen_x + (self.WIDTH / 2 - 2) * math.cos(angle)
                y = self.y + (self.HEIGHT / 2 - 2) * math.sin(5 * angle + phase)
                if previous is not None:
                    pico2d.draw_line(*previous, x, y, 70, 70, 70)
                previous = (x, y)
        pico2d.draw_rectangle(*game_world.screen_bb(self.get_bb()), 100, 100, 100)


def overlaps(a, b):
    """면적이 있는 겹침만 판정한다. 가장자리 접촉은 허용한다."""
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
