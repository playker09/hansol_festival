import pygame
import random
from classes.weapon import Weapon

def safe_font(size=16):
    pygame.font.init()
    # 한국어 표시 가능한 폰트 우선 탐색
    candidates = [
        "Malgun Gothic", "NanumGothic", "Noto Sans CJK KR", "Apple SD Gothic Neo",
        "맑은 고딕", "나눔고딕", "Noto Sans KR", None  # None -> 기본 시스템 폰트
    ]
    for name in candidates:
        try:
            return pygame.font.SysFont(name, size)
        except:
            continue
    return pygame.font.SysFont(None, size)

# ---------------- Upgrade 클래스 ----------------
class Upgrade:
    def __init__(self, name, desc, effect, extra_effects=None, max_level=5):
        self.name = name
        self.desc = desc
        self.effect = effect                # (player, level) -> 기본 효과
        self.extra_effects = extra_effects or {}  # {레벨: 함수(player)}
        self.level = 0                      # 현재 레벨
        self.max_level = max_level
        # UI with safe font
        self.font = safe_font(size=24)
        self.big_font = safe_font(size=48) 
        self.small_font = safe_font(size=16)          # 최대 레벨 (None이면 무제한)

    def apply(self, player):
        if self.max_level is not None and self.level >= self.max_level:
            print(f"[최대 레벨] {self.name} Lv.{self.level}")
            return  # 최대 레벨 도달하면 적용 안함
        
        self.level += 1
        # 기본 효과
        self.effect(player, self.level)
        # 추가 효과
        if self.level in self.extra_effects:
            self.extra_effects[self.level](player)
            print(f"[추가 효과 발동] {self.name} Lv.{self.level}")


# ---------------- 공용 업그레이드 ----------------
COMMON_UPGRADES = [
    Upgrade(
        "속사 모드", "무기 발사 속도가 빨라집니다.",
        effect=lambda p, lvl: setattr(p.current_weapon, "fire_rate", max(50, p.current_weapon.fire_rate - 10)),
        extra_effects={
            3: lambda p: setattr(p.current_weapon, "spread", max(1, p.current_weapon.spread - 1)),
        },
    ),
    Upgrade(
        "대용량 탄창", "탄약 수가 늘어납니다.",
        effect=lambda p, lvl: setattr(p.current_weapon, "mag_size", p.current_weapon.mag_size + 3)
    ),
    Upgrade(
        "철갑탄", "총알이 적을 관통합니다.",
        effect=lambda p, lvl: setattr(p.current_weapon, "pierce_level", lvl)
    ),
    Upgrade(
        "고위력탄", "총알의 기본 피해가 크게 증가합니다.",
        effect=lambda p, lvl: setattr(p.current_weapon, "damage", getattr(p.current_weapon, "damage", 1) + 1 * lvl),
        extra_effects={
            3: lambda p: setattr(p.current_weapon, "damage", getattr(p.current_weapon, "damage", 1) + 1),
            5: lambda p: setattr(p.current_weapon, "damage", getattr(p.current_weapon, "damage", 1) + 2),
        },
    ),
]


# ---------------- 무기별 전용 업그레이드 ----------------
WEAPON_SPECIFIC = {
    "DMR": [
        Upgrade(
            "DMR - 예리한 손놀림", "관통력이 증가합니다.",
            effect=lambda p, lvl: setattr(p.current_weapon, "pierce_level", getattr(p.current_weapon, "pierce_level", 1) + 1)
        )
    ],
    "SMG": [
        Upgrade(
            "SMG - 보정기", "반동이 줄어듭니다.",
            effect=lambda p, lvl: setattr(p.current_weapon, "spread", max(1, p.current_weapon.spread - 1))
        )
    ],
    "Rifle": [
        Upgrade(
            "돌격 소총 - 불법 개조", "데미지가 증가합니다.",
            effect=lambda p, lvl: setattr(p.current_weapon, "damage", getattr(p.current_weapon, "damage", 1) + 1)
        )
    ],
    "Shotgun": [
        Upgrade(
            "샷건 - 산탄 수 증가", "산탄 수가 늘어납니다.",
            effect=lambda p, lvl: setattr(p.current_weapon, "pellet_count", p.current_weapon.pellet_count + 2)
        )
    ],
}

