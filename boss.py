"""1번 보스 패턴: 예고 → 탄막 → 낮은 약점 노출 → 반복."""

import pico2d
import game_world
from bullet import Bullet
from enemy import TestEnemy


class Boss(TestEnemy):
    PHASE_DURATIONS = {'warning': 1.2, 'attack': 4.0, 'rest': 4.0}
    FIRE_INTERVAL = 0.45
    BULLET_SPEED = 200.0

    def __init__(self, world_width, world_height, ground_y):
        super().__init__(world_width, world_height, ground_y)
        self.ground_y = ground_y
        self.y = ground_y + self.HEIGHT / 2
        self.state = 'warning'
        self.state_time = 0.0
        self.fire_timer = 0.0
        self.volley_index = 0

    def get_weak_bb(self):
        left = self.x - self.WIDTH / 2
        return (left, self.ground_y + 12, left + 28, self.ground_y + 44)

    def take_damage(self, amount):
        if self.state == 'rest' and self.hp > 0:
            super().take_damage(amount)
            if self.hp == 0:
                self.clear_enemy_bullets()

    def receive_bullet(self, bullet):
        _, bottom, _, top = self.get_weak_bb()
        if (bullet.team == 'player' and self.state == 'rest'
                and bullet.y + bullet.HEIGHT / 2 >= bottom
                and bullet.y - bullet.HEIGHT / 2 <= top):
            self.take_damage(bullet.DAMAGE)

    def clear_enemy_bullets(self):
        for obj in game_world.objects(game_world.PROJECTILES):
            if isinstance(obj, Bullet) and obj.team == self.team:
                obj.active = False
                game_world.remove_object(obj)

    def advance_phase(self):
        self.state = {'warning': 'attack', 'attack': 'rest', 'rest': 'warning'}[self.state]
        self.state_time = 0.0
        self.fire_timer = 0.0
        if self.state == 'rest':
            # 휴식 동안은 남은 탄에 맞지 않고 낙서 제거·반격을 시도할 수 있다.
            self.clear_enemy_bullets()

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
                while self.fire_timer <= 0:
                    self.fire_volley()
                    self.fire_timer += self.FIRE_INTERVAL
            self.state_time += step
            remaining -= step
            if self.state_time >= duration:
                self.advance_phase()

    def draw(self):
        super().draw()
        weak_color = (40, 200, 80) if self.state == 'rest' else (100, 100, 110)
        pico2d.draw_rectangle(*self.get_weak_bb(), *weak_color, filled=True)
        if self.state == 'warning':
            for height in (28, 76, 118):
                pico2d.draw_line(0, self.ground_y + height,
                                 self.x - self.WIDTH / 2, self.ground_y + height,
                                 210, 150, 100)
