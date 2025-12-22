import pygame
import os
import math
from scenes.map import MAP_WIDTH, MAP_HEIGHT
from classes.weapon import Weapon
from assets.sprite_sheet import load_sprite_sheet, get_frame, extract_grid
from assets import image_gun_x as gun_images
# from scenes.upgrade import show_upgrade_screen

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_IMAGE_DIR = os.path.join(BASE_DIR, "assets", "image")
ASSET_SFX_DIR = os.path.join(BASE_DIR, "assets", "sfx")

player_img = pygame.image.load(os.path.join(ASSET_IMAGE_DIR, "player.png"))

# 사운드 로드 예시
smg_shoot_sound = pygame.mixer.Sound(os.path.join(ASSET_SFX_DIR, "smg_shoot.wav"))

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load(os.path.join(ASSET_IMAGE_DIR, "player.png")).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (34, 66))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(MAP_WIDTH/2, MAP_HEIGHT/2))

        # 이동
        self.speed = 3.2

        # 체력
        self.max_hp = 100
        self.hp = 100

        # 레벨
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 10

        # 주무기 & 무기 선택
        self.weapons = {
            "dmr": Weapon("DMR", fire_rate=130, spread=1, mode="single", mag_size=25, reload_time=900, damage=5, pierce_level=3),
            "smg": Weapon("SMG", fire_rate=90, spread=5, mode="auto", reload_time=1200,damage=2, pierce_level=1),
            "rifle": Weapon("Rifle", fire_rate=120, spread=3, mode="auto", reload_time= 1600, damage=3, pierce_level=2),
            "shotgun": Weapon("Shotgun", fire_rate=700, spread=15, mode="shotgun", pellet_count=7,damage=2)
        }
        self.primary_weapon = None
        self.current_weapon = None
        self.current_weapon_key = None  # for texture lookup (e.g. 'dmr','smg')

        # 업그레이드 관리
        self.upgrades = {
            "weapon": [],      # Upgrade 객체 리스트
            "accessory": []
        }
        self.max_weapon_upgrades = 3
        self.max_accessory = 4

        # 대쉬 관련
        self.is_dashing = False
        self.dash_vector = (0, 0)
        self.dash_speed = 25
        self.dash_duration = 70
        self.dash_start_time = 0
        self.dash_cooldown_time = 3000
        self.dash_cooldown = 0
        self.is_invincible = False

        # 방향(좌/우) -> 기본 오른쪽
        self.facing_right = True

        # 대쉬 잔상(trail) 관련
        self.trails = []  # 각 항목: { 'image': Surface, 'pos': (cx, cy), 'time': created_time }
        self.trail_duration = 300  # ms
        self.trail_interval = 30   # ms 간격으로 잔상 생성
        self._last_trail_time = 0

        # 애니메이션 (스프라이트 시트 기반)
        self.anim_frames = []
        try:
            sheet = load_sprite_sheet(os.path.join(ASSET_IMAGE_DIR, "player_motion.png"))
            # 사용자 제공: frame size is 23x44, 5 frames (1 idle + 4 walk)
            frames_count = 5
            frame_w, frame_h = 23, 44
            frames = []
            for i in range(frames_count):
                rect = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
                # 안전하게 부분 복사 (영역이 시트 밖이면 투명으로 채워짐)
                frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), rect)
                frames.append(frame)
            # 스케일해서 사용
            self.anim_frames = [pygame.transform.scale(f, (34, 66)) for f in frames]
        except Exception:
            # 로드 실패 시 기존 이미지 사용
            self.anim_frames = [self.original_image.copy()]

        self.anim_index = 0
        self.anim_interval = 100  # ms per frame when walking
        self.last_anim_time = 0
        self.moving = False

        # 레벨업 큐 시스템
        self.level_up_queue = 0
        self.upgrading = False

        # 피격(붉게 깜박임) 관련
        self.last_hit_time = 0
        self.hit_flash_duration = 250  # ms

    def update_image(self):
        # 애니메이션 프레임 또는 기본 이미지로 현재 이미지를 설정
        if self.anim_frames:
            # anim_index에 따른 프레임 선택 (좌우 반전 지원)
            frame = self.anim_frames[self.anim_index % len(self.anim_frames)]
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            self.image = frame.copy()
        else:
            if self.facing_right:
                self.image = self.original_image.copy()
            else:
                self.image = pygame.transform.flip(self.original_image, True, False)

    def choose_primary_weapon(self, surface, WIDTH, HEIGHT):
        font_title = pygame.font.SysFont("malgungothic", 36, bold=True)
        font_stats = pygame.font.SysFont("malgungothic", 20)
        font_weapon = pygame.font.SysFont("malgungothic", 28, bold=True)

        weapons_list = list(self.weapons.values())
        weapon_names = ["DMR", "SMG", "Rifle", "Shotgun"]  # 무기 이름 리스트
        selected = None

        slot_width = 150
        slot_height = 250
        margin = 20

        while selected is None:
            surface.fill((0,0,0))

            # 제목
            title_surf = font_title.render("Select your weapon", True, (255, 255, 255))
            surface.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 50))

            start_x = (WIDTH - (slot_width + margin) * len(weapons_list) + margin) // 2
            y = HEIGHT//2 - slot_height//2

            slots = []
            mx, my = pygame.mouse.get_pos()
            for i, w in enumerate(weapons_list):
                x = start_x + i * (slot_width + margin)
                rect = pygame.Rect(x, y, slot_width, slot_height)
                slots.append((rect, w))

                # 마우스 오버 강조
                if rect.collidepoint((mx,my)):
                    pygame.draw.rect(surface, (70,70,70), rect, border_radius=10)  # 배경 밝게
                    border_color = (255, 255, 0)
                else:
                    pygame.draw.rect(surface, (50,50,50), rect, border_radius=10)
                    border_color = (200,200,200)

                pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)

                # 무기 이름 표시
                weapon_name = weapon_names[i] if i < len(weapon_names) else "Weapon"
                text_surf = font_weapon.render(weapon_name, True, (255, 255, 255))
                surface.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.y + 20))

                # 스탯
                stats_y = rect.y + 90
                stats = [
                    f"데미지: {w.damage}",
                    f"관통력: {w.pierce_level}",
                    f"재장전: {w.reload_time/1000:.1f}s",
                    f"탄퍼짐: {w.spread}"
                ]
                for s in stats:
                    stat_surf = font_stats.render(s, True, (255,255,255))
                    surface.blit(stat_surf, (rect.x + 10, stats_y))
                    stats_y += 25

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for rect, w in slots:
                        if rect.collidepoint((mx,my)):
                            selected = w
                            break

        self.primary_weapon = selected
        self.current_weapon = selected
        # determine and save the weapon key so we can lookup textures like texture_gun_<key>
        for k, v in self.weapons.items():
            if v is selected:
                self.current_weapon_key = k
                break




    def move(self, keys):
        # 입력에 따른 좌우 방향 결정 (이미지 반전)
        if keys[pygame.K_a]:
            if self.facing_right:
                self.facing_right = False
                self.update_image()
        elif keys[pygame.K_d]:
            if not self.facing_right:
                self.facing_right = True
                self.update_image()

        # 대쉬 중에는 이동 입력 무시 (단, 방향은 위에서 반영됨)
        if self.is_dashing:
            self.moving = False
            return
        moved = False
        if keys[pygame.K_w] and self.rect.top > 0:
            self.rect.y -= self.speed
            moved = True
        if keys[pygame.K_s] and self.rect.bottom < MAP_HEIGHT:
            self.rect.y += self.speed
            moved = True
        if keys[pygame.K_a] and self.rect.left > 0:
            self.rect.x -= self.speed
            moved = True
        if keys[pygame.K_d] and self.rect.right < MAP_WIDTH:
            self.rect.x += self.speed
            moved = True

        # 이동 여부 플래그
        self.moving = moved

    def dash(self, direction_vector, current_time):
        if not self.is_dashing and self.dash_cooldown <= 0:
            self.is_dashing = True
            self.dash_start_time = current_time
            self.dash_vector = direction_vector
            self.is_invincible = True

            # 대시 방향에 맞춰 좌우 반전 적용
            dx = direction_vector[0]
            if dx < 0:
                if self.facing_right:
                    self.facing_right = False
                    self.update_image()
            elif dx > 0:
                if not self.facing_right:
                    self.facing_right = True
                    self.update_image()

            # 초기 잔상 생성
            self._last_trail_time = current_time
            self.trails.append({
                'image': self.image.copy(),
                'pos': self.rect.center,
                'time': current_time
            })

            dash_sfx = pygame.mixer.Sound(os.path.join(ASSET_SFX_DIR, "dash.mp3"))
            dash_sfx.set_volume(0.7)
            dash_sfx.play()

    def update(self, current_time):
        if self.is_dashing:
            elapsed = current_time - self.dash_start_time
            if elapsed < self.dash_duration:
                self.rect.x += self.dash_vector[0] * self.dash_speed
                self.rect.y += self.dash_vector[1] * self.dash_speed

                # 대시 중이면 정해진 간격으로 잔상 생성
                if current_time - self._last_trail_time >= self.trail_interval:
                    self._last_trail_time = current_time
                    self.trails.append({
                        'image': self.image.copy(),
                        'pos': self.rect.center,
                        'time': current_time
                    })
            else:
                self.is_dashing = False
                self.is_invincible = False
                self.dash_cooldown = self.dash_cooldown_time

        # 오래된 잔상 제거
        self.trails = [t for t in self.trails if current_time - t['time'] < self.trail_duration]

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 16

        self.update_weapon(current_time)

        # 애니메이션 업데이트 (현재 시간 기준)
        if self.moving:
            if current_time - self.last_anim_time >= self.anim_interval:
                self.last_anim_time = current_time
                if len(self.anim_frames) > 1:
                    # 프레임 0은 idle로 유지, 걷기 애니메이션은 1..n-1
                    if self.anim_index == 0:
                        self.anim_index = 1
                    else:
                        self.anim_index += 1
                        if self.anim_index >= len(self.anim_frames):
                            self.anim_index = 1
                else:
                    self.anim_index = 0
        else:
            # 멈추면 idle (0번)으로 되돌림
            self.anim_index = 0

        # 이미지 갱신
        self.update_image()

    def shoot(self, mx, my, camera, bullets, current_time):
        px, py = self.rect.center
        self.current_weapon.shoot(px, py, mx, my, camera, bullets, current_time)

    def switch_weapon(self, name):
        if name in self.weapons:
            self.current_weapon = self.weapons[name]
            self.current_weapon_key = name

    def reload(self, current_time):
        self.current_weapon.reload(current_time)

    def update_weapon(self, current_time):
        self.current_weapon.update(current_time)

    def gain_exp(self, amount):
        self.exp += amount
        leveled_up = False
        while self.exp >= self.exp_to_next_level:
            self.exp -= self.exp_to_next_level
            self.level += 1
            self.exp_to_next_level += 5 * self.level
            self.level_up_queue += 1   # 큐에 쌓기
            leveled_up = True
        return leveled_up

    def draw(self, surface, camera):
        now = pygame.time.get_ticks()
        # 잔상 그리기 (나중에 사라지도록 점점 투명해짐)
        for t in self.trails:
            age = now - t['time']
            alpha = max(0, 255 * (1 - age / self.trail_duration))
            surf = t['image'].copy()
            # 표면에 알파 설정
            surf.set_alpha(int(alpha))
            rect = surf.get_rect(center=(t['pos'][0], t['pos'][1]))
            surface.blit(surf, camera.apply(rect))

        # 플레이어 본체 그리기
        surface.blit(self.image, camera.apply(self.rect))

        # 현재 무기에 따라 총 그리기 (플레이어 중심에서 마우스 방향 바라보기, 왼쪽 각도면 반전)
        if getattr(self, 'current_weapon_key', None):
            gun_attr = f"texture_gun_{self.current_weapon_key}"
            gun_surf = getattr(gun_images, gun_attr, None)
            if gun_surf:
                gun = gun_surf.copy()
                gun = pygame.transform.scale(gun, (gun.get_width()*1.7, gun.get_height()*1.7))
                # 플레이어 중심을 화면 좌표로 변환
                px_screen = self.rect.centerx - camera.offset_x
                py_screen = self.rect.centery - camera.offset_y
                mx, my = pygame.mouse.get_pos()
                dx = mx - px_screen
                dy = my - py_screen
                # 각도 계산 (0도는 오른쪽, 시계방향은 음수로 회전하기 위해 -angle 사용)
                angle = math.degrees(math.atan2(dy, dx)) if not (dx == 0 and dy == 0) else 0
                # 왼쪽을 바라볼 때는 원본을 좌우 반전
                if dx < 0:
                    gun = pygame.transform.flip(gun, False, True)
                # 회전하고 플레이어 중앙에 배치
                rotated = pygame.transform.rotate(gun, -angle)
                rrect = rotated.get_rect(center=(px_screen, py_screen))
                surface.blit(rotated, rrect)

        # 피격 시 붉게 깜박임(점점 사라짐) - 투명 픽셀은 보호
        elapsed = now - getattr(self, 'last_hit_time', 0)
        if elapsed < self.hit_flash_duration:
            ratio = 1.0 - (elapsed / self.hit_flash_duration)
            alpha = int(160 * ratio)  # 최대 알파 160
            # 원본 프레임의 알파를 유지하면서 빨간 톤 적용
            red_surf = self.image.copy()
            red_surf.fill((255, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            rect = self.image.get_rect(center=self.rect.center)
            surface.blit(red_surf, camera.apply(rect))

        # 플레이어 HP 바는 별도의 함수로 처리됨


    def draw_hp_bar(self, surface, camera):
        bar_width = 50
        bar_height = 8
        bar_x = self.rect.centerx - bar_width // 2 - camera.offset_x
        bar_y = self.rect.top - 15 - camera.offset_y
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, (255,0,0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (0,255,0),(bar_x, bar_y, bar_width * hp_ratio, bar_height))
