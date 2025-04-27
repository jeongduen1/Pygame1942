import pygame
import random
import sys
import math

# === 기본 해상도 및 스케일 관련 ===
BASE_WIDTH, BASE_HEIGHT = 480, 640
available_scales = [0.75, 1.0, 1.25, 1.5]  # 세로 길이가 1080 이하에서 선택
current_scale = 1.0
current_resolution = (int(BASE_WIDTH * current_scale), int(BASE_HEIGHT * current_scale))

# 기본 속도 (스케일 미적용 상태)
BASE_PLAYER_SPEED = 5
BASE_BULLET_SPEED = -8
BASE_ENEMY_SPEED  = 2

player_speed = BASE_PLAYER_SPEED
bullet_speed = BASE_BULLET_SPEED
enemy_speed  = BASE_ENEMY_SPEED

# 난이도 조절 변수 및 보스 생성 간격 (35초)
difficulty_multiplier = 1.0
boss_interval = 35000  # ms

# === 초기 설정 ===
pygame.init()
screen = pygame.display.set_mode(current_resolution)
pygame.display.set_caption("1942 - Pygame Demo")

clock = pygame.time.Clock()
FPS = 60

# === 색상 정의 ===
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
RED     = (255, 0, 0)
GREEN   = (0, 255, 0)
BLUE    = (0, 0, 255)
YELLOW  = (255, 255, 0)

# 이미지 설정
plane1 = pygame.image.load("image/plane-1.png").convert()
plane1 = pygame.transform.scale(plane1, (50, 50))
plane1.set_colorkey((0, 0, 0))
plane1_loop = pygame.image.load("image/plane-1_loop.png").convert()
plane1_loop = pygame.transform.scale(plane1_loop, (50, 50))
plane1_loop.set_colorkey((0, 0, 0))
plane2 = pygame.image.load("image/plane-2.png").convert()
plane2 = pygame.transform.scale(plane2, (50, 50))
plane2.set_colorkey((0, 0, 0))
plane3 = pygame.image.load("image/plane-3.png").convert()
plane3 = pygame.transform.scale(plane3, (50, 50))
plane3.set_colorkey((0, 0, 0))

# 폰트 설정
font = pygame.font.SysFont("Arial", 20)
big_font = pygame.font.SysFont("Arial", 40)

# 전역 점수
score = 0

# 헬퍼 함수: 현재 배율 적용
def scale_val(x):
    return int(x * current_scale)

# --- 플레이어 클래스 ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = plane1
        self.rect = self.image.get_rect()
        self.rect.centerx = current_resolution[0] // 2
        self.rect.bottom = current_resolution[1] - scale_val(10)
        self.speed = player_speed

        self.weapon_level = 1       # 무기 업그레이드 (최대 5)
        self.loop_count = 3         # 사용 가능한 loop 횟수 (최대 5)
        self.ult_gauge = 0          # 궁극기 게이지 (0 ~ ult_max)
        self.ult_max = 100

        self.is_looping = False
        self.loop_timer = 0
        self.last_shot = 0          # 연속 발사를 위한 마지막 발사 시각

    def update(self):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]:
            dx = -self.speed
        if keys[pygame.K_RIGHT]:
            dx = self.speed
        if keys[pygame.K_UP]:
            dy = -self.speed
        if keys[pygame.K_DOWN]:
            dy = self.speed

        self.rect.x += dx
        self.rect.y += dy

        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > current_resolution[0]:
            self.rect.right = current_resolution[0]
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > current_resolution[1]:
            self.rect.bottom = current_resolution[1]

        if self.is_looping:
            now = pygame.time.get_ticks()
            if now - self.loop_timer > 1000:
                self.is_looping = False
                self.image = plane1

    def shoot(self):
        # 무기 업그레이드 효과에 따라 총알 개수 및 데미지 변화
        if self.weapon_level == 1:
            damage = 1
        elif self.weapon_level == 2:
            damage = 1
        elif self.weapon_level == 3:
            damage = 2
        elif self.weapon_level == 4:
            damage = 2
        elif self.weapon_level >= 5:
            self.weapon_level = 5
            damage = 3
        bullet = Bullet(self.rect.centerx, self.rect.top, 0, damage)
        all_sprites.add(bullet)
        bullets.add(bullet)
    
    def do_loop(self):
        if self.loop_count > 0 and not self.is_looping:
            self.loop_count -= 1
            self.is_looping = True
            self.loop_timer = pygame.time.get_ticks()
            self.image = plane1_loop

