"""스프라이트 시트 사용 예제

- 사용법:
    1) 스프라이트 시트 이미지 파일을 프로젝트의 적절한 위치(예: assets/image/)에 둡니다.
    2) 이 파일의 load_sprite_sheet(), get_frame() 함수를 사용해 프레임을 추출하여 사용합니다.

간단한 예제가 포함되어 있으니 필요에 따라 수정해서 사용하세요.
"""

import sys
import pygame
pygame.init()

def load_sprite_sheet(path):
    return pygame.image.load(path).convert_alpha()

def get_frame(sheet, x, y, w, h):
    """sheet에서 (x,y) 좌표와 (w,h) 크기의 프레임을 잘라 반환합니다."""
    return sheet.subsurface((x, y, w, h)).copy()

def extract_grid(sheet, cell_w, cell_h):
    """시트에서 셀 크기 기준으로 모든 프레임을 리스트로 반환합니다."""
    frames = []
    sw, sh = sheet.get_size()
    cols = sw // cell_w
    rows = sh // cell_h
    for r in range(rows):
        for c in range(cols):
            frames.append(get_frame(sheet, c*cell_w, r*cell_h, cell_w, cell_h))
    return frames

# --- 간단한 런 루프 (테스트 용) ---
if __name__ == '__main__':
    SCREEN = pygame.display.set_mode((480, 360))
    CLOCK = pygame.time.Clock()

    try:
        sheet = load_sprite_sheet('assets/image/full_texture.png')
    except Exception as e:
        print('스프라이트 시트를 로드할 수 없습니다:', e)
        pygame.quit()
        sys.exit()

    frames = extract_grid(sheet, 64, 64)  # 예: 64x64 프레임
    idx = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        SCREEN.fill((30, 30, 30))
        if frames:
            SCREEN.blit(frames[idx // 6 % len(frames)], (200, 140))
            idx += 1

        pygame.display.flip()
        CLOCK.tick(60)