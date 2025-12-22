import pygame
pygame.init()

sprite_sheet = pygame.image.load("full_texture.png").convert_alpha()

sprite = sprite_sheet.subsurface((0, 0, 64, 64))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((255, 255, 255))   # 배경 흰색
    screen.blit(sprite, (100, 100)) # 이미지 위치 (x, y)
    pygame.display.flip()

    pygame.time.Clock().tick(60)