# ---------------- 악세사리 ----------------
ACCESSORIES = [
    Upgrade(
        "응급치료 키트", "체력이 즉시 회복됩니다.",
        effect=lambda p, lvl: setattr(p, "hp", min(p.max_hp, p.hp + 40))
    ),
    Upgrade(
        "에너지 음료", "대쉬 쿨타임이 감소합니다.",
        effect=lambda p, lvl: setattr(p, "dash_cooldown_time", max(1000, p.dash_cooldown_time - 500))
    ),
    Upgrade(
        "베테랑", "추가 경험치 획득",
        effect=lambda p, lvl: setattr(p, "exp", p.exp + 5)
    ),
    Upgrade(
        "가벼운 발걸음", "이동 속도가 증가합니다.",
        effect=lambda p, lvl: setattr(p, "speed", p.speed + 0.2)
    ),
    Upgrade(
        "끈기", "최대 체력이 증가합니다.",
        effect=lambda p, lvl: setattr(p, "max_hp", p.max_hp + 20),
        extra_effects={
            3: lambda p: setattr(p, "hp_regen", getattr(p, "hp_regen", 0) + 1)
        }
    ),
]
# ---------------- 업그레이드 후보 생성 ----------------
def generate_upgrades(player):
    upgrades = []
    if player.primary_weapon and player.primary_weapon.name in WEAPON_SPECIFIC:
        upgrades.extend(WEAPON_SPECIFIC[player.primary_weapon.name])
    upgrades.extend(COMMON_UPGRADES)
    if len(player.upgrades["accessory"]) < player.max_accessory:
        upgrades.extend(ACCESSORIES)
    return random.sample(upgrades, min(3, len(upgrades)))

def draw_upgrade_ui(surface, player, choices):
    font = safe_font(size=24)
    small_font = safe_font(size=16)

    ui_width, ui_height = 500, 360
    overlay = pygame.Surface((ui_width, ui_height))
    overlay.fill((50, 50, 50))
    overlay.set_alpha(230)
    rect = overlay.get_rect(center=(surface.get_width()//2, surface.get_height()//2))
    surface.blit(overlay, rect.topleft)

    btn_rects = []
    mx, my = pygame.mouse.get_pos()

    for i, up in enumerate(choices):
        btn_rect = pygame.Rect(rect.x + 50, rect.y + 40 + i*100, ui_width-100, 80)
        btn_rects.append(btn_rect)

        # 마우스 오버 여부 확인
        if btn_rect.collidepoint(mx, my):
            bg_color = (150, 150, 50)  # 강조된 배경
            border_color = (255, 255, 0)
        else:
            bg_color = (100, 100, 100)
            border_color = (200, 200, 200)

        # 버튼 배경 & 테두리
        pygame.draw.rect(surface, bg_color, btn_rect, border_radius=10)
        pygame.draw.rect(surface, border_color, btn_rect, 2, border_radius=10)

        # 레벨 가져오기
        level = up.level

        # 이름 + 레벨
        text = font.render(f"{up.name} (Lv.{level})", True, (255, 255, 255))
        surface.blit(text, (btn_rect.x + 10, btn_rect.y + 10))

        # 설명
        desc = small_font.render(up.desc, True, (220, 220, 220))
        surface.blit(desc, (btn_rect.x + 10, btn_rect.y + 45))

    return btn_rects


def reset_upgrades():
    """게임 재시작 시 모든 업그레이드 레벨을 초기화합니다."""
    for up in COMMON_UPGRADES:
        up.level = 0
    for lst in WEAPON_SPECIFIC.values():
        for up in lst:
            up.level = 0
    for up in ACCESSORIES:
        up.level = 0