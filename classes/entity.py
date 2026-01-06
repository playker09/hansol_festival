import pygame
import math
import random
import os
from scenes.map import MAP_WIDTH, MAP_HEIGHT  # 맵 크기 가져오기

ENEMY_COLOR = (255, 50, 50)
GREEN = (0, 255, 0)

ENEMY_SIZE = 30

# --- Culling / optimization defaults ---
EXPORB_MAX_AGE_MS = 60_000        # 경험치 오브가 없을 때 자동 삭제되는 시간 (ms)
EXPORB_CULL_DISTANCE = 3000      # 플레이어로부터 떨어진 경험치 오브 삭제 거리 (px)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_IMAGE_DIR = os.path.join(BASE_DIR, "assets", "image")
ASSET_SFX_DIR = os.path.join(BASE_DIR, "assets", "sfx")

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, size=30, speed=1.2, max_hp=2.7, damage=5, damage_cooldown=900):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join(ASSET_IMAGE_DIR, "enemy2.png")).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (50, 50))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.size = size
        self.speed = speed
        self.max_hp = max_hp
        self.hp = max_hp
        self.damage = damage
        self.damage_cooldown = damage_cooldown  # ms
        self.last_hit_time = 0  # 플레이어를 마지막으로 공격한 시간
        self.knockback_x = 0
        self.knockback_y = 0
        self.knockback_decay = 0.85  # 매 프레임마다 줄어드는 비율

        # 피격(붉게 깜박임) 관련
        self.last_hurt_time = 0
        self.hurt_flash_duration = 180  # ms

    def move(self, player_rect, enemies):
        self.rect.x += self.knockback_x
        self.rect.y += self.knockback_y
        # 매 프레임마다 줄어듦 (감속)
        self.knockback_x *= self.knockback_decay
        self.knockback_y *= self.knockback_decay
        
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        if distance != 0:
            dx /= distance
            dy /= distance
            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed

        # 다른 적들과 겹치지 않도록
        for enemy in enemies:
            if enemy is not self and self.rect.colliderect(enemy.rect):
                if self.rect.x < enemy.rect.x:
                    self.rect.x -= self.speed
                elif self.rect.x > enemy.rect.x:
                    self.rect.x += self.speed
                if self.rect.y < enemy.rect.y:
                    self.rect.y -= self.speed
                elif self.rect.y > enemy.rect.y:
                    self.rect.y += self.speed

    def can_attack(self, current_time):
        return current_time - self.last_hit_time >= self.damage_cooldown
    def deal_damage(self, player, current_time):
        """플레이어에게 피해를 주고 마지막 공격 시간 업데이트"""
        player.hp -= self.damage
        self.last_hit_time = current_time
        # 플레이어가 피격되었음을 표시하여 붉게 깜박이게 함
        try:
            player.last_hit_time = current_time
        except Exception:
            pass

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))

        # 피격 시 붉게 깜박임 - 투명 영역 보호
        now = pygame.time.get_ticks()
        elapsed = now - getattr(self, 'last_hurt_time', 0)
        if elapsed < self.hurt_flash_duration:
            ratio = 1.0 - (elapsed / self.hurt_flash_duration)
            alpha = int(150 * ratio)
            red_surf = self.image.copy()
            red_surf.fill((255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            rect = self.image.get_rect(topleft=self.rect.topleft)
            surface.blit(red_surf, camera.apply(rect))

        # 체력바
        bar_width = self.rect.width
        bar_height = 5
        bar_x = self.rect.centerx - bar_width // 2 - camera.offset_x
        bar_y = self.rect.top - 10 - camera.offset_y
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (0, 255, 0),(bar_x, bar_y, bar_width * hp_ratio, bar_height))

class FastEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, max_hp=2, size=30,speed=2.5, damage=3, damage_cooldown=500)
        self.original_image = pygame.image.load(os.path.join(ASSET_IMAGE_DIR, "enemy1.png")).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (50, 50))
        self.image = self.original_image.copy()

class TankEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, max_hp=30, speed=1, damage=7, damage_cooldown=1500, size=45)
        self.original_image = pygame.image.load(os.path.join(ASSET_IMAGE_DIR, "enemy3.png")).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.original_image.get_width()*0.9, self.original_image.get_height()*0.9))
        self.image = self.original_image.copy()

