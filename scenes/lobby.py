import pygame
import sys
import math

def lobby_screen(surface, WIDTH, HEIGHT):
    # 버튼 위치와 크기
    button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 60)
    title_font = pygame.font.SysFont("arial", 80, bold=True)
    button_font = pygame.font.SysFont("arial", 40)

    while True:
        surface.fill((0,0,0))  # 배경 색

        # 제목
        title_surface = title_font.render("AREA-X", True, (255, 255, 255))
        surface.blit(title_surface, (WIDTH//2 - title_surface.get_width()//2, HEIGHT//4))

        # 버튼 그리기
        pygame.draw.rect(surface, (200, 200, 200), button_rect, border_radius=10)
        text_surface = button_font.render("Start", True, (0, 0, 0))
        surface.blit(text_surface, (button_rect.x + (button_rect.width - text_surface.get_width())//2,
                                button_rect.y + (button_rect.height - text_surface.get_height())//2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(event.pos):
                    return  # 다음 장면으로 이동

def tutorial_screen(surface, WIDTH, HEIGHT):
    """튜토리얼: 여러 페이지로 게임 목표와 타워 활성화/웨이브 메커닉을 설명하고 간단한 데모를 제공합니다."""
    font_title = pygame.font.SysFont("malgungothic", 48, bold=True)
    font = pygame.font.SysFont("malgungothic", 28)
    small = pygame.font.SysFont("malgungothic", 20)

    ui_w, ui_h = 920, 540
    ui_rect = pygame.Rect((WIDTH-ui_w)//2, (HEIGHT-ui_h)//2, ui_w, ui_h)

    # 내비게이션 버튼
    back_rect = pygame.Rect(ui_rect.x + 40, ui_rect.bottom - 80, 120, 50)
    next_rect = pygame.Rect(ui_rect.right - 160, ui_rect.bottom - 80, 120, 50)
    confirm_rect = pygame.Rect(ui_rect.centerx - 80, ui_rect.bottom - 80, 160, 50)
    close_rect = pygame.Rect(ui_rect.right - 80, ui_rect.y + 10, 60, 36)

    # 튜토리얼 페이지 정의
    pages = [
        {
            "title": "목표",
            "lines": [
                "맵에 무작위로 배치된 타워 3개를 모두 활성화하세요.",
                "타워를 활성화하면 제한시간이 시작되고, 그 동안 적 웨이브가 발생합니다.",
                "제한시간을 버텨내면, 해당 범위 내의 적들이 소멸합니다."
            ],
            "show_demo": False
        },
        {
            "title": "타워 활성화",
            "lines": [
                "타워 가까이에서 'E' 키를 눌러 활성화하십시오.",
                "활성화 시 타워는 노란색 원으로 범위를 표시하며, 플레이어는 해당 범위를 벗어날 수 없습니다."
            ],
            "show_demo": False
        },
        {
            "title": "카운트다운과 웨이브",
            "lines": [
                "타워 활성화 후 제한시간(30초~)이 흐르며 적 웨이브가 시작됩니다.",
                "제한시간 동안 생존하면 웨이브 종료 시점에 범위 내 적이 소멸합니다."
            ],
            "show_demo": True
        },
        {
            "title": "생존 보상",
            "lines": [
                "성공적으로 타워의 제한시간을 버티면 보상이 주어집니다 (경험치, 자원 등).",
                "실패하면 타워는 활성 상태가 해제되거나 다른 패널티가 있을 수 있습니다(게임 모드에 따라)."
            ],
            "show_demo": False
        },
        {
            "title": "전술 팁",
            "lines": [
                "적의 웨이브에서는 위치 선정과 무기 선택이 중요합니다.",
                "대쉬로 위기에서 벗어나고, 업그레이드를 잘 활용하세요.",
                "타워 범위 표시를 잘 확인해 안전 거리를 유지하세요."
            ],
            "show_demo": False
        }
    ]

    page_index = 0

    def wrap_text(text, font, max_width):
        words = text.split(' ')
        lines = []
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip() if cur else w
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # 튜토리얼 페이지 정의 (조작법 페이지 추가, 데모 제거)
    pages = [
        {
            "title": "목표",
            "lines": [
                "맵에 무작위로 배치된 타워 3개를 모두 활성화하세요.",
                "타워를 활성화하면 제한시간이 시작되고, 그 동안 적 웨이브가 발생합니다.",
                "제한시간을 버텨내면, 해당 범위 내의 적들이 소멸합니다."
            ]
        },
        {
            "title": "조작법",
            "lines": [
                "이동: W / A / S / D",
                "발사: 왼쪽 마우스 버튼 (좌클릭)",
                "대쉬: Shift",
                "장전: R",
                "상호작용(타워 활성화): E"
            ]
        },
        {
            "title": "타워 활성화",
            "lines": [
                "플레이어 주변 노란 화살표를 따라가 타워 가까이에서 'E' 키를 눌러 활성화하십시오.",
                "활성화 시 타워는 노란색 원으로 범위를 표시하며 , 플레이어는 해당 범위를 벗어날 수 없습니다."
            ]
        },
        {
            "title": "카운트다운과 웨이브",
            "lines": [
                "타워 활성화 후 제한시간이 흐르며 적 웨이브가 시작됩니다.",
                "제한시간 동안 생존하면 웨이브 종료 시점에 범위 내 적이 소멸합니다."
            ]
        },
        {
            "title": "업그레이드",
            "lines": [
                "적을 처치하면 경험치를 획득 할 수 있습니다.",
                "일정 경험치를 모으면 플레이어 레벨이 올라가고, 업그레이드를 할 수 있습니다.(한 업그레이드 당 5레벨)",
            ]
        },
        {
            "title": "전술 팁",
            "lines": [
                "적의 웨이브에서는 위치 선정과 무기 선택이 중요합니다.",
                "대쉬로 위기에서 벗어나고, 업그레이드를 잘 활용하세요.",
                "타워 범위 표시를 잘 확인해 안전 거리를 유지하세요."
            ]
        }
    ]
    # 메인 튜토리얼 루프
    while True:
        surface.fill((0,0,0))

        # 배경 박스
        pygame.draw.rect(surface, (30,30,30), ui_rect, border_radius=10)
        pygame.draw.rect(surface, (80,80,80), ui_rect, 2, border_radius=10)

        # 제목
        page = pages[page_index]
        title = font_title.render(f"튜토리얼 - {page['title']}", True, (255,255,255))
        surface.blit(title, (ui_rect.x + 30, ui_rect.y + 20))

        # 내용 그리기 (자동 줄바꿈 적용)
        y = ui_rect.y + 100
        max_text_w = ui_rect.width - 80
        for line in page["lines"]:
            wrapped = wrap_text(line, font, max_text_w)
            for wl in wrapped:
                txt = font.render(wl, True, (220,220,220))
                surface.blit(txt, (ui_rect.x + 40, y))
                y += txt.get_height() + 8

        # 버튼들
        mx, my = pygame.mouse.get_pos()
        # Back
        c = (140,140,140) if not back_rect.collidepoint((mx,my)) else (180,180,60)
        pygame.draw.rect(surface, c, back_rect, border_radius=8)
        back_txt = small.render("이전", True, (0,0,0))
        surface.blit(back_txt, (back_rect.x + (back_rect.width - back_txt.get_width())//2, back_rect.y + (back_rect.height - back_txt.get_height())//2))
        # Next
        c = (140,140,140) if not next_rect.collidepoint((mx,my)) else (180,180,60)
        pygame.draw.rect(surface, c, next_rect, border_radius=8)
        next_txt = small.render("다음", True, (0,0,0))
        surface.blit(next_txt, (next_rect.x + (next_rect.width - next_txt.get_width())//2, next_rect.y + (next_rect.height - next_txt.get_height())//2))

        # Close 또는 마지막 페이지 확인 버튼
        if page_index < len(pages)-1:
            c = (120,120,120) if not close_rect.collidepoint((mx,my)) else (200,80,80)
            pygame.draw.rect(surface, c, close_rect, border_radius=6)
            close_txt = small.render("X", True, (0,0,0))
            surface.blit(close_txt, (close_rect.x + (close_rect.width - close_txt.get_width())//2, close_rect.y + (close_rect.height - close_txt.get_height())//2))
        else:
            c = (140,140,140) if not confirm_rect.collidepoint((mx,my)) else (180,180,60)
            pygame.draw.rect(surface, c, confirm_rect, border_radius=8)
            confirm_txt = small.render("확인", True, (0,0,0))
            surface.blit(confirm_txt, (confirm_rect.x + (confirm_rect.width - confirm_txt.get_width())//2, confirm_rect.y + (confirm_rect.height - confirm_txt.get_height())//2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    page_index = max(0, page_index-1)
                if next_rect.collidepoint(event.pos):
                    page_index = min(len(pages)-1, page_index+1)
                if page_index < len(pages)-1 and close_rect.collidepoint(event.pos):
                    return
                if page_index == len(pages)-1 and confirm_rect.collidepoint(event.pos):
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