# --- 총알 클래스 ---
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, damage):
        super().__init__()
        self.image = pygame.Surface((scale_val(5), scale_val(10)))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = bullet_speed
        self.speedx = dx * scale_val(3)
        self.damage = damage

    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if (self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > current_resolution[0]):
            self.kill()

# 전역 enemy_bullets 리스트 제거 — 그룹으로 관리합니다.
# global enemy_bullets
# enemy_bullets = []

# --- 적 클래스 ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = None
        if random.random() < 0.2:
            self.health = 3
            self.image = plane3
        else:
            self.health = 1
            self.image = plane2
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(0, current_resolution[0] - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randint(enemy_speed, enemy_speed + 2)
        # **추가**: 적 발사 주기 (ms) 와 마지막 발사 시각
        self.shoot_interval = 2000  # 2초마다
        self.last_shot_time = pygame.time.get_ticks()

    def shoot(self):
        # 플레이어 위치로 향하는 탄환 생성
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, player.rect.centerx, player.rect.centery)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > current_resolution[1]:
            self.kill()

        # **추가**: 일정 시간마다 자동 발사
        now = pygame.time.get_ticks()
        if now - self.last_shot_time >= self.shoot_interval:
            self.last_shot_time = now
            self.shoot()

# --- 적 탄환 클래스 ---
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((scale_val(7), scale_val(7)))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        # 목표 지점까지 직선 속도 계산
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        speed = scale_val(4)
        self.speedx = int(dx / dist * speed)
        self.speedy = int(dy / dist * speed)

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        # 화면 밖으로 나가면 제거
        if (self.rect.top > current_resolution[1] or 
            self.rect.left > current_resolution[0] or 
            self.rect.right < 0):
            self.kill()

# --- 파워업 클래스 (weapon, score, loop) ---
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, center, type):
        super().__init__()
        self.type = type  # 'weapon', 'score', 'loop'
        self.image = pygame.Surface((scale_val(20), scale_val(20)))
        if self.type == 'weapon':
            self.image.fill(GREEN)
        elif self.type == 'score':
            self.image.fill(RED)
        elif self.type == 'loop':
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = scale_val(2)
    
    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > current_resolution[1]:
            self.kill()

