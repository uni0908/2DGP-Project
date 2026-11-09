"""플레이어의 위치와 이동을 관리한다."""

import pico2d


class Player:
    WIDTH = 36
    HEIGHT = 56
    MOVE_SPEED = 260.0  # 임시 값: 초당 픽셀

    def __init__(self, x, ground_y, world_width):
        self.x = x
        self.y = ground_y + self.HEIGHT / 2
        self.ground_y = ground_y
        self.world_width = world_width
        self.facing = 1
        self.pressed_keys = set()

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN:
            self.pressed_keys.add(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self.pressed_keys.discard(event.key)

    def clear_input(self):
        self.pressed_keys.clear()

    def update(self, dt):
        direction = (pico2d.SDLK_RIGHT in self.pressed_keys) - (
            pico2d.SDLK_LEFT in self.pressed_keys
        )
        if direction:
            self.facing = direction
        self.x += direction * self.MOVE_SPEED * dt
        self.x = max(self.WIDTH / 2, min(self.x, self.world_width - self.WIDTH / 2))

    def draw(self):
        left = self.x - self.WIDTH / 2
        bottom = self.y - self.HEIGHT / 2
        pico2d.draw_rectangle(left, bottom, left + self.WIDTH,
                              bottom + self.HEIGHT, 40, 40, 40)
        eye_x = self.x + self.facing * 9
        pico2d.draw_rectangle(eye_x - 2, self.y + 8, eye_x + 2,
                              self.y + 12, 40, 40, 40)