class ExpOrb(pygame.sprite.Sprite):
    def __init__(self, x, y, value=1):
        super().__init__()
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (0, 255, 0), (0, 0, 15, 15))
        self.rect = self.image.get_rect(center=(x, y))
        self.value = value
        self.absorbing = False
        self.target = None
        self.absorb_speed = 0
        # 생성 시각 기록
        self.created_at = pygame.time.get_ticks()

    def update(self, player=None):
        """흡수 동작을 수행하고, 오브가 너무 오래되었거나 플레이어로부터 멀리 떨어졌으면 삭제한다."""
        now = pygame.time.get_ticks()
        age = now - self.created_at

        # 아직 흡수되지 않는 오브일 때: 시간 또는 거리 기반 삭제
        if not self.absorbing:
            if age > EXPORB_MAX_AGE_MS:
                # 오래된 오브는 삭제
                self.kill()
                return
            if player is not None:
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > EXPORB_CULL_DISTANCE:
                    # 너무 멀리 있는 오브는 삭제
                    self.kill()
                    return

        # 흡수 중인 경우 기존 동작 유지
        if self.absorbing and self.target:
            px, py = self.target.rect.center
            ox, oy = self.rect.center   #  중심 좌표 사용
            dx, dy = px - ox, py - oy
            dist = math.hypot(dx, dy)   #  올바른 거리 계산

            if dist < 10:
                # 경험치 지급 및 효과음
                self.target.gain_exp(self.value)
                try:
                    s = pygame.mixer.Sound(os.path.join(ASSET_SFX_DIR, "exp1.mp3"))
                    s.set_volume(0.3)
                    s.play()
                except Exception:
                    pass
                self.kill()
            else:
                self.rect.x += dx / dist * self.absorb_speed
                self.rect.y += dy / dist * self.absorb_speed



    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))

