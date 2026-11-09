"""pico2d 실행 시작점."""

from time import perf_counter

import pico2d
import play_mode


def main():
    pico2d.open_canvas(play_mode.WINDOW_WIDTH, play_mode.WINDOW_HEIGHT)
    try:
        play_mode.enter()
        previous_time = perf_counter()
        running = True
        while running:
            current_time = perf_counter()
            dt = min(current_time - previous_time, 0.05)
            previous_time = current_time
            running = play_mode.handle_events()
            if not running:
                break
            play_mode.update(dt)
            play_mode.draw()
            pico2d.delay(0.01)
    finally:
        play_mode.exit()
        pico2d.close_canvas()


if __name__ == '__main__':
    main()
