"""1번 보스 패턴: 예고 → 정해진 수의 탄막 → 휴식 → 반복."""

import pico2d
import game_world
from bullet import Bullet
from enemy import TestEnemy


class Boss(TestEnemy):
    FIRE_INTERVAL = 0.45
    VOLLEYS_PER_BURST = 6
    PHASE_DURATIONS = {'warning': 1.2, 'attack': FIRE_INTERVAL * VOLLEYS_PER_BURST,
                       'rest': 4.0}
    BULLET_SPEED = 200.0

    def __init__(self, world_width, world_height, ground_y):
        super().__init__(world_width, world_height, ground_y)
        self.ground_y = ground_y
        self.y = ground_y + self.HEIGHT / 2
        self.state = 'warning'
        self.state_time = 0.0
        self.fire_timer = 0.0
        self.volley_index = 0
        self.burst_shots = 0

    def take_damage(self, amount):
        if self.hp > 0:
            super().take_damage(amount)
            if self.hp == 0:
                self.clear_enemy_bullets()

    def clear_enemy_bullets(self):
        for obj in game_world.objects(game_world.PROJECTILES):
            if isinstance(obj, Bullet) and obj.team == self.team:
                obj.active = False
                game_world.remove_object(obj)

    def advance_phase(self):
        self.state = {'warning': 'attack', 'attack': 'rest', 'rest': 'warning'}[self.state]
        self.state_time = 0.0
        self.fire_timer = 0.0
        if self.state == 'attack':
            self.burst_shots = 0

    def fire_volley(self):
        reward = ('doodle', 'eraser')[self.volley_index % 2]
        for height, parry_reward in ((28, None), (76, reward), (118, None)):
            bullet = Bullet(self.x - self.WIDTH / 2 - Bullet.WIDTH / 2,
                            self.ground_y + height, -1, self.team,
                            self.world_width, parry_reward=parry_reward)
            bullet.speed = self.BULLET_SPEED
            game_world.add_object(bullet, game_world.PROJECTILES)
        self.volley_index += 1

    def update(self, dt):
        if self.hp <= 0:
            return
        remaining = max(0, dt)
        while remaining > 0:
            duration = self.PHASE_DURATIONS[self.state]
            step = min(remaining, duration - self.state_time)
            if self.state == 'attack':
                self.fire_timer -= step
                while self.fire_timer <= 0 and self.burst_shots < self.VOLLEYS_PER_BURST:
                    self.fire_volley()
                    self.burst_shots += 1
                    self.fire_timer += self.FIRE_INTERVAL
            self.state_time += step
            remaining -= step
            if self.state_time >= duration:
                self.advance_phase()

    def draw(self):
        super().draw()
        if self.state == 'warning':
            for height in (28, 76, 118):
                pico2d.draw_line(0, self.ground_y + height,
                                 self.x - self.WIDTH / 2, self.ground_y + height,
                                 210, 150, 100)