class EMP_Tower(pygame.sprite.Sprite):
    def __init__(self, x, y, player=None, survive_time=30, game_start_time=None):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join(ASSET_IMAGE_DIR, "tower.png")).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.original_image.get_width()*1.7, self.original_image.get_height()*1.7))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        
        self.activated = False   # 최종 발동 여부
        self.active = False      # 플레이어가 활성화 시켰는지 여부
        self.survive_time = survive_time  # 버텨야 하는 시간(초)
        self.timer = 0           # 남은 시간
        self.font = pygame.font.SysFont(None, 32)
        self.player = player
        self.game_start_time = game_start_time
        # 흡수 반경 (px) 및 흡수 속도 — 출입 불가 링 반경과 동일하게 사용
        self.absorb_radius = 900
        self.absorb_speed = 15

        # 타워마다 개별 스폰 타이머 관리
        self.spawn_timer = 0  

        # 파동 이펙트 관련
        self.wave_active = False
        self.wave_radius = 0.0
        self.wave_duration = 0.8  # 초 단위: 파동이 최대 반경까지 확장되는 시간
        self.wave_max_radius = self.absorb_radius  # 파동의 최대 반경
        self.wave_speed = (self.wave_max_radius / self.wave_duration) if self.wave_duration > 0 else 0
        self._affected_enemies = set()  # 이미 파동에 의해 처리된 적 ID 저장
        self._pops = []  # 파동에 맞은 적 위치에서 잠깐 보여줄 이펙트 (pos, time, max_radius)
        self._wave_sfx = None  # 필요시 사운드 재생
        

    def start(self,towers):
        """플레이어가 타워와 상호작용하면 호출"""
        if not self.active and not self.activated:
            self.active = True
            active_towers = sum(1 for tower in towers if tower.activated)
            self.timer = self.survive_time + (active_towers * 10)

    def activate(self, enemies, exp_orbs, all_sprites):
        """타워 발동: 즉시 모두 제거하지 않고 확장하는 파동을 발생시켜 자연스럽게 적을 제거한다."""
        # 이미 발동 파동이 진행중이면 무시
        if self.wave_active or self.activated:
            return

        self.active = False
        self.wave_active = True
        self.wave_radius = 0.0
        self._affected_enemies = set()
        self._pops = []
        # 재생 사운드가 있으면 재생 (파일이 있으면 추가 가능)
        try:
            s = pygame.mixer.Sound(os.path.join(BASE_DIR, "assets", "sfx", "emp_wave.mp3"))
            s.set_volume(0.6)
            s.play()
        except Exception:
            pass

        # 파동 시작 시 약간의 카메라 이펙트나 다른 효과를 여기에 추가 가능
        # 파동은 update()에서 점진적으로 적을 처리함
        

    def update(self, dt, player, enemies, all_sprites, exp_orbs, current_time,towers):
        """타워 로직"""
        keys = pygame.key.get_pressed()
        if not self.active and not self.activated:
            if self.rect.colliderect(player.rect) and keys[pygame.K_e]:
                self.start(towers)
    
        # 버티는 중이면 타이머 감소 + 적 스폰
        if self.active:
            self.timer -= dt

            active_towers = sum(1 for tower in towers if tower.active or tower.activated)

            # 플레이어가 출입 불가 링을 벗어나지 못하도록 강제
            if self.player:
                dx = self.player.rect.centerx - self.rect.centerx
                dy = self.player.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > self.absorb_radius and dist != 0:
                    nx = self.rect.centerx + dx / dist * self.absorb_radius
                    ny = self.rect.centery + dy / dist * self.absorb_radius
                    self.player.rect.centerx = int(nx)
                    self.player.rect.centery = int(ny)
                    # 맵 범위 내로 보정
                    self.player.rect.centerx = max(0, min(MAP_WIDTH, self.player.rect.centerx))
                    self.player.rect.centery = max(0, min(MAP_HEIGHT, self.player.rect.centery))

            # Spawn enemies around the tower using the ring radius so enemies can move freely in/out
            self.spawn_timer = spawn_enemies(
                player, enemies, all_sprites,
                self.spawn_timer, current_time,
                base_interval=150,
                base_num=7,
                spawn_radius=1400,
                difficulty_scale=False,
                extra_multiplier=1 + (active_towers*0.7),
                spawn_center=None,
                game_start_time=self.game_start_time
            )
            if self.timer <= 0:
                self.activate(enemies, exp_orbs, all_sprites)

        # 파동이 활성화되어 있으면 반경을 늘리고 도달한 적들을 처리
        if self.wave_active:
            # dt는 초 단위
            self.wave_radius += self.wave_speed * dt

            # 새로 파동 범위에 들어온 적들을 처리
            for enemy in list(enemies):
                if enemy in self._affected_enemies:
                    continue
                dx = enemy.rect.centerx - self.rect.centerx
                dy = enemy.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist <= self.wave_radius:
                    # 파동에 맞은 적 처리: 경험치 오브 생성 + 제거
                    orb = ExpOrb(enemy.rect.centerx, enemy.rect.centery, random.randint(1, 7))
                    exp_orbs.add(orb)
                    all_sprites.add(orb)

                    # 임시 이펙트(팝)를 추가
                    self._pops.append((enemy.rect.center, pygame.time.get_ticks(), 30))

                    enemy.kill()
                    self._affected_enemies.add(enemy)

            # 파동이 최대 반경에 도달하면 종료 처리
            if self.wave_radius >= self.wave_max_radius:
                self.wave_active = False
                self.activated = True  # 완료되면 타워는 ON 상태

                # 파동이 끝난 뒤, 생성된 오브들은 흡수 대상이 되도록 설정
                for orb in exp_orbs:
                    dx = orb.rect.centerx - self.rect.centerx
                    dy = orb.rect.centery - self.rect.centery
                    dist = math.hypot(dx, dy)
                    if dist < self.absorb_radius:
                        orb.absorbing = True
                        orb.target = self.player
                        orb.absorb_speed = self.absorb_speed

        # 팝 이펙트 오래된 것 삭제
        now = pygame.time.get_ticks()
        self._pops = [p for p in self._pops if now - p[1] < 300] 

    def draw(self, screen, camera):
        """타워와 남은 시간 표시"""
        screen.blit(self.image, camera.apply(self.rect))

        # 시각적 링 그리기 (월드 좌표 -> 화면 좌표 변환)
        screen_x = int(self.rect.centerx - camera.offset_x)
        screen_y = int(self.rect.centery - camera.offset_y)
        if self.active and not self.activated:
            # 노란색 링: 플레이어 출입 불가
            pygame.draw.circle(screen, (255, 255, 0), (screen_x, screen_y), int(self.absorb_radius), 3)
            text = self.font.render(str(int(self.timer) + 1), True, (255, 255, 0))
            text_rect = text.get_rect(center=(self.rect.centerx - camera.offset_x,
                                              self.rect.top - 20 - camera.offset_y))
            screen.blit(text, text_rect)
        elif self.activated:
            # 녹색 링: 이미 발동됨
            pygame.draw.circle(screen, (0, 255, 0), (screen_x, screen_y), int(self.absorb_radius), 3)
            text = self.font.render("ONLINE", True, (0, 255, 0))
            text_rect = text.get_rect(center=(self.rect.centerx - camera.offset_x,
                                              self.rect.top - 20 - camera.offset_y))
            screen.blit(text, text_rect)

        # 파동 시각화: 활성화 도중에는 확장하는 원을 그립니다
        if self.wave_active:
            # 반경
            r = int(self.wave_radius)
            if r > 0:
                # 반투명 외곽선 + 내부 희미한 채움
                # 외곽선
                pygame.draw.circle(screen, (0, 200, 255), (screen_x, screen_y), r, 4)
                # 내부 희미한 채움 (원 안에 반투명 색을 칠함)
                try:
                    temp = pygame.Surface((r*2+6, r*2+6), pygame.SRCALPHA)
                    pygame.draw.circle(temp, (0, 200, 255, 30), (r+3, r+3), r)
                    screen.blit(temp, (screen_x - r - 3, screen_y - r - 3))
                except Exception:
                    # 큰 서피스 생성이 실패할 경우 외곽선만 그리기
                    pass

        # 파동에 맞은 적 팝 이펙트 그리기
        now = pygame.time.get_ticks()
        for pos, start_t, max_r in list(self._pops):
            age = now - start_t
            t_ratio = min(1.0, age / 300)
            pr = int(max_r * (0.5 + t_ratio))
            alpha = int(255 * (1 - t_ratio))
            tx = pos[0] - camera.offset_x
            ty = pos[1] - camera.offset_y
            try:
                tmp = pygame.Surface((pr*2+6, pr*2+6), pygame.SRCALPHA)
                pygame.draw.circle(tmp, (255, 220, 100, alpha), (pr+3, pr+3), pr)
                screen.blit(tmp, (tx - pr - 3, ty - pr - 3))
            except Exception:
                pygame.draw.circle(screen, (255, 220, 100), (int(tx), int(ty)), pr, 2)

