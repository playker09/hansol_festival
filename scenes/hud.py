import pygame
import math

def draw_level(surface, font, player):
    """플레이어 레벨과 경험치 표시"""
    level_text = font.render(f"LvL: {player.level} EXP: {player.exp}/{player.exp_to_next_level}", True, (255, 255, 255))
    surface.blit(level_text, (40, 12))

def draw_ammo(surface, font, player):
    """현재 무기 탄약 표시"""
    weapon = player.current_weapon
    text = font.render(f" {weapon.ammo_in_mag}", True, (255, 255, 255))
    surface.blit(text, (40, 900)) 

def draw_activated(surface, font, towers):
    """현재 활성화된 타워 개수 표시"""
    activated_count = sum(1 for t in towers if t.activated)
    text = font.render(f"타워: {activated_count} / 3", True, (255, 255, 255))
    surface.blit(text, (1600, 15))

def draw_dash_indicator(surface, font, player):
    """대쉬 가능 표시"""
    if player.dash_cooldown <= 0:
        text = font.render("DASH READY", True, (0, 255, 0))
        surface.blit(text, (60, 970))
    else: 
        text = font.render(f"{player.dash_cooldown/1000+1:.1f}", True, (2, 255, 0))
        surface.blit(text, (60, 970))
# --- 마우스 조준선 ---
def draw_crosshair(surface, mx, my, size=10, color=(255,255,255), width=2):
    pygame.draw.line(surface, color, (mx - size, my), (mx + size, my), width)
    pygame.draw.line(surface, color, (mx, my - size), (mx, my + size), width)

# --- 재장전 원 표시 ---
def draw_reload_circle(surface, pos, radius, weapon):
    if not weapon.is_reloading:
        return
    
    # 진행률 계산
    current_time = pygame.time.get_ticks()
    elapsed = current_time - weapon.reload_start_time
    progress = min(elapsed / weapon.reload_time, 1)  # 0~1
    
    start_angle = math.pi/2  # 위쪽에서 시작
    end_angle = start_angle - progress * 2 * math.pi  # 반시계 방향
    
    # 항상 같은 두께로 그림
    pygame.draw.arc(surface, (255, 255, 0), 
                    (pos[0]-radius, pos[1]-radius, radius*2, radius*2),
                    end_angle, start_angle, 3)  # <- width=3 고정
    
def draw_emp_indicator(surface, player, towers, camera):
    """
    플레이어 기준 가장 가까운 **활성화되지 않은 타워**만 표시 (플레이어 중심에 표시)
    """
    # 활성화되지 않은 타워만 선택
    inactive_towers = [t for t in towers if not t.activated]
    if not inactive_towers:
        return

    # 가장 가까운 타워 선택 (월드 좌표 기반)
    nearest_tower = min(
        inactive_towers,
        key=lambda t: math.hypot(t.rect.centerx - player.rect.centerx,
                                 t.rect.centery - player.rect.centery)
    )

    dx = nearest_tower.rect.centerx - player.rect.centerx
    dy = nearest_tower.rect.centery - player.rect.centery
    distance = math.hypot(dx, dy)

    if distance < 300:  # 너무 가까우면 표시 안 함
        return

    # 방향 계산
    angle = math.atan2(dy, dx)
    # 플레이어의 화면상의 위치를 기준으로 화살표를 그림
    cx = player.rect.centerx - camera.offset_x
    cy = player.rect.centery - camera.offset_y
    offset = 100
    indicator_size = 20
    arrow_x = cx + math.cos(angle) * offset
    arrow_y = cy + math.sin(angle) * offset

    points = [
        (arrow_x + math.cos(angle) * indicator_size, arrow_y + math.sin(angle) * indicator_size),
        (arrow_x + math.cos(angle + 2.5) * indicator_size, arrow_y + math.sin(angle + 2.5) * indicator_size),
        (arrow_x + math.cos(angle - 2.5) * indicator_size, arrow_y + math.sin(angle - 2.5) * indicator_size),
    ]
    
    pygame.draw.polygon(surface, (255, 255, 0), points)


def draw_health_vignette(surface, player, max_thickness=140):
    """플레이어 체력 비율에 따라 화면 가장자리에 붉은 비네팅을 그립니다.

    - 효과 시작: 체력 30% 이하부터 서서히 적용
    - 완전히 붉어지지 않도록 최대 불투명도를 제한
    """
    hp_ratio = max(0.0, min(1.0, player.hp / player.max_hp))
    start_threshold = 0.30  # 30%부터 효과 시작
    # 시작값보다 높으면 효과 없음
    if hp_ratio > start_threshold:
        return

    # 정규화: start_threshold -> 0.0    0.0 -> 1.0
    norm = (start_threshold - hp_ratio) / start_threshold
    norm = max(0.0, min(1.0, norm))

    # 최대 강도 제한 (255가 아닌 값으로 완전 붉어짐 방지)
    MAX_ALPHA = 100
    alpha = int(MAX_ALPHA * norm)  # 0..MAX_ALPHA

    steps = 6
    w, h = surface.get_width(), surface.get_height()

    for i in range(steps):
        t = int(max_thickness * (i + 1) / steps)
        # 바깥쪽일수록 불투명도 낮게 하기 위해 계단식 곡선 적용
        a = int(alpha * ((i + 1) / steps) ** 1.2)
        if a <= 0:
            continue
        # 위쪽
        s_top = pygame.Surface((w, t), pygame.SRCALPHA)
        s_top.fill((255, 0, 0, a))
        surface.blit(s_top, (0, 0))
        # 아래쪽
        surface.blit(s_top, (0, h - t))
        # 왼쪽
        s_left = pygame.Surface((t, h), pygame.SRCALPHA)
        s_left.fill((255, 0, 0, a))
        surface.blit(s_left, (0, 0))
        # 오른쪽
        surface.blit(s_left, (w - t, 0))
