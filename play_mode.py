"""플레이 화면의 입력, 업데이트, 그리기."""

from pathlib import Path

import pico2d
import game_world
from player import Player
import player_actions
from boss1 import Boss1

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
GROUND_Y = 144
IMAGE_DIR = Path(__file__).resolve().parent / 'assets' / 'images'
BACKGROUND_LAYERS = (
    IMAGE_DIR / 'forest-scroll' / 'paper_background.png',
    IMAGE_DIR / 'forest-scroll' / 'background.png',
    IMAGE_DIR / 'boss-arena' / 'terrain_flat_960x540.png',
)
background_images = None
LASER_TEST_MODE = False  # True로 바꾸면 레이저만 반복하는 테스트 모드다.
player = None
font = None
enemy = None
game_over = False


def enter(player_state=None):
    global player, enemy, game_over
    game_world.clear()
    player = Player(120, GROUND_Y, WINDOW_WIDTH)
    if player_state is not None:
        player.hp = player_state['hp']
        player.doodle_count = player_state['doodle_count']
        player.eraser_count = player_state['eraser_count']
    game_world.add_object(player, game_world.ACTORS)
    enemy = Boss1(WINDOW_WIDTH, WINDOW_HEIGHT, GROUND_Y, laser_only=LASER_TEST_MODE)
    game_world.add_object(enemy, game_world.ACTORS)
    game_over = False


def exit():
    global player, font, enemy, game_over, background_images
    game_world.clear()
    player = None
    font = None
    enemy = None
    game_over = False
    background_images = None


def handle_events(events=None):
    for event in pico2d.get_events() if events is None else events:
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
    if game_over:
        return None
    return player_actions.spawn_doodle(player, WINDOW_WIDTH, WINDOW_HEIGHT, GROUND_Y)


def update(dt):
    global game_over
    if game_over:
        player.update(dt)
        for effect in game_world.objects(game_world.EFFECTS):
            effect.update(dt)
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
    if game_over:
        return None
    return player_actions.throw_eraser(player, WINDOW_WIDTH, GROUND_Y)


def draw():
    global font, background_images
    if font is None:
        font_path = Path(pico2d.__file__).parent / 'data' / 'ConsolaMalgun.ttf'
        font = pico2d.load_font(str(font_path), 20)
    pico2d.clear_canvas()
    if background_images is None:
        background_images = tuple(pico2d.load_image(str(path)) for path in BACKGROUND_LAYERS)
    for image in background_images:
        image.clip_draw(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT,
                        WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
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