def spawn_enemies(
        player, enemies, all_sprites,
        spawn_timer, current_time,
        base_interval=180,          # 기본 스폰 주기 (tick 단위)
        base_num=5,                # 기본 스폰 수
        margin=1200,                 # 플레이어 최소 거리 (기본값)
        spawn_radius=1400,          # 최대 거리 (기본값)
        enemy_size=32,              # 적 크기
        difficulty_scale=True,      # 시간 경과에 따른 난이도 증가 여부
        extra_multiplier=1.1,         # 웨이브일 때 배수 (기본은 1.1)
        spawn_center=None,          # (x,y) 중심을 지정하면 해당 좌표를 기준으로 스폰
        game_start_time=None,
        max_enemies=None            
    ):
        """적 스폰 함수. 기본 스폰 및 웨이브 이벤트 모두 지원.

        이제 선택적으로 spawn_center=(x,y)를 전달하면 해당 좌표를 기준으로 적을 소환합니다.
        기본 동작은 기존과 동일하게 플레이어 중심을 기준으로 소환합니다.
        """

        spawn_timer += 1
        if spawn_timer > base_interval:  
            # 난이도 스케일 (시간에 따라 강해짐)
            if game_start_time is None:
                elapsed_sec = current_time // 1000
            else:
                elapsed_sec = max(0, (current_time - game_start_time) // 1000)
            level_scale = (1 + elapsed_sec // 40) 
            # 이번에 스폰할 적 수
            num_to_spawn = round((base_num + level_scale) * extra_multiplier)

            # 스폰 기준점 결정 (spawn_center가 있으면 그걸 사용하고, 없으면 플레이어 중심 사용)
            if spawn_center is not None:
                center_x, center_y = spawn_center
            else:
                center_x, center_y = player.rect.centerx, player.rect.centery

            # 적 스폰
            for _ in range(num_to_spawn):
                # 만약 max_enemies에 도달하면 더 이상 생성하지 않음
                if max_enemies is not None and len(enemies) >= max_enemies:
                    break
                while True:
                    angle = random.uniform(0, 2*math.pi)
                    distance = random.randint(margin, spawn_radius)
                    spawn_x = int(center_x + math.cos(angle) * distance)
                    spawn_y = int(center_y + math.sin(angle) * distance)

                    # 맵 범위 제한
                    spawn_x = max(0, min(MAP_WIDTH - enemy_size, spawn_x))
                    spawn_y = max(0, min(MAP_HEIGHT - enemy_size, spawn_y))

                    # 새 적 생성
                    enemy_class = random.choices(
                        [Enemy, FastEnemy, TankEnemy],
                        weights=[0.85, 0.14, 0.01],  # 등장 확률 조정
                        k=1
                    )[0]

                    new_enemy = enemy_class(spawn_x, spawn_y)

                    # HP 스케일 적용 (기존 level_scale)
                    new_enemy.max_hp += int(level_scale)
                    new_enemy.hp = new_enemy.max_hp

                    if not pygame.sprite.spritecollideany(new_enemy, enemies):
                        enemies.add(new_enemy)
                        all_sprites.add(new_enemy)
                        break

            spawn_timer = 0

        return spawn_timer
