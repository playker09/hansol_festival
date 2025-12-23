import sys
import os
import pygame
import math
import random

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.player import Player
from classes.entity import spawn_enemies, EMP_Tower, ExpOrb
from classes.camera import Camera
from scenes.map import draw_grid, MAP_WIDTH, MAP_HEIGHT
from scenes.game_over import game_over_screen, game_success_screen
from hud import draw_level, draw_ammo, draw_dash_indicator, draw_crosshair, draw_reload_circle, draw_emp_indicator, draw_activated, draw_health_vignette
from classes.upgrade import generate_upgrades, draw_upgrade_ui, COMMON_UPGRADES, WEAPON_SPECIFIC, ACCESSORIES, reset_upgrades
from scenes.lobby import lobby_screen, tutorial_screen   

# 초기화
pygame.init()
WIDTH, HEIGHT = 1960, 1080
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AREA-X")

# FPS
clock = pygame.time.Clock()
FPS = 60

# --- Optimization / object limits ---
MAX_ENEMIES = 150
MAX_EXP_ORBS = 300
ENEMY_CULL_DISTANCE = 4000                  # 플레이어로부터 너무 멀리 있는 적은 삭제 (px)

pygame.mixer.init()
game_state = "lobby"  # play, upgrade, game_over, prepare, lobby
# 사운드 파일 경로를 절대 경로로 지정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_SFX_DIR = os.path.join(BASE_DIR, "assets", "sfx")
ingame_bgm = pygame.mixer.Sound(os.path.join(ASSET_SFX_DIR, "bgm1.wav"))
ingame_bgm.set_volume(0.3)
# 프로젝트 루트 기준

# 클릭 사운드 
click_sfx_path = os.path.join(ASSET_SFX_DIR, "click.mp3")

current_music_state = None  # 지금 어떤 상태에서 음악이 재생되고 있는지 기록

def safe_font(size=16, bold=False):
    pygame.font.init()
    # 한국어 표시 가능한 폰트 우선 탐색
    candidates = [
        "Malgun Gothic", "NanumGothic", "Noto Sans CJK KR", "Apple SD Gothic Neo",
        "맑은 고딕", "나눔고딕", "Noto Sans KR", None  # None -> 기본 시스템 폰트
    ]
    for name in candidates:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except:
            continue
    return pygame.font.SysFont(None, size, bold=bold)

def update_music(game_state):
    global current_music_state

    if game_state in ["play", "upgrade"]:
        if current_music_state != "ingame_bgm":
            # stop any music stream, and ensure previous ingame Sound is stopped
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            try:
                ingame_bgm.stop()
            except Exception:
                pass
            ingame_bgm.play(-1)  # 무한 반복
            current_music_state = "ingame_bgm"
    else:
        # only stop if currently playing ingame bgm
        if current_music_state == "ingame_bgm":
            try:
                ingame_bgm.stop()
            except Exception:
                pass
            current_music_state = None

def generate_tower_positions(num_towers, min_distance_between, min_center_distance):
    """
    - num_towers: 설치할 타워 개수
    - min_distance_between: 타워끼리 최소 거리
    - min_center_distance: 맵 중앙에서 최소 거리
    """
    positions = []
    center_x, center_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
    
    while len(positions) < num_towers:
        x = random.randint(100, MAP_WIDTH - 100)
        y = random.randint(100, MAP_HEIGHT - 100)

        # 타워끼리 최소 거리 확인
        too_close_to_others = any(math.hypot(x - px, y - py) < min_distance_between for px, py in positions)

        # 중앙에서 충분히 떨어졌는지 확인
        too_close_to_center = math.hypot(x - center_x, y - center_y) < min_center_distance

        if not too_close_to_others and not too_close_to_center:
            positions.append((x, y))
    
    return positions

