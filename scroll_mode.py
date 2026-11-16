"""다섯 레이어의 숲을 가로로 스크롤하는 맵."""

from pathlib import Path

import pico2d
import game_framework
import game_world
import player_actions
import play_mode
from camera import Camera
from player import Player
from player_hud import PlayerHealthBar

health_bar = PlayerHealthBar()

WINDOW_WIDTH, WINDOW_HEIGHT = 960, 540
WORLD_WIDTH = 3600
GROUND_Y = 144
PLAYER_START_X = WINDOW_WIDTH * 0.4
MAP_DIR = Path(__file__).resolve().parent / 'assets' / 'images' / 'forest-scroll'
MAP_LAYERS = ('paper_background.png', 'background.png', 'midground.png',
              'terrain.png', 'foreground.png')
map_images = None
player = None
camera = None
font = None
transition_requested = False


def enter():
    global player, camera, transition_requested
    game_world.clear()
    player = Player(PLAYER_START_X, GROUND_Y, WORLD_WIDTH)
    camera = Camera(WINDOW_WIDTH, WORLD_WIDTH)
    game_world.add_object(player, game_world.ACTORS)
    transition_requested = False


def exit():
    global player, camera, font, map_images
    game_world.clear()
    player = camera = font = None
    map_images = None
    health_bar.image = None


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
    global font, map_images
    if font is None:
        font = pico2d.load_font(str(Path(pico2d.__file__).parent / 'data' / 'ConsolaMalgun.ttf'), 18)
    pico2d.clear_canvas()
    pico2d.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1,
                          247, 247, 239, filled=True)
    if map_images is None:
        map_images = tuple(pico2d.load_image(str(MAP_DIR / name)) for name in MAP_LAYERS)
    for image in map_images[:-1]:
        image.clip_draw(int(camera.x), 0, WINDOW_WIDTH, WINDOW_HEIGHT,
                        WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
    game_world.draw()
    map_images[-1].clip_draw(int(camera.x), 0, WINDOW_WIDTH, WINDOW_HEIGHT,
                             WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
    health_bar.draw(player.hp)
    font.draw(520, WINDOW_HEIGHT - 28, '방향키 이동 / Space 점프 / A 사격', (45, 60, 50))
    font.draw(520, WINDOW_HEIGHT - 55, 'S 낙서 / D 지우개 / R 재시작', (60, 70, 60))
    font.draw(520, WINDOW_HEIGHT - 82, '아래+S 발밑 생성 / 아래+D 삭제', (60, 70, 60))
    font.draw(520, WINDOW_HEIGHT - 109, f'거리 {int(player.x)} / {WORLD_WIDTH}   낙서 {player.doodle_count}   지우개 {player.eraser_count}',
              (60, 70, 60))
    pico2d.update_canvas()
