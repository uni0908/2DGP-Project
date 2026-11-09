"""플레이 화면의 입력, 업데이트, 그리기."""

import pico2d

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
GROUND_Y = 80


def enter():
    pass


def exit():
    pass


def handle_events():
    for event in pico2d.get_events():
        if event.type == pico2d.SDL_QUIT:
            return False
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            return False
    return True


def update(dt):
    pass


def draw():
    pico2d.clear_canvas()
    pico2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, GROUND_Y)
    pico2d.update_canvas()
