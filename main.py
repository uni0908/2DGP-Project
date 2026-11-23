"""pico2d 실행 시작점."""

import pico2d
from core import game_framework
import play_mode
import scroll_mode


def main():
    pico2d.open_canvas(scroll_mode.WINDOW_WIDTH, scroll_mode.WINDOW_HEIGHT)
    try:
        game_framework.run(scroll_mode, {pico2d.SDLK_F1: scroll_mode,
                                         pico2d.SDLK_F2: play_mode})
    finally:
        pico2d.close_canvas()


if __name__ == '__main__':
    main()
