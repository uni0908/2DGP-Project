"""플레이 화면의 입력, 업데이트, 그리기."""

from pathlib import Path

import pico2d
import game_world
from player import Player
from doodle import Doodle, overlaps
from eraser import Eraser
from boss1 import Boss1

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
GROUND_Y = 80
LASER_TEST_MODE = False  # True로 바꾸면 레이저만 반복하는 테스트 모드다.
player = None
font = None
enemy = None
game_over = False


def enter():
    global player, enemy, game_over
    game_world.clear()
    player = Player(120, GROUND_Y, WINDOW_WIDTH)
    game_world.add_object(player, game_world.ACTORS)
    enemy = Boss1(WINDOW_WIDTH, WINDOW_HEIGHT, GROUND_Y, laser_only=LASER_TEST_MODE)
    game_world.add_object(enemy, game_world.ACTORS)
    game_over = False


def exit():
    global player, font, enemy, game_over
    game_world.clear()
    player = None
    font = None
    enemy = None
    game_over = False


def handle_events():
    for event in pico2d.get_events():
        if event.type == pico2d.SDL_QUIT:
            return False
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            return False
        if game_over or enemy.hp <= 0:
            if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_r:
                enter()
            continue
        if (event.type == pico2d.SDL_WINDOWEVENT
                and event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST):
            player.clear_input()
        if (event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_s
                and event.key not in player.pressed_keys):
            spawn_doodle()
        if (event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_d
                and event.key not in player.pressed_keys):
            throw_eraser()
        player.handle_event(event)
    return True


def spawn_doodle():
    if game_over or player.hp <= 0 or player.doodle_count <= 0:
        return None
    if pico2d.SDLK_DOWN in player.pressed_keys:
        feet_y = player.get_bb()[1]
        doodle = Doodle(player.x, feet_y - Doodle.UNDERFOOT_GAP - Doodle.HEIGHT / 2)
    else:
        distance = player.WIDTH / 2 + Doodle.SPAWN_GAP + Doodle.WIDTH / 2
        doodle = Doodle(player.x + player.facing * distance,
                        max(player.y, GROUND_Y + Doodle.HEIGHT / 2))
    bounds = doodle.get_bb()
    # 경계에서 위치를 강제로 보정하지 않고 생성을 거절한다.
    if (bounds[0] < 0 or bounds[2] > WINDOW_WIDTH
            or bounds[1] < GROUND_Y or bounds[3] > WINDOW_HEIGHT):
        return None
    occupied = (player.get_bb(),) + tuple(
        obj.get_bb() for obj in game_world.objects(game_world.TERRAIN)
    )
    occupied += tuple(obj.get_bb() for obj in game_world.objects(game_world.ACTORS)
                      if obj is not player)
    if any(overlaps(bounds, other) for other in occupied):
        return None
    game_world.add_object(doodle, game_world.TERRAIN)
    player.doodle_count -= 1
    return doodle


def update(dt):
    global game_over
    if game_over:
        return
    # 투사체가 움직이는 대상의 이전/현재 위치 사이를 건너뛰지 않게 분할한다.
    remaining = max(0, dt)
    while remaining > 0:
        step = min(remaining, 1 / 120)
        game_world.update(step)
        remaining -= step
        if player.hp <= 0:
            game_over = True
            player.clear_input()
            break


def throw_eraser():
    if game_over or player.hp <= 0 or player.eraser_count <= 0:
        return None
    # 플레이어 중심 높이에서 발사해 바로 앞 낙서부터 충돌을 판정한다.
    feet_y = player.get_bb()[1]
    downward = (pico2d.SDLK_DOWN in player.pressed_keys
                and feet_y > GROUND_Y + 0.001)
    eraser = Eraser(player.x, player.y, player.facing, WINDOW_WIDTH,
                    downward=downward, ground_y=GROUND_Y)
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
              f'체력: {player.hp}/5   [S] 낙서: {player.doodle_count}   [D] 지우개: {player.eraser_count}',
              (30, 30, 30))
    font.draw(20, WINDOW_HEIGHT - 58, '좌우: 이동  아래: 웅크리기  Space: 점프  A: 연사  Esc: 종료',
              (30, 30, 30))
    font.draw(20, WINDOW_HEIGHT - 84, '아래 + S: 발밑 낙서 생성 / 아래 + D: 발판 지우기', (30, 30, 30))
    font.draw(20, WINDOW_HEIGHT - 112, f'{enemy.NAME} · {enemy.attack_name}', (90, 50, 70))
    font.draw(20, 45, 'Space: 짧게/길게 점프  |  공중 재입력: 분홍·하늘탄 패링',
              (30, 30, 30))
    if player.parry_feedback_timer > 0:
        reward_name = '낙서' if player.last_parry_reward == 'doodle' else '지우개'
        font.draw(20, 20, f'패링 성공! {reward_name} +1', (150, 30, 120))
    if game_over:
        font.draw(WINDOW_WIDTH / 2 - 160, WINDOW_HEIGHT / 2,
                  '게임 오버! R: 재시작 / Esc: 종료', (180, 30, 30))
    elif enemy.hp <= 0:
        font.draw(WINDOW_WIDTH / 2 - 120, WINDOW_HEIGHT - 90,
                  '보스 처치! R: 다시 도전', (30, 80, 30))
    pico2d.update_canvas()
