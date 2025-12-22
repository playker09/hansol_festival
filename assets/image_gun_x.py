import pygame
import os

# NOTE: don't call pygame.init() here — modules should not initialize/quit the video system on import.
# Image loading should be safe even if display hasn't been set yet.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_PATH = os.path.join(BASE_DIR, "assets", "image")

texture_gun = pygame.image.load(os.path.join(IMAGE_PATH, "texture_gun.png"))
# Try to convert for faster blits, but skip if display not initialized yet
try:
    texture_gun = texture_gun.convert_alpha()
except Exception:
    # convert_alpha may fail if no video mode is set; that's okay — leave as-is
    pass

texture_bullet_silver = texture_gun.subsurface(pygame.Rect(0, 0, 3, 2)).copy()
texture_bullet_bronze = texture_gun.subsurface(pygame.Rect(0, 2, 3, 2)).copy()
texture_bullet_shotgun = texture_gun.subsurface(pygame.Rect(0, 4, 4, 2)).copy()
texture_bullet_shotgun_used = texture_gun.subsurface(pygame.Rect(0, 7, 4, 3)).copy()
texture_bullet_iron = texture_gun.subsurface(pygame.Rect(0, 6, 1, 1)).copy()

texture_effect_1 = texture_gun.subsurface(pygame.Rect(4, 0, 12, 9)).copy()
texture_effect_2 = texture_gun.subsurface(pygame.Rect(16, 0, 12, 9)).copy()

texture_gun_ak47 = texture_gun.subsurface(pygame.Rect(0, 10, 22, 7)).copy()
texture_gun_rifle = texture_gun.subsurface(pygame.Rect(0, 17, 32, 9)).copy()
texture_gun_smg = texture_gun.subsurface(pygame.Rect(0, 26, 13, 10)).copy()
texture_gun_dmr = texture_gun.subsurface(pygame.Rect(0, 36, 41, 8)).copy()
texture_gun_shotgun = texture_gun.subsurface(pygame.Rect(0, 44, 28, 6)).copy()
texture_gun_easteregg = texture_gun.subsurface(pygame.Rect(0, 50, 23, 10)).copy()