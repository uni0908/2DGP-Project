"""레이저 왕복, 화면 내 낙서 제거와 회피·피격 범위 검사."""

import unittest

import game_world
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

    def test_up_down_covers_doodles_at_all_legal_screen_edges(self):
        for x in (44, 250, 916):
            for y in (96, 160, 300, 524):
                game_world.add_object(Doodle(x, y), game_world.TERRAIN)
        ascent = (self.laser.top_y - self.laser.bottom_y) / self.laser.SPEED
        self.laser.update(ascent)
        self.assertEqual(self.laser.y, self.laser.top_y)
        self.assertEqual(self.laser.direction, -1)
        self.assertFalse(game_world.objects(game_world.TERRAIN))
        new = Doodle(250, 300)
        game_world.add_object(new, game_world.TERRAIN)
        self.laser.update(ascent + .01)
        self.assertFalse(game_world.objects(game_world.TERRAIN))
        self.assertFalse(self.laser.active)
        self.assertNotIn(self.laser, game_world.objects(game_world.PROJECTILES))

    def test_laser_destroys_full_health_support_and_player_falls(self):
        platform = Doodle(300, 160)
        game_world.add_object(platform, game_world.TERRAIN)
        player = Player(300, 80, 960)
        player.y = 204
        game_world.add_object(player, game_world.ACTORS)
        self.laser.update(.64)
        self.assertNotIn(platform, game_world.objects(game_world.TERRAIN))
        player.update(.02)
        self.assertFalse(player.grounded)
        self.assertLess(player.y, 204)

    def test_upward_doodle_survives_overlap_until_trailing_edge_passes(self):
        platform = Doodle(250, 160)  # 아래 144, 위 176
        game_world.add_object(platform, game_world.TERRAIN)
        self.laser.y = 120
        self.laser.update(.1)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.laser.update(.2)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.laser.update(.06)
        self.assertNotIn(platform, game_world.objects(game_world.TERRAIN))

    def test_downward_doodle_survives_overlap_until_trailing_edge_passes(self):
        platform = Doodle(250, 160)
        game_world.add_object(platform, game_world.TERRAIN)
        self.laser.y = 200
        self.laser.direction = -1
        self.laser.update(.1)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.laser.update(.2)
        self.assertIn(platform, game_world.objects(game_world.TERRAIN))
        self.laser.update(.06)
        self.assertNotIn(platform, game_world.objects(game_world.TERRAIN))

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
