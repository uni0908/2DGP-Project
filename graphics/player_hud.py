"""Player health artwork clipped to the number of remaining hearts."""


import pico2d
from core.paths import PROJECT_ROOT


class PlayerHealthBar:
    IMAGE_PATH = PROJECT_ROOT / 'assets' / 'images' / 'items' / 'player-hp.png'
    # Each boundary falls in the transparent gap following the face or a heart.
    RIGHT_EDGES = (784, 1030, 1283, 1535, 1784, 2035)
    SCALE = .11

    def __init__(self):
        self.image = None

    def draw(self, hp, left=20, top=520):
        if self.image is None:
            self.image = pico2d.load_image(str(self.IMAGE_PATH))
        hearts = max(0, min(len(self.RIGHT_EDGES) - 1, int(hp)))
        source_left, source_top, source_bottom = 180, 80, 650
        width = self.RIGHT_EDGES[hearts] - source_left
        height = source_bottom - source_top
        draw_width, draw_height = width * self.SCALE, height * self.SCALE
        self.image.clip_draw(source_left, 724 - source_bottom, width, height,
                             left + draw_width / 2, top - draw_height / 2,
                             draw_width, draw_height)
