"""생성 위치에 고정되는 낙서 지형. 현재 그림은 임시 선 표현이다."""


import pico2d
from core.paths import PROJECT_ROOT
from core import game_world
class Doodle:
    IMAGE_PATH = PROJECT_ROOT / 'assets' / 'images' / 'items' / 'doodle.png'
    image = None
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
        if Doodle.image is None:
            Doodle.image = pico2d.load_image(str(self.IMAGE_PATH))
        Doodle.image.draw(game_world.screen_x(self.x), self.y, self.WIDTH, self.HEIGHT)


def overlaps(a, b):
    """면적이 있는 겹침만 판정한다. 가장자리 접촉은 허용한다."""
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
