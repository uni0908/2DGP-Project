"""플레이 화면의 입력, 업데이트, 그리기."""

from pathlib import Path

import pico2d
import game_world
from player import Player
from doodle import Doodle, overlaps
from eraser import Eraser

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
GROUND_Y = 80
player = None
font = None


def enter():
    global player
    game_world.clear()
    player = Player(120, GROUND_Y, WINDOW_WIDTH)
    game_world.add_object(player, game_world.ACTORS)


def exit():
    global player, font
    game_world.clear()
    player = None
    font = None


def handle_events():
    for event in pico2d.get_events():
        if event.type == pico2d.SDL_QUIT:
            return False
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            return False
        if (event.type == pico2d.SDL_WINDOWEVENT
                and event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST):
            player.clear_input()
        if (event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_d
                and event.key not in player.pressed_keys):
            spawn_doodle()
        if (event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_e
                and event.key not in player.pressed_keys):
            throw_eraser()
        player.handle_event(event)
    return True


def spawn_doodle():
    if player.doodle_count <= 0:
        return None
    distance = player.WIDTH / 2 + Doodle.SPAWN_GAP + Doodle.WIDTH / 2
    doodle = Doodle(player.x + player.facing * distance, player.y)
    bounds = doodle.get_bb()
    # 경계에서 위치를 강제로 보정하지 않고 생성을 거절한다.
    if (bounds[0] < 0 or bounds[2] > WINDOW_WIDTH
            or bounds[1] < GROUND_Y or bounds[3] > WINDOW_HEIGHT):
        return None
    occupied = (player.get_bb(),) + tuple(
        obj.get_bb() for obj in game_world.objects(game_world.TERRAIN)
    )
    if any(overlaps(bounds, other) for other in occupied):
        return None
    game_world.add_object(doodle, game_world.TERRAIN)
    player.doodle_count -= 1
    return doodle


def update(dt):
    game_world.update(dt)


def throw_eraser():
    if player.eraser_count <= 0:
        return None
    # 플레이어 중심 높이에서 발사해 바로 앞 낙서부터 충돌을 판정한다.
    eraser = Eraser(player.x, player.y, player.facing, WINDOW_WIDTH)
    game_world.add_object(eraser, game_world.PROJECTILES)
    player.eraser_count -= 1
    return eraser


def draw():
    global font
    if font is None:
        font_path = Path(pico2d.__file__).parent / 'data' / 'ConsolaMalgun.ttf'
        font = pico2d.load_font(str(font_path), 20)
    pico2d.clear_canvas()
    pico2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, GROUND_Y)
    game_world.draw()
    font.draw(20, WINDOW_HEIGHT - 30,
              f'[D] 낙서: {player.doodle_count}   [E] 지우개: {player.eraser_count}',
              (30, 30, 30))
    font.draw(20, WINDOW_HEIGHT - 58, '방향키: 이동   Space: 점프   Esc: 종료',
              (30, 30, 30))
    pico2d.update_canvas()
