"""레이저 왕복과 낙서 보존·발판 삭제 낙하·피격 범위 검사."""

import unittest

from core import game_world
from doodle import Doodle
from player import Player
from sweep_laser import SweepLaser


class SweepLaserTests(unittest.TestCase):
    def setUp(self):
        game_world.clear()
        self.laser = SweepLaser(960, 540, 80)
        game_world.add_object(self.laser, game_world.PROJECTILES)

    def tearDown(self):
        game_world.clear()

    def test_thinner_than_doodle_and_faster_than_normal_missile(self):
        self.assertLess(self.laser.THICKNESS, Doodle.HEIGHT)
        self.assertGreater(self.laser.SPEED, 150)
        self.assertLess(self.laser.SAFE_EDGE, Doodle.WIDTH)
        self.assertGreaterEqual(self.laser.SAFE_EDGE, Player.WIDTH)

    def test_up_down_preserves_doodles_at_all_legal_screen_edges(self):
        for x in (44, 250, 916):
            for y in (96, 160, 300, 524):
                game_world.add_object(Doodle(x, y), game_world.TERRAIN)
        ascent = (self.laser.top_y - self.laser.bottom_y) / self.laser.SPEED
        self.laser.update(ascent)
        self.assertEqual(self.laser.y, self.laser.top_y)
        self.assertEqual(self.laser.direction, -1)
        self.assertEqual(len(game_world.objects(game_world.TERRAIN)), 12)
        self.assertTrue(all(obj.hp == 20 for obj in game_world.objects(game_world.TERRAIN)))
        new = Doodle(250, 300)
        game_world.add_object(new, game_world.TERRAIN)
        self.laser.update(ascent + .01)
        self.assertEqual(len(game_world.objects(game_world.TERRAIN)), 13)
        self.assertEqual(new.hp, 20)
        self.assertFalse(self.laser.active)
        self.assertNotIn(self.laser, game_world.objects(game_world.PROJECTILES))

    def test_laser_does_not_remove_support_but_still_damages_player(self):
        platform = Doodle(300, 160)
        game_world.add_object(platform, game_world.TERRAIN)
        player = Player(300, 80, 960)
        player.y = 204
        game_world.add_object(player, game_world.ACTORS)
        self.laser.update(.64)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        player.update(.02)
        self.assertTrue(player.grounded)
        self.assertEqual(player.y, 204)
        self.assertEqual(player.hp, 4)

    def test_upward_doodle_survives_before_during_and_after_overlap(self):
        platform = Doodle(250, 160)  # 아래 144, 위 176
        game_world.add_object(platform, game_world.TERRAIN)
        self.laser.y = 120
        self.laser.update(.1)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.laser.update(.2)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.laser.update(.06)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.assertEqual(platform.hp, 20)

    def test_downward_doodle_survives_before_during_and_after_overlap(self):
        platform = Doodle(250, 160)
        game_world.add_object(platform, game_world.TERRAIN)
        self.laser.y = 200
        self.laser.direction = -1
        self.laser.update(.1)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.laser.update(.2)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.laser.update(.06)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.assertEqual(platform.hp, 20)

    def test_down_eraser_drop_can_gain_space_from_descending_laser(self):
        from eraser import Eraser
        import pico2d
        platform = Doodle(300, 250)
        game_world.add_object(platform, game_world.TERRAIN)
        player = Player(300, 80, 960)
        player.y = 294
        player.pressed_keys.add(pico2d.SDLK_DOWN)
        player.update(.001)
        game_world.add_object(player, game_world.ACTORS)
        eraser = Eraser(player.x, player.y, 1, 960, downward=True, ground_y=80)
        game_world.add_object(eraser, game_world.PROJECTILES)
        self.laser.y, self.laser.direction = 430, -1
        for _ in range(40):
            game_world.update(.01)
        self.assertNotIn(platform, game_world.objects(game_world.TERRAIN))
        self.assertLess(player.get_bb()[1], 266)
        self.assertEqual(player.hp, 5)
        for _ in range(180):
            game_world.update(.01)
        self.assertFalse(self.laser.active)
        self.assertEqual(player.x, 300)
        self.assertTrue(player.crouching)
        self.assertEqual(player.hp, 5)

    def test_descent_stops_above_crouched_head_but_hits_standing_player(self):
        import pico2d
        standing = Player(300, 80, 960)
        crouched = Player(500, 80, 960)
        crouched.pressed_keys.add(pico2d.SDLK_DOWN)
        crouched.update(.001)
        for player in (standing, crouched):
            game_world.add_object(player, game_world.ACTORS)
        self.laser.y = 200
        self.laser.direction = -1
        self.laser.update(1)
        self.assertFalse(self.laser.active)
        self.assertEqual(self.laser.y, self.laser.descent_end_y)
        self.assertGreater(self.laser.y - self.laser.THICKNESS / 2, crouched.get_bb()[3])
        self.assertLess(self.laser.y - self.laser.THICKNESS / 2, standing.get_bb()[3])
        self.assertEqual(crouched.hp, 5)
        self.assertEqual(standing.hp, 4)

    def test_player_edge_is_safe_and_contact_respects_existing_invincibility(self):
        safe = Player(18, 80, 960)
        exposed = Player(120, 80, 960)
        for player in (safe, exposed):
            game_world.add_object(player, game_world.ACTORS)
        self.laser.update(.1)
        self.assertEqual(safe.hp, 5)
        self.assertEqual(exposed.hp, 4)
        self.laser.update(.1)
        self.assertEqual(exposed.hp, 4)

    def test_falling_through_ascending_laser_is_not_automatically_invincible(self):
        player = Player(300, 80, 960)
        player.y = 294
        player.grounded = False
        game_world.add_object(player, game_world.ACTORS)
        self.laser.y = 200
        for _ in range(50):
            game_world.update(.01)
        self.assertLess(player.hp, 5)
