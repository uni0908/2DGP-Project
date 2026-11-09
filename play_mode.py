"""플레이 화면의 입력, 업데이트, 그리기."""

import pico2d
from player import Player

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
GROUND_Y = 80
player = None


def enter():
    global player
    player = Player(120, GROUND_Y, WINDOW_WIDTH)


def exit():
    global player
    player = None


def handle_events():
    for event in pico2d.get_events():
        if event.type == pico2d.SDL_QUIT:
            return False
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            return False
        if (event.type == pico2d.SDL_WINDOWEVENT
                and event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST):
            player.clear_input()
        player.handle_event(event)
    return True


def update(dt):
    player.update(dt)


def draw():
    pico2d.clear_canvas()
    pico2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, GROUND_Y)
    player.draw()
    pico2d.update_canvas()