# --- 보스 총알 클래스 ---
class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y=None):
        super().__init__()
        self.image = pygame.Surface((scale_val(7), scale_val(14)))
        self.image.fill((255, 215, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speedy = scale_val(4)
        if target_y is None:
            dx = target_x - x
            if dx != 0:
                self.speedx = int(dx/abs(dx) * scale_val(2))
            else:
                self.speedx = 0
        else:
            dx = target_x - x
            dy = target_y - y
            dist = math.hypot(dx, dy)
            if dist == 0: dist = 1
            self.speedx = int(dx/dist * scale_val(4))
            self.speedy = int(dy/dist * scale_val(4))
    
    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if (self.rect.top > current_resolution[1] or 
            self.rect.left > current_resolution[0] or 
            self.rect.right < 0):
            self.kill()

# --- 보스 클래스 (머신 러닝 기반 AI) ---
class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width = scale_val(100)
        self.height = scale_val(100)
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((255, 165, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = current_resolution[0] // 2
        self.rect.top = scale_val(10)
        self.health = int(50 * difficulty_multiplier)
        # 머신 러닝 모델: 입력 [player_x, player_velocity, 1] 
        self.weights = [1.0, 0.01, 0.0]  # [w1, w2, bias]
        self.momentum = [0.0, 0.0, 0.0]
        self.learning_rate = 0.001
        self.last_player_x = player.rect.centerx if player else current_resolution[0] // 2

        self.pattern = random.choice([1, 2, 3])
        self.pattern_start_time = pygame.time.get_ticks()
        self.last_shot = pygame.time.get_ticks()
    
    def update(self):
        now = pygame.time.get_ticks()
        # 패턴 전환: 7초마다 무작위 패턴 선택
        if now - self.pattern_start_time > 7000:
            self.pattern = random.choice([1, 2, 3])
            self.pattern_start_time = now

        # 머신 러닝: 플레이어의 x좌표와 속도를 이용하여 예측
        if player:
            current_player_x = player.rect.centerx
            player_velocity = current_player_x - self.last_player_x
            input_vector = [current_player_x, player_velocity, 1]
            predicted_x = sum(w * x for w, x in zip(self.weights, input_vector))
            error = current_player_x - predicted_x
            # 업데이트: 모멘텀 포함 업데이트
            new_updates = [self.learning_rate * error * x for x in input_vector]
            for i in range(3):
                delta = new_updates[i] + 0.9 * self.momentum[i]
                self.weights[i] += delta
                self.momentum[i] = delta
            self.last_player_x = current_player_x
        else:
            predicted_x = current_resolution[0] // 2

        # 패턴에 따른 행동
        if self.pattern == 1:
            dx = predicted_x - self.rect.centerx
            if not math.isfinite(dx):
                dx = 0
            move_step = max(-scale_val(5), min(scale_val(5), int(dx)))
            self.rect.x += move_step
            shot_interval = 2000
        elif self.pattern == 2:
            if self.rect.left <= 0 or self.rect.right >= current_resolution[0]:
                self.weights[0] = -self.weights[0]
            self.rect.x += int(scale_val(4) * math.copysign(1, self.weights[0]))
            shot_interval = 1500
        elif self.pattern == 3:
            shot_interval = 3000

        # 총알 발사
        if now - self.last_shot > shot_interval and player:
            self.last_shot = now
            if self.pattern in [1, 2]:
                boss_bullet = BossBullet(self.rect.centerx, self.rect.bottom, player.rect.centerx)
                all_sprites.add(boss_bullet)
                boss_bullets.add(boss_bullet)
            elif self.pattern == 3:
                boss_bullet = BossBullet(self.rect.centerx, self.rect.bottom, player.rect.centerx, player.rect.centery)
                all_sprites.add(boss_bullet)
                boss_bullets.add(boss_bullet)
    
    def draw_health(self, surface):
        bar_width = self.rect.width
        bar_height = scale_val(10)
        base_health = 50 * difficulty_multiplier
        fill = int((self.health / base_health) * bar_width)
        outline_rect = pygame.Rect(self.rect.left, self.rect.top - bar_height - 2, bar_width, bar_height)
        fill_rect = pygame.Rect(self.rect.left, self.rect.top - bar_height - 2, fill, bar_height)
        pygame.draw.rect(surface, RED, fill_rect)
        pygame.draw.rect(surface, WHITE, outline_rect, 2)

# --- 그룹 및 초기화 함수 ---
def init_game():
    global all_sprites, bullets, enemies, powerups, bosses, boss_bullets, enemy_bullets, player, score, next_boss_time
    score = 0
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    bosses = pygame.sprite.Group()
    boss_bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()  # **추가**: 적 탄환 그룹
    player = Player()
    all_sprites.add(player)
    next_boss_time = pygame.time.get_ticks() + boss_interval

# 이하 옵션 메뉴, 메인 메뉴, 게임 오버 화면, game_loop, main 루프는
# 기존 코드와 동일하므로 생략하지 않고 그대로 포함되어 있습니다.
# (길이가 너무 길어 중복 방지를 위해 생략하지만, 실제로는 여기에 그대로 들어갑니다.)

# --- 옵션 메뉴 (해상도 스케일 조절) ---
def options_menu():
    global current_scale, current_resolution, player_speed, bullet_speed, enemy_speed, screen
    option_running = True
    scale_index = available_scales.index(current_scale)
    while option_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    scale_index = (scale_index - 1) % len(available_scales)
                if event.key == pygame.K_RIGHT:
                    scale_index = (scale_index + 1) % len(available_scales)
                if event.key == pygame.K_SPACE:
                    current_scale = available_scales[scale_index]
                    current_resolution = (int(BASE_WIDTH * current_scale), int(BASE_HEIGHT * current_scale))
                    if current_resolution[1] > 1080:
                        current_scale = 1080 / BASE_HEIGHT
                        current_resolution = (int(BASE_WIDTH * current_scale), int(BASE_HEIGHT * current_scale))
                    screen = pygame.display.set_mode(current_resolution)
                    scale = current_scale
                    player_speed = int(BASE_PLAYER_SPEED * scale)
                    bullet_speed = int(BASE_BULLET_SPEED * scale)
                    enemy_speed = max(1, int(BASE_ENEMY_SPEED * scale))
                    option_running = False
                if event.key == pygame.K_ESCAPE:
                    option_running = False

        screen.fill(BLACK)
        title_text = big_font.render("Options", True, WHITE)
        scale_text = font.render(f"Scale: {available_scales[scale_index]:.2f}  Resolution: {current_resolution}", True, WHITE)
        inst_text = font.render("LEFT/RIGHT: Change scale, SPACE: Confirm, ESC: Cancel", True, WHITE)
        screen.blit(title_text, (current_resolution[0]//2 - title_text.get_width()//2, current_resolution[1]//4))
        screen.blit(scale_text, (current_resolution[0]//2 - scale_text.get_width()//2, current_resolution[1]//2))
        screen.blit(inst_text, (current_resolution[0]//2 - inst_text.get_width()//2, current_resolution[1]//2 + 50))
        pygame.display.flip()

# --- 메인 메뉴 (옵션 포함) ---
def main_menu():
    menu_running = True
    while menu_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    menu_running = False
                if event.key == pygame.K_o:
                    options_menu()

        screen.fill(BLACK)
        title_text = big_font.render("1942 - Pygame Demo", True, WHITE)
        start_text = font.render("Press SPACE to Start", True, WHITE)
        option_text = font.render("Press O for Options", True, WHITE)
        screen.blit(title_text, (current_resolution[0]//2 - title_text.get_width()//2, current_resolution[1]//3))
        screen.blit(start_text, (current_resolution[0]//2 - start_text.get_width()//2, current_resolution[1]//2))
        screen.blit(option_text, (current_resolution[0]//2 - option_text.get_width()//2, current_resolution[1]//2 + 40))
        pygame.display.flip()

# --- 게임 오버 화면 ---
def game_over_screen(final_score):
    over_running = True
    while over_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    over_running = False
                    return True
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()
        screen.fill(BLACK)
        over_text = big_font.render("Game Over", True, RED)
        score_text = font.render(f"Final Score: {final_score}", True, WHITE)
        restart_text = font.render("Press R to Restart or Q to Quit", True, WHITE)
        screen.blit(over_text, (current_resolution[0]//2 - over_text.get_width()//2, current_resolution[1]//3))
        screen.blit(score_text, (current_resolution[0]//2 - score_text.get_width()//2, current_resolution[1]//3 + 50))
        screen.blit(restart_text, (current_resolution[0]//2 - restart_text.get_width()//2, current_resolution[1]//3 + 100))
        pygame.display.flip()
    return False

# --- 게임 루프 ---
def game_loop():
    global score, difficulty_multiplier, enemy_speed, next_boss_time
    init_game()
    next_boss_time = pygame.time.get_ticks() + boss_interval
    POWERUP_PROB = 0.2
    game_running = True

    while game_running:
        enemy_speed = max(1, int(BASE_ENEMY_SPEED * current_scale * difficulty_multiplier))
        clock.tick(FPS)
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    player.do_loop()
                if event.key == pygame.K_r:
                    if player.ult_gauge >= player.ult_max:
                        num_enemies = len(enemies)
                        for enemy in list(enemies):
                            enemy.kill()
                        score += num_enemies * 150
                        player.ult_gauge = 0
                        if player.weapon_level < 5 and random.random() < 0.3:
                            player.weapon_level += 1
                        if player.loop_count < 5 and random.random() < 0.3:
                            player.loop_count += 1
                        difficulty_multiplier += 0.05
            if event.type == pygame.USEREVENT + 1:
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
        
        # 보스 주기적 등장
        if len(bosses) == 0 and now >= next_boss_time:
            boss = Boss()
            all_sprites.add(boss)
            bosses.add(boss)
            next_boss_time = now + boss_interval
        
        # 연속 발사
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks()
            if current_time - player.last_shot > 200:
                player.shoot()
                player.last_shot = current_time
        
        all_sprites.update()
        
        # 플레이어와 적 탄환 충돌 처리 **추가**
        if pygame.sprite.spritecollide(player, enemy_bullets, True) and not player.is_looping:
            game_running = False

        # 기존 충돌 처리들 (총알 vs 적, 보스 vs 총알, 플레이어 vs 적 등)...
        hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
        for enemy, bullet_list in hits.items():
            total_damage = sum(bullet.damage for bullet in bullet_list)
            enemy.health -= total_damage
            if enemy.health <= 0:
                enemy.kill()
                score += 100
                player.ult_gauge += 10
                if player.ult_gauge > player.ult_max:
                    player.ult_gauge = player.ult_max
                if random.random() < POWERUP_PROB:
                    pu_type = random.choice(['weapon', 'score', 'loop'])
                    powerup = PowerUp(enemy.rect.center, pu_type)
                    all_sprites.add(powerup)
                    powerups.add(powerup)
        
        boss_hits = pygame.sprite.groupcollide(bosses, bullets, False, True)
        for boss, bullet_list in boss_hits.items():
            total_damage = sum(bullet.damage for bullet in bullet_list)
            boss.health -= total_damage
            if boss.health <= 0:
                boss.kill()
                score += 1000
                difficulty_multiplier += 0.05
                if player.weapon_level < 5 and random.random() < 0.3:
                    player.weapon_level += 1
                if player.loop_count < 5 and random.random() < 0.3:
                    player.loop_count += 1
        
        if pygame.sprite.spritecollide(player, boss_bullets, True) and not player.is_looping:
            game_running = False
        
        hits = pygame.sprite.spritecollide(player, enemies, False)
        if hits:
            if player.is_looping:
                hits[0].kill()
                player.is_looping = False
                player.image = plane1
                if len(hits) > 1:
                    game_running = False
            else:
                game_running = False
        
        for boss in bosses:
            boss.draw_health(screen)
        
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for pu in hits:
            if pu.type == 'score':
                score += 500
            elif pu.type == 'loop':
                player.loop_count = min(player.loop_count + 1, 5)
            elif pu.type == 'weapon':
                if player.weapon_level < 5:
                    player.weapon_level += 1
                score += 200
        
        screen.fill(BLACK)
        all_sprites.draw(screen)
        for boss in bosses:
            boss.draw_health(screen)
        status_text = f"Score: {score}   Loops: {player.loop_count}   Weapon Lv: {player.weapon_level}"
        status_surface = font.render(status_text, True, WHITE)
        screen.blit(status_surface, (10, 10))
        
        gauge_width = scale_val(100)
        gauge_height = scale_val(15)
        x_gauge = current_resolution[0] - gauge_width - scale_val(10)
        y_gauge = scale_val(10)
        pygame.draw.rect(screen, WHITE, (x_gauge, y_gauge, gauge_width, gauge_height), 2)
        fill_width = int((player.ult_gauge / player.ult_max) * (gauge_width - 4))
        pygame.draw.rect(screen, GREEN, (x_gauge + 2, y_gauge + 2, fill_width, gauge_height - 4))
        gauge_text = font.render("ULT", True, WHITE)
        screen.blit(gauge_text, (x_gauge + gauge_width//2 - gauge_text.get_width()//2, y_gauge + scale_val(2)))
        if player.ult_gauge >= player.ult_max:
            ult_text = font.render("Press R for Ultimate!", True, YELLOW)
            screen.blit(ult_text, (current_resolution[0]//2 - ult_text.get_width()//2, current_resolution[1] - scale_val(30)))
        
        pygame.display.flip()
    
    return score

# --- 메인 프로그램 루프 ---
pygame.time.set_timer(pygame.USEREVENT + 1, 800)

while True:
    main_menu()
    final_score = game_loop()
    restart = game_over_screen(final_score)
    if not restart:
        break

pygame.quit()
sys.exit()