def main():
    global game_state # play, upgrade, game_over, prepare, lobby
    
    game_state = "prepare"

    # 업그레이드 상태 초기화
    reset_upgrades()

    # 모든 스프라이트 그룹
    player = Player()
    lobby_screen(WIN, WIDTH, HEIGHT)
    # 튜토리얼 화면 표시 (Start 후)
    tutorial_screen(WIN, WIDTH, HEIGHT)
    player.choose_primary_weapon(WIN, WIDTH, HEIGHT)
    game_state = "play"
    play_start_time = pygame.time.get_ticks()
    
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    exp_orbs = pygame.sprite.Group()
    tower_positions = generate_tower_positions(
        num_towers=3,
        min_distance_between=1000,
        min_center_distance=800   # 중앙에서 최소 800px 떨어짐
    )
    towers = pygame.sprite.Group([EMP_Tower(x, y, player) for x, y in tower_positions])
    all_sprites.add(towers)
    all_sprites.add(player)

    spawn_timer = 1000         
    camera = Camera(WIDTH, HEIGHT)  # 카메라 초기화
    last_hit_time = 0  # 마지막으로 플레이어가 적에게 맞은 시간
    shooting = False
    upgrade_choices = []
    btn_rects = []
    upgrade_start_time = 0

    while True:
        update_music(game_state)
        dt = clock.tick(FPS) / 1000.0
        WIN.fill((0,0,0))
        current_time = pygame.time.get_ticks()

        # 이벤트 처리
        for event in pygame.event.get():
            # mark if this event was used by UI (so it won't also trigger firing)
            event_consumed = False

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game_state == "upgrade":
                current_time = pygame.time.get_ticks()
                
                # UI 그리기
                btn_rects = draw_upgrade_ui(WIN, player, upgrade_choices)
                
                # 클릭 가능 여부 (0.5초 딜레이)
                allow_click = current_time - upgrade_start_time >= 500
                
                if allow_click and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    for i, rect in enumerate(btn_rects):
                        if rect.collidepoint((mx, my)):
                            chosen_upgrade = upgrade_choices[i]
                            chosen_upgrade.apply(player)
                            
                            # 카테고리 등록
                            category = "weapon" if chosen_upgrade in COMMON_UPGRADES + WEAPON_SPECIFIC.get(player.primary_weapon.name, []) else "accessory"
                            if chosen_upgrade not in player.upgrades[category]:
                                player.upgrades[category].append(chosen_upgrade)
                            
                            pygame.mixer.Sound(click_sfx_path).play()
                            player.upgrading = False
                            game_state = "play"
                            # consume the click so it doesn't also fire the weapon
                            event_consumed = True
                            
            # 장전
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    player.reload(current_time)
            # 발사 (오직 플레이 상태에서만 처리)
            if event.type == pygame.MOUSEBUTTONDOWN and game_state == "play" and not event_consumed:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    mode = player.current_weapon.mode
                    if mode == "single" or mode == "burst" or mode == "shotgun":
                        player.shoot(mx, my, camera, bullets, current_time)
                    elif mode == "auto":
                        shooting = True

            if event.type == pygame.MOUSEBUTTONUP and game_state == "play":
                if event.button == 1:
                    shooting = False
        
        if game_state == "play":
            if shooting:
                mx, my = pygame.mouse.get_pos()
                player.shoot(mx, my, camera, bullets, current_time)
            bullets.update()
            
            player.update_weapon(current_time)
                
            # 플레이어 이동
            keys = pygame.key.get_pressed()
            dash_dir = [0, 0]

            # 이동 방향 벡터 생성
            if keys[pygame.K_w]: dash_dir[1] -= 1
            if keys[pygame.K_s]: dash_dir[1] += 1
            if keys[pygame.K_a]: dash_dir[0] -= 1
            if keys[pygame.K_d]: dash_dir[0] += 1

            # 대쉬 시작 (방향이 있을 때만)
            if dash_dir != [0, 0] and keys[pygame.K_LSHIFT]:
                player.dash(tuple(dash_dir), current_time)

            # 이동 처리
            player.move(keys)
            # 플레이어 상태 업데이트 (대쉬, 무적, 무기)
            player.update(current_time)
            # 카메라 업데이트
            camera.update(player)

            # EMP 타워 업데이트
            for tower in towers:
                tower.update(dt, player, enemies, all_sprites, exp_orbs, current_time, towers)

            activated_towers = sum(1 for t in towers if t.activated)
            if activated_towers >= 3:
                survival_seconds = (current_time - play_start_time) / 1000.0
                action = game_success_screen(WIN, survival_seconds, activated_towers, WIDTH, HEIGHT)
                if action == "retry":
                    main()
                else:
                    pygame.quit()
                    sys.exit()
                
            spawn_timer = spawn_enemies(player, enemies, all_sprites, spawn_timer, current_time, max_enemies=MAX_ENEMIES)

            # 멀리 있는 오브젝트 정리: 일정 거리 이상, 오래된 적 제거
            for enemy in list(enemies):
                dx = enemy.rect.centerx - player.rect.centerx
                dy = enemy.rect.centery - player.rect.centery
                dist = math.hypot(dx, dy)
                if dist > ENEMY_CULL_DISTANCE:
                    enemy.kill()
            
            # 총알 이동 및 제거
            for bullet in bullets.copy():
                hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
                for enemy in hit_enemies:
                    enemy.hp -= bullet.damage
                    # 피격 표시 시간 설정
                    try:
                        enemy.last_hurt_time = current_time
                    except Exception:
                        pass

                    # 넉백 계산
                    dx = enemy.rect.centerx - bullet.rect.centerx
                    dy = enemy.rect.centery - bullet.rect.centery
                    dist = math.hypot(dx, dy)
                    if dist != 0:
                        dx /= dist
                        dy /= dist
                        knockback_strength = 2 # 넉백 세기, 필요하면 총알 속성으로 변경 가능
                        enemy.knockback_x += dx * knockback_strength
                        enemy.knockback_y += dy * knockback_strength

                    bullet.pierce_count += 1
                    
                    if enemy.hp <= 0:
                        exp_orb = ExpOrb(enemy.rect.centerx, enemy.rect.centery, random.randint(4, 7))
                        exp_orbs.add(exp_orb)
                        all_sprites.add(exp_orb)
                        enemy.kill()
                    if bullet.pierce_count > bullet.max_pierce:
                        bullet.kill()
                        break  # 이미 최대 관통
            
            hit_enemies = pygame.sprite.spritecollide(player, enemies, False)
            current_time = pygame.time.get_ticks()
            for enemy in hit_enemies:
                if enemy.can_attack(current_time):
                    enemy.deal_damage(player, current_time)

                    if player.hp <= 0:
                        game_state = "game_over"
                        survival_seconds = (current_time - play_start_time) / 1000.0
                        activated_towers = sum(1 for t in towers if t.activated)
                        action = game_over_screen(WIN, player.level, survival_seconds, activated_towers, WIDTH, HEIGHT)
                        if action == "retry":
                            main()
                        else:
                            pygame.quit()
                            sys.exit()
            # 적 이동
            for enemy in enemies:
                enemy.move(player.rect, enemies)
            pass

        # 경험치 오브: 가까이 있으면 자동으로 끌려오고, 흡수가 진행됩니다.
        ATTRACT_RADIUS = 220  # 픽셀
        for orb in exp_orbs.copy():
            # 거리 계산 (플레이어 중심과 오브 중심)
            dx = player.rect.centerx - orb.rect.centerx
            dy = player.rect.centery - orb.rect.centery
            dist = math.hypot(dx, dy)
            # 가까워지면 흡수 시작 (타워에 의해 이미 흡수 중이면 건너뜀)
            if not orb.absorbing and dist < ATTRACT_RADIUS:
                orb.absorbing = True
                orb.target = player
                # 흡수 속도는 거리에 따라 다르게 (가까울수록 빠름)
                orb.absorb_speed = min(18, 4 + (ATTRACT_RADIUS - dist) / 30 * 8)
            # 지속적으로 흡수 속도 약간 증가시켜 당김 느낌 강화
            if orb.absorbing and orb.target == player:
                orb.absorb_speed = min(20, orb.absorb_speed + 0.2)
            # 플레이어 정보를 전달하여 거리/시간 기반 자동 삭제가 가능하도록 함
            orb.update(player)

        # 경험치 오브 개수 제한: 가장 먼 것부터 삭제
        if len(exp_orbs) > MAX_EXP_ORBS:
            orbs_sorted = sorted(exp_orbs, key=lambda o: math.hypot(o.rect.centerx - player.rect.centerx, o.rect.centery - player.rect.centery), reverse=True)
            remove_count = len(exp_orbs) - MAX_EXP_ORBS
            for o in orbs_sorted[:remove_count]:
                o.kill()

        # 레벨업 큐 확인
        if player.level_up_queue > 0 and game_state != "upgrade":
            player.level_up_queue -= 1
            game_state = "upgrade"
            player.upgrading = True

            s = pygame.mixer.Sound(os.path.join(ASSET_SFX_DIR, "level_up.mp3"))
            s.set_volume(0.3)
            s.play()

            upgrade_choices = generate_upgrades(player)  # 업그레이드 후보 생성
            upgrade_start_time = pygame.time.get_ticks()

        draw_grid(WIN, camera)

        for sprite in all_sprites:
            if hasattr(sprite, "draw"):  # EMP_Tower, Player 등은 draw 있음
                sprite.draw(WIN, camera)
            else:  # 일반 Enemy 같은 경우는 그냥 이미지 블릿
                WIN.blit(sprite.image, camera.apply(sprite))

        # 그리기
        for bullet in bullets:
            bullet.draw(WIN, camera)  # 회전된 총알 그리기

        # 플레이어 HP 바 및 HUD
        player.draw_hp_bar(WIN, camera)
        font = safe_font(size=48,bold=True)
        large_font = safe_font(size=50,bold=True)
        small_font = safe_font(size=36,bold=True)
        draw_level(WIN, font, player)
        draw_ammo(WIN, large_font, player)
        draw_dash_indicator(WIN, small_font, player)
        mx, my = pygame.mouse.get_pos()
        draw_crosshair(WIN, mx, my)
        draw_reload_circle(WIN, (mx, my), 20, player.current_weapon)
        draw_emp_indicator(WIN, player, towers, camera)
        draw_activated(WIN, font, towers)

        if game_state == "upgrade":
            btn_rects = draw_upgrade_ui(WIN, player, upgrade_choices)

        # 체력에 따른 화면 가장자리 붉어짐 효과
        draw_health_vignette(WIN, player)

        pygame.display.update()

click_sound = pygame.mixer.Sound(os.path.join(ASSET_SFX_DIR, "click.mp3"))
exp_sound = pygame.mixer.Sound(os.path.join(ASSET_SFX_DIR, "exp1.mp3"))
levelup_sound = pygame.mixer.Sound(os.path.join(ASSET_SFX_DIR, "level_up.mp3"))
if __name__ == "__main__":
    main()
