"""장면의 진입·입력·업데이트·그리기·종료와 전환을 관리한다."""

from time import perf_counter

import pico2d

current_mode = None
next_mode = None
running = False


def change_mode(mode):
    global next_mode
    if mode is not current_mode:
        next_mode = mode


def quit():
    global running
    running = False


def apply_mode_change():
    global current_mode, next_mode
    if next_mode is None:
        return
    if current_mode is not None:
        current_mode.exit()
    current_mode, next_mode = next_mode, None
    current_mode.enter()


def run(start_mode, shortcuts=None):
    global current_mode, next_mode, running
    shortcuts = shortcuts or {}
    current_mode, next_mode, running = None, start_mode, True
    try:
        apply_mode_change()
        previous_time = perf_counter()
        while running:
            now = perf_counter()
            dt = min(now - previous_time, 0.05)
            previous_time = now
            events = []
            for event in pico2d.get_events():
                if event.type == pico2d.SDL_QUIT:
                    quit()
                elif event.type == pico2d.SDL_KEYDOWN and event.key in shortcuts:
                    change_mode(shortcuts[event.key])
                else:
                    events.append(event)
            if not running:
                break
            if next_mode is None and current_mode.handle_events(events) is False:
                quit()
            if not running:
                break
            apply_mode_change()
            current_mode.update(dt)
            current_mode.draw()
            pico2d.delay(0.01)
    finally:
        if current_mode is not None:
            current_mode.exit()
        current_mode = next_mode = None
        running = False
