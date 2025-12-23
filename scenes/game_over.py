import pygame
import sys

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

def game_over_screen(surface, player_level, survival_seconds, activated_towers, width, height):
    small_font = safe_font(size=26, bold=True)
    font = safe_font(size=36, bold=True)
    large_font = safe_font(size=72, bold=True)

    # 게임 오버 메시지
    game_over_text = large_font.render("GAME OVER!", True, (255, 0, 0))
    level_text = font.render(f"레벨: {player_level}", True, (255, 255, 255))

    # 생존 시간 및 활성 타워 텍스트
    mm = int(survival_seconds // 60)
    ss = int(survival_seconds % 60)
    time_text = font.render(f"생존 시간: {mm:02d}:{ss:02d}", True, (255, 255, 255))
    tower_text = font.render(f"활성화된 타워: {activated_towers}", True, (255, 255, 255))

    # 버튼 설정
    retry_button = pygame.Rect(width // 2 - 100, height // 2 + 70, 200, 50)
    quit_button = pygame.Rect(width // 2 - 100, height // 2 + 140, 200, 50)

    while True:
        surface.fill((0, 0, 0))  # 검은 배경

        # 텍스트 그리기
        surface.blit(game_over_text, (width // 2 - game_over_text.get_width() // 2, height // 2 - 300))
        surface.blit(level_text, (width // 2 - level_text.get_width() // 2, height // 2 - 150))
        surface.blit(time_text, (width // 2 - time_text.get_width() // 2, height // 2 - 90))
        surface.blit(tower_text, (width // 2 - tower_text.get_width() // 2, height // 2 - 30))

        # 버튼 그리기
        pygame.draw.rect(surface, (0, 200, 0), retry_button)
        pygame.draw.rect(surface, (200, 0, 0), quit_button)

        retry_text = small_font.render("다시하기", True, (255, 255, 255))
        quit_text = small_font.render("종료하기", True, (255, 255, 255))
        surface.blit(retry_text, (retry_button.centerx - retry_text.get_width() // 2, retry_button.centery - retry_text.get_height() // 2))
        surface.blit(quit_text, (quit_button.centerx - quit_text.get_width() // 2, quit_button.centery - quit_text.get_height() // 2))

        pygame.display.update()

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_button.collidepoint(event.pos):  # 다시하기 버튼 클릭
                    return "retry"
                if quit_button.collidepoint(event.pos):  # 끝내기 버튼 클릭
                    return "quit"
                
def game_success_screen(surface, survival_seconds, activated_towers, width, height):
    small_font = safe_font(size=26, bold=True)
    font = safe_font(size=36, bold=True)
    large_font = safe_font(size=72, bold=True)

    # 게임 성공 메시지
    success_text = large_font.render("CLEAR!", True, (0, 255, 0))
    congrats_text = font.render("모든 타워가 활성화되었습니다.", True, (255, 255, 255))

    # 생존 시간 및 활성 타워 텍스트
    mm = int(survival_seconds // 60)
    ss = int(survival_seconds % 60)
    time_text = font.render(f"생존 시간: {mm:02d}:{ss:02d}", True, (255, 255, 255))
    tower_text = font.render(f"활성화된 타워: {activated_towers}", True, (255, 255, 255))

    # 버튼 설정
    retry_button = pygame.Rect(width // 2 - 100, height // 2 + 70, 200, 50)
    quit_button = pygame.Rect(width // 2 - 100, height // 2 + 140, 200, 50)

    while True:
        surface.fill((0, 0, 0))  # 배경

        # 텍스트 그리기
        surface.blit(success_text, (width // 2 - success_text.get_width() // 2, height // 2 - 300))
        surface.blit(congrats_text, (width // 2 - congrats_text.get_width() // 2, height // 2 - 150))
        surface.blit(time_text, (width // 2 - time_text.get_width() // 2, height // 2 - 90))
        surface.blit(tower_text, (width // 2 - tower_text.get_width() // 2, height // 2 - 30))

        # 버튼 그리기
        pygame.draw.rect(surface, (0, 200, 0), retry_button)
        pygame.draw.rect(surface, (200, 0, 0), quit_button)

        retry_text = small_font.render("다시하기", True, (255, 255, 255))
        quit_text = small_font.render("종료하기", True, (255, 255, 255))
        surface.blit(retry_text, (retry_button.centerx - retry_text.get_width() // 2, retry_button.centery - retry_text.get_height() // 2))
        surface.blit(quit_text, (quit_button.centerx - quit_text.get_width() // 2, quit_button.centery - quit_text.get_height() // 2))

        pygame.display.update()

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_button.collidepoint(event.pos):  # 다시하기 버튼 클릭
                    return "retry"
                if quit_button.collidepoint(event.pos):  # 끝내기 버튼 클릭
                    return "quit"