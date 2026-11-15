"""바닥만 있는 긴 횡스크롤 맵. 오른쪽 끝에서 보스1 전투로 전환한다."""

from pathlib import Path

import pico2d
import game_framework
import game_world
import player_actions
import play_mode
from camera import Camera
from player import Player

WINDOW_WIDTH, WINDOW_HEIGHT = 960, 540
WORLD_WIDTH = 3600
GROUND_Y = 80
player = None
camera = None
font = None
transition_requested = False


def enter():
    global player, camera, transition_requested
    game_world.clear()
    player = Player(120, GROUND_Y, WORLD_WIDTH)
    camera = Camera(WINDOW_WIDTH, WORLD_WIDTH)
    game_world.add_object(player, game_world.ACTORS)
    transition_requested = False


def exit():
    global player, camera, font
    game_world.clear()
    player = camera = font = None


def handle_events(events=None):
    for event in pico2d.get_events() if events is None else events:
        if event.type == pico2d.SDL_QUIT:
            return False
        if event.type == pico2d.SDL_KEYDOWN:
            if event.key == pico2d.SDLK_ESCAPE:
                return False
            if event.key == pico2d.SDLK_r:
                enter()
                continue
            if event.key not in player.pressed_keys:
                if event.key == pico2d.SDLK_s:
                    player_actions.spawn_doodle(player, WORLD_WIDTH, WINDOW_HEIGHT, GROUND_Y)
                elif event.key == pico2d.SDLK_d:
                    player_actions.throw_eraser(player, WORLD_WIDTH, GROUND_Y)
        if (event.type == pico2d.SDL_WINDOWEVENT
                and event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST):
            player.clear_input()
        player.handle_event(event)
    return True


def update(dt):
    global transition_requested
    remaining = max(0, dt)
    while remaining > 0:
        step = min(remaining, 1 / 120)
        game_world.update(step)
        remaining -= step
    camera.follow(player.x)
    game_world.camera_x = camera.x
    if player.x >= WORLD_WIDTH - player.WIDTH / 2 - 0.001 and not transition_requested:
        transition_requested = True
        state = {'hp': player.hp, 'doodle_count': player.doodle_count,
                 'eraser_count': player.eraser_count}
        game_framework.change_mode(play_mode, player_state=state)


def draw():
    global font
    if font is None:
        font = pico2d.load_font(str(Path(pico2d.__file__).parent / 'data' / 'ConsolaMalgun.ttf'), 18)
    pico2d.clear_canvas()
    pico2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1,
                          247, 247, 239, filled=True)
    pico2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, GROUND_Y,
                          215, 214, 201, filled=True)
    pico2d.draw_line(0, GROUND_Y, WINDOW_WIDTH, GROUND_Y, 65, 70, 60)
    # 바닥 이음새만 월드 좌표에 맞춰 그려 스크롤을 확인한다.
    first = int(camera.x // 96) * 96
    for x in range(first, first + WINDOW_WIDTH + 96, 96):
        sx = game_world.screen_x(x)
        pico2d.draw_line(sx, 0, sx, GROUND_Y, 185, 184, 171)
    game_world.draw()
    font.draw(22, WINDOW_HEIGHT - 28, '횡스크롤 맵 1  |  오른쪽 끝에 도착하면 보스1 전투', (45, 60, 50))
    font.draw(22, WINDOW_HEIGHT - 55, '방향키 이동·웅크림 / Space 점프 / A 사격 / S 낙서 / D 지우개', (60, 70, 60))
    font.draw(22, WINDOW_HEIGHT - 82, '아래+S 발밑 생성 / 아래+D 발판 삭제 / R 처음부터 / Esc 종료', (60, 70, 60))
    font.draw(22, 30, f'거리 {int(player.x)} / {WORLD_WIDTH}   낙서 {player.doodle_count}   지우개 {player.eraser_count}',
              (60, 70, 60))
    pico2d.update_canvas()
