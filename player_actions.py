"""횡스크롤과 보스 화면에서 공통으로 사용하는 낙서·지우개 조작."""

import pico2d
import game_world
from doodle import Doodle, overlaps
from eraser import Eraser


def spawn_doodle(player, world_width, world_height, ground_y):
    if player.hp <= 0 or player.doodle_count <= 0:
        return None
    if pico2d.SDLK_DOWN in player.pressed_keys:
        doodle = Doodle(player.x, player.get_bb()[1] - Doodle.UNDERFOOT_GAP - Doodle.HEIGHT / 2)
    else:
        distance = player.WIDTH / 2 + Doodle.SPAWN_GAP + Doodle.WIDTH / 2
        doodle = Doodle(player.x + player.facing * distance,
                        max(player.y, ground_y + Doodle.HEIGHT / 2))
    bounds = doodle.get_bb()
    if (bounds[0] < 0 or bounds[2] > world_width
            or bounds[1] < ground_y or bounds[3] > world_height):
        return None
    occupied = [obj.get_bb() for obj in game_world.objects(game_world.TERRAIN)]
    occupied.extend(obj.get_bb() for obj in game_world.objects(game_world.ACTORS))
    if any(overlaps(bounds, other) for other in occupied):
        return None
    game_world.add_object(doodle, game_world.TERRAIN)
    player.doodle_count -= 1
    return doodle


def throw_eraser(player, world_width, ground_y):
    if player.hp <= 0 or player.eraser_count <= 0:
        return None
    downward = (pico2d.SDLK_DOWN in player.pressed_keys
                and player.get_bb()[1] > ground_y + 0.001)
    eraser = Eraser(player.x, player.y, player.facing, world_width,
                    downward=downward, ground_y=ground_y)
    game_world.add_object(eraser, game_world.PROJECTILES)
    player.eraser_count -= 1
    return eraser
