"""보스1 전용 행동과 공격 패턴."""

import random

import pico2d
from core import game_world
from projectiles.bullet import Bullet
from actors.enemy import TestEnemy
from projectiles.homing_missile import HomingMissile
from projectiles.sweep_laser import SweepLaser
from graphics.boss_sprite import BossSprite, BossDeath, animation_for, rest_pose


class Boss1(TestEnemy):
    NAME = '보스1'
    BARRAGE_ATTACK_NAME = '탄막 공격'
    NORMAL_ATTACK_NAME = '일반 공격'
    HOMING_ATTACK_NAME = '유도탄 공격'
    LASER_ATTACK_NAME = '레이저 공격'
    WIDTH = 216
    HEIGHT = 168
    PROJECTILE_SCALE = 1.5
    BARRAGE_HEIGHTS = (12, 36, 60, 84, 108, 132)
    REST_HEIGHT = HEIGHT / 2
    FIRE_INTERVAL = 0.45
    VOLLEYS_PER_BURST = 6
    PHASE_DURATIONS = {'attack': FIRE_INTERVAL * VOLLEYS_PER_BURST, 'rest': 4.0}
    BULLET_SPEED = 200.0
    REST_MIN_HEIGHT = 72
    REST_MAX_HEIGHT = 152
    REST_INTERVAL_RANGE = (0.08, 0.14)
    REST_BULLET_SPEED = 300.0
    NORMAL_PHASE_DURATIONS = {'normal_burst': 0.54, 'normal_pause': 0.9,
                              'normal_parry': 2.5}
    NORMAL_FIRE_INTERVAL = 0.18
    NORMAL_BURST_SHOTS = 3
    NORMAL_CYCLES = 2
    NORMAL_MOVE_SPEED = 70.0
    HOMING_PHASE_DURATIONS = {'homing_launch': 1.4, 'homing_recover': 1.0}
    HOMING_FIRE_INTERVAL = 0.7
    HOMING_SHOTS = 2
    LASER_PHASE_DURATIONS = {'laser_charge': 3.0, 'laser_recover': 1.0}

    def __init__(self, world_width, world_height, ground_y, rng=None, laser_only=False,
                 shuffle_patterns=True):
        super().__init__(world_width, world_height, ground_y)
        self.sprite = BossSprite()
        self.hit_elapsed = 1.0
        self.ground_y = ground_y
        self.y = ground_y + self.HEIGHT / 2
        self.state = 'attack'
        self.state_time = 0.0
        self.fire_timer = 0.0
        self.volley_index = 0
        self.burst_shots = 0
        self.rest_shots = 0
        self.rng = rng if rng is not None else random.Random()
        self.pattern = 'barrage'
        self.normal_cycles = 0
        self.normal_shots = 0
        self.normal_motion_time = 0.0
        self.normal_parry_fired = False
        self.homing_shots = 0
        self.homing_parry_fired = False
        self.homing_reward_index = 0
        self.world_height = world_height
        self.laser = None
        self.laser_only = laser_only
        self.shuffle_patterns = shuffle_patterns
        self.pattern_queue = []
        if self.laser_only:
            self.start_pattern('laser')
        elif self.shuffle_patterns:
            self.pattern_queue = ['barrage', 'homing', 'laser']
            self.rng.shuffle(self.pattern_queue)
            self.start_pattern('normal')

    def start_pattern(self, pattern):
        self.pattern = pattern
        self.state = {'barrage': 'attack', 'normal': 'normal_burst',
                      'homing': 'homing_launch', 'laser': 'laser_charge'}[pattern]
        self.state_time = self.fire_timer = 0.0
        self.y = self.min_y
        self.burst_shots = self.rest_shots = 0
        self.normal_cycles = self.normal_shots = 0
        self.normal_motion_time = 0.0
        self.normal_parry_fired = False
        self.homing_shots = 0
        self.homing_parry_fired = False
        self.laser = None

    def take_damage(self, amount):
        if self.hp <= 0 or amount <= 0:
            return
        self.hit_elapsed = 0.0
        super().take_damage(amount)
        if self.hp == 0:
            left, bottom, right, _ = self.get_bb()
            bounds = (left, bottom, right, bottom + self.HEIGHT)
            game_world.add_object(BossDeath(self.sprite, bounds), game_world.EFFECTS)

    def choose_next_pattern(self):
        if self.laser_only:
            self.start_pattern('laser')
            return
        if not self.shuffle_patterns:
            self.start_pattern({'barrage': 'normal', 'normal': 'homing',
                                'homing': 'laser', 'laser': 'barrage'}[self.pattern])
            return
        if not self.pattern_queue:
            self.pattern_queue = ['normal', 'barrage', 'homing', 'laser']
            self.rng.shuffle(self.pattern_queue)
            if self.pattern_queue[0] == self.pattern:
                self.pattern_queue[0], self.pattern_queue[1] = self.pattern_queue[1], self.pattern_queue[0]
        self.start_pattern(self.pattern_queue.pop(0))

    @property
    def attack_name(self):
        return {'normal': self.NORMAL_ATTACK_NAME, 'barrage': self.BARRAGE_ATTACK_NAME,
                'homing': self.HOMING_ATTACK_NAME, 'laser': self.LASER_ATTACK_NAME}[self.pattern]

    @property
    def body_height(self):
        return self.REST_HEIGHT if self.state == 'rest' else self.HEIGHT

    def get_bb(self):
        bottom = self.y - self.HEIGHT / 2 if self.pattern == 'normal' else self.ground_y
        return (self.x - self.WIDTH / 2, bottom,
                self.x + self.WIDTH / 2, bottom + self.body_height)

    def advance_phase(self):
        if self.pattern == 'laser':
            if self.state == 'laser_charge':
                self.state = 'laser_sweep'
                self.laser = SweepLaser(self.world_width, self.world_height, self.ground_y)
                self.laser.sprite_bank = self.sprite
                game_world.add_object(self.laser, game_world.PROJECTILES)
            elif self.state == 'laser_sweep':
                self.state = 'laser_recover'
            else:
                self.choose_next_pattern()
        elif self.pattern == 'homing':
            if self.state == 'homing_launch':
                self.state = 'homing_wait'
            elif self.state == 'homing_wait':
                self.state = 'homing_parry'
                self.homing_parry_fired = False
            elif self.state == 'homing_parry':
                self.state = 'homing_recover'
            else:
                self.choose_next_pattern()
        elif self.pattern == 'normal':
            if self.state == 'normal_burst':
                self.state = 'normal_pause'
            elif self.state == 'normal_pause':
                self.state = 'normal_parry'
                self.normal_parry_fired = False
            else:
                self.normal_cycles += 1
                if self.normal_cycles >= self.NORMAL_CYCLES:
                    self.choose_next_pattern()
                else:
                    self.state = 'normal_burst'
                    self.normal_shots = 0
        elif self.state == 'attack':
            self.state = 'rest'
        else:
            self.choose_next_pattern()
        if self.pattern != 'normal':
            self.y = self.ground_y + self.body_height / 2
        self.state_time = 0.0
        self.fire_timer = 0.0
        if self.state == 'attack':
            self.burst_shots = 0
        elif self.state == 'rest':
            self.rest_shots = 0

    def has_hostile_projectiles(self):
        return any(isinstance(obj, Bullet) and obj.team == 'enemy' and obj.active
                   for obj in game_world.objects(game_world.PROJECTILES))

    def fire_homing_missile(self, reward=None):
        target = next((obj for obj in game_world.objects(game_world.ACTORS)
                       if getattr(obj, 'team', None) == 'player' and obj.hp > 0), None)
        height = self.ground_y + (90 if reward else 70)
        missile = HomingMissile(self.x - self.WIDTH / 2 - 14, height,
                                target, self.world_width, parry_reward=reward)
        missile.WIDTH *= self.PROJECTILE_SCALE
        missile.HEIGHT *= self.PROJECTILE_SCALE
        missile.x = self.x - self.WIDTH / 2 - missile.WIDTH / 2
        missile.sprite_bank = self.sprite
        game_world.add_object(missile, game_world.PROJECTILES)
        return missile

    def update_normal(self, dt):
        self.normal_motion_time += dt
        span = self.max_y - self.min_y
        travel = (self.normal_motion_time * self.NORMAL_MOVE_SPEED) % (2 * span)
        self.y = self.min_y + span - abs(span - travel)
        if self.state == 'normal_burst':
            self.fire_timer -= dt
            while self.fire_timer <= 0 and self.normal_shots < self.NORMAL_BURST_SHOTS:
                self.fire_normal_bullet()
                self.normal_shots += 1
                self.fire_timer += self.NORMAL_FIRE_INTERVAL
        elif self.state == 'normal_parry' and not self.normal_parry_fired:
            self.fire_normal_bullet(('doodle', 'eraser')[self.normal_cycles % 2])
            self.normal_parry_fired = True

    def fire_normal_bullet(self, reward=None):
        height = self.y - self.HEIGHT / 2 + 28
        if reward is not None:
            # 점프로 닿을 수 있는 높이에서 단독 발사한다.
            height = min(self.ground_y + 130, max(self.ground_y + 90, height))
        bullet = Bullet(self.x - self.WIDTH / 2 - Bullet.WIDTH / 2,
                        height, -1, self.team, self.world_width, parry_reward=reward)
        bullet.WIDTH *= self.PROJECTILE_SCALE
        bullet.HEIGHT *= self.PROJECTILE_SCALE
        bullet.x = self.x - self.WIDTH / 2 - bullet.WIDTH / 2
        bullet.sprite_bank = self.sprite
        game_world.add_object(bullet, game_world.PROJECTILES)

    def fire_volley(self):
        self.fire_rows(self.BARRAGE_HEIGHTS, self.BULLET_SPEED)
        self.volley_index += 1

    def fire_rest_volley(self):
        height = self.rng.uniform(self.REST_MIN_HEIGHT, self.REST_MAX_HEIGHT)
        self.fire_rows((height,), self.REST_BULLET_SPEED)
        self.rest_shots += 1

    def fire_rows(self, heights, speed):
        for height in heights:
            bullet = Bullet(self.x - self.WIDTH / 2 - Bullet.WIDTH / 2,
                            self.ground_y + height, -1, self.team,
                            self.world_width)
            bullet.WIDTH *= self.PROJECTILE_SCALE
            bullet.HEIGHT = 14 * self.PROJECTILE_SCALE
            bullet.x = self.x - self.WIDTH / 2 - bullet.WIDTH / 2
            bullet.sprite_bank = self.sprite
            bullet.speed = speed
            game_world.add_object(bullet, game_world.PROJECTILES)

    def update(self, dt):
        if self.hp <= 0:
            return
        self.hit_elapsed += max(0, dt)
        remaining = max(0, dt)
        while remaining > 0:
            if self.pattern == 'laser' and self.state == 'laser_sweep':
                if self.laser is not None and self.laser.active:
                    self.state_time += remaining
                    break
                self.advance_phase()
                continue
            if self.pattern == 'homing' and self.state in ('homing_wait', 'homing_parry'):
                if self.state == 'homing_parry' and not self.homing_parry_fired:
                    reward = ('doodle', 'eraser')[self.homing_reward_index % 2]
                    self.fire_homing_missile(reward)
                    self.homing_reward_index += 1
                    self.homing_parry_fired = True
                if self.has_hostile_projectiles():
                    self.state_time += remaining
                    break
                self.advance_phase()
                continue
            durations = (self.NORMAL_PHASE_DURATIONS if self.pattern == 'normal'
                         else self.HOMING_PHASE_DURATIONS if self.pattern == 'homing'
                         else self.LASER_PHASE_DURATIONS if self.pattern == 'laser'
                         else self.PHASE_DURATIONS)
            duration = durations[self.state]
            step = min(remaining, duration - self.state_time)
            if self.pattern == 'normal':
                self.update_normal(step)
            elif self.pattern == 'homing' and self.state == 'homing_launch':
                self.fire_timer -= step
                while self.fire_timer <= 0 and self.homing_shots < self.HOMING_SHOTS:
                    self.fire_homing_missile()
                    self.homing_shots += 1
                    self.fire_timer += self.HOMING_FIRE_INTERVAL
            elif self.state == 'attack':
                self.fire_timer -= step
                while self.fire_timer <= 0 and self.burst_shots < self.VOLLEYS_PER_BURST:
                    self.fire_volley()
                    self.burst_shots += 1
                    self.fire_timer += self.FIRE_INTERVAL
            elif self.state == 'rest':
                self.fire_timer -= step
                while self.fire_timer <= 0:
                    self.fire_rest_volley()
                    self.fire_timer += self.rng.uniform(*self.REST_INTERVAL_RANGE)
            self.state_time += step
            remaining -= step
            if self.state_time >= duration:
                self.advance_phase()

    def draw(self):
        left, bottom, right, top = self.get_bb()
        name, elapsed = (rest_pose(self) if self.state == 'rest'
                         else (animation_for(self), self.state_time))
        self.sprite.draw_body(name, elapsed, (left, bottom, right, bottom + self.HEIGHT))
        if self.hit_elapsed < 1 / 3:
            self.sprite.draw_effect('hit_overlay', self.hit_elapsed,
                                    self.x, (bottom + top) / 2, 48, 40)
        pico2d.draw_rectangle(left, top + 8,
                              left + self.WIDTH * self.hp / self.MAX_HP,
                              top + 14, 180, 40, 40, filled=True)
