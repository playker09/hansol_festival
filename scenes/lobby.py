import pygame
import sys

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
    """튜토리얼: 키와 목표(타워) 사용법 안내 후 확인 버튼으로 진행"""
    font_title = pygame.font.SysFont("malgungothic", 48, bold=True)
    font = pygame.font.SysFont("malgungothic", 28)
    small = pygame.font.SysFont("malgungothic", 20)

    ui_w, ui_h = 860, 520
    ui_rect = pygame.Rect((WIDTH-ui_w)//2, (HEIGHT-ui_h)//2, ui_w, ui_h)
    confirm_rect = pygame.Rect(ui_rect.centerx-100, ui_rect.bottom-80, 200, 50)

    while True:
        surface.fill((0,0,0))

        # 배경 박스
        pygame.draw.rect(surface, (30,30,30), ui_rect, border_radius=10)
        pygame.draw.rect(surface, (80,80,80), ui_rect, 2, border_radius=10)

        # 제목
        title = font_title.render("튜토리얼", True, (255,255,255))
        surface.blit(title, (ui_rect.x + 30, ui_rect.y + 20))

        # 설명들
        lines = [
            ("이동: W A S D", "W / A / S / D 키로 이동합니다."),
            ("발사: 좌클릭", "왼쪽 마우스 버튼을 눌러 사격합니다."),
            ("대쉬: SHIFT", "Shift 키로 대쉬합니다 (쿨타임 있음)."),
            ("타워 위치", "화면 중앙 노란색 화살표는 타워의 위치를 알려줍니다."),
            ("타워 작동", "타워 근처에서 'E' 키를 눌러 활성화합니다."),
        ]

        y = ui_rect.y + 100
        for title_text, desc_text in lines:
            t = font.render(title_text, True, (255,255,0))
            d = small.render(desc_text, True, (220,220,220))
            surface.blit(t, (ui_rect.x + 40, y))
            surface.blit(d, (ui_rect.x + 360, y+4))
            y += 70

        # 확인 버튼
        mx, my = pygame.mouse.get_pos()
        if confirm_rect.collidepoint((mx,my)):
            c = (180,180,60)
        else:
            c = (140,140,140)
        pygame.draw.rect(surface, c, confirm_rect, border_radius=8)
        txt = font.render("확인", True, (0,0,0))
        surface.blit(txt, (confirm_rect.x + (confirm_rect.width - txt.get_width())//2, confirm_rect.y + (confirm_rect.height - txt.get_height())//2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if confirm_rect.collidepoint(event.pos):
                    return
