<<<<<<< HEAD
print("Hello,World")
=======
import math
import random
import sys
import pygame

# =========================
# DASH & SLASH: LoL? LOL.
# pygame single-file roguelite-arena
# =========================

WIDTH, HEIGHT = 960, 540
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DASH & SLASH: LoL? LOL.")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 20)
bigfont = pygame.font.SysFont("consolas", 42, bold=True)

# --------- helpers
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def vec_from_angle(angle, length=1.0):
    return pygame.math.Vector2(math.cos(angle), math.sin(angle)) * length

def draw_text(surf, text, size, x, y, color=(240,240,240), center=False):
    f = pygame.font.SysFont("consolas", size, bold=False)
    t = f.render(text, True, color)
    r = t.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    surf.blit(t, r)

def circle_outline(surf, color, pos, radius, thickness=2):
    pygame.draw.circle(surf, color, pos, radius, thickness)

# --------- particles
class Particle:
    def __init__(self, pos, vel, life, color):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.life = life
        self.color = color
        self.max_life = life
        self.size = random.randint(2,4)

    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0: return
        alpha = clamp(int(255 * (self.life / self.max_life)), 0, 255)
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
        surf.blit(s, (self.pos.x - self.size, self.pos.y - self.size))

# --------- bullets (enemy projectiles)
class Bullet:
    def __init__(self, pos, vel, dmg, color=(250,120,120)):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.dmg = dmg
        self.color = color
        self.radius = 5
        self.alive = True

    def update(self, dt):
        self.pos += self.vel * dt
        if not ( -50 <= self.pos.x <= WIDTH+50 and -50 <= self.pos.y <= HEIGHT+50 ):
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

# --------- player
class Player:
    def __init__(self):
        self.pos = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
        self.vel = pygame.math.Vector2(0,0)
        self.speed = 240
        self.color = (120,200,255)
        self.radius = 14

        self.max_hp = 100
        self.hp = self.max_hp
        self.iframes = 0.0  # damage invuln
        self.dash_cd = 0.0
        self.dash_ready = True
        self.dash_speed = 750
        self.dash_time = 0.12
        self.dashing = 0.0

        # melee
        self.attack_cd = 0.0
        self.attack_rate = 0.35  # lower is faster
        self.attack_range = 60
        self.attack_arc = math.radians(70)
        self.damage = 18

        # meta stats
        self.coins = 0
        self.alive = True

        self.facing = 0

    def center(self): return (int(self.pos.x), int(self.pos.y))

    def update(self, dt, cursor, inputs):
        if not self.alive: return

        # movement
        direction = pygame.math.Vector2(0,0)
        if inputs["w"]: direction.y -= 1
        if inputs["s"]: direction.y += 1
        if inputs["a"]: direction.x -= 1
        if inputs["d"]: direction.x += 1
        if direction.length_squared() > 0:
            direction = direction.normalize()
        base_speed = self.speed * (1.8 if self.dashing>0 else 1.0)
        self.vel = direction * base_speed
        self.pos += self.vel * dt
        self.pos.x = clamp(self.pos.x, 16, WIDTH-16)
        self.pos.y = clamp(self.pos.y, 16, HEIGHT-16)

        # facing
        aim = pygame.math.Vector2(cursor) - self.pos
        self.facing = aim.as_polar()[1] * math.pi/180 if aim.length() > 0 else 0

        # timers
        self.iframes = max(0.0, self.iframes - dt)
        self.dash_cd = max(0.0, self.dash_cd - dt)
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.dashing = max(0.0, self.dashing - dt)

    def draw(self, surf):
        # body
        pygame.draw.circle(surf, self.color, self.center(), self.radius)
        # eye (shows facing)
        eye = vec_from_angle(self.facing, self.radius-3)
        pygame.draw.circle(surf, (30,30,40), (int(self.pos.x+eye.x), int(self.pos.y+eye.y)), 4)
        # hp bar
        hp_pct = self.hp / self.max_hp
        bw, bh = 80, 8
        bx, by = self.pos.x - bw/2, self.pos.y - self.radius - 14
        pygame.draw.rect(surf, (40,40,50), (bx, by, bw, bh), border_radius=4)
        pygame.draw.rect(surf, (60,230,120), (bx, by, bw*hp_pct, bh), border_radius=4)
        if self.dash_cd <= 0:
            circle_outline(surf, (200,255,255), self.center(), self.radius+6, 2)

    def try_dash(self, cursor):
        if self.dash_cd > 0 or self.dashing>0: return
        aim = pygame.math.Vector2(cursor) - self.pos
        if aim.length_squared()==0:
            aim = pygame.math.Vector2(1,0)
        dir = aim.normalize()
        self.pos += dir * 60  # snap forward a bit
        self.dashing = self.dash_time
        self.iframes = 0.18
        self.dash_cd = 1.2

    def take_damage(self, dmg):
        if self.iframes > 0 or self.dashing>0: return
        self.hp -= dmg
        self.iframes = 0.5
        if self.hp <= 0:
            self.alive = False

    def try_attack(self):
        if self.attack_cd>0: return False
        self.attack_cd = self.attack_rate
        return True

# --------- enemies
class Enemy:
    def __init__(self, kind, x, y, level):
        self.kind = kind  # "chaser" or "shooter" or "brute" or "boss"
        self.pos = pygame.math.Vector2(x,y)
        self.vel = pygame.math.Vector2(0,0)
        self.alive = True
        self.color = (250,90,90)
        self.target_angle = 0

        if kind=="chaser":
            self.radius = 12
            self.speed = 120 + level*6
            self.hp = 30 + level*4
            self.touch_dmg = 8 + level*1
            self.reload = 0
        elif kind=="shooter":
            self.radius = 12
            self.speed = 90 + level*4
            self.hp = 24 + level*4
            self.touch_dmg = 6 + level*1
            self.reload = random.uniform(0.8, 1.6)
        elif kind=="brute":
            self.radius = 18
            self.speed = 70 + level*3
            self.hp = 80 + level*10
            self.touch_dmg = 14 + level*2
            self.reload = 0
        elif kind=="boss":
            self.radius = 28
            self.speed = 85 + level*4
            self.hp = 800 + level*60
            self.touch_dmg = 20 + level*2
            self.reload = 1.2
        else:
            raise ValueError("unknown enemy kind")

    def update(self, dt, player, bullets, level):
        if not self.alive: return
        to_player = player.pos - self.pos
        dist = to_player.length() + 1e-6
        dir = to_player / dist

        # move
        self.vel = dir * self.speed
        self.pos += self.vel * dt
        self.target_angle = math.atan2(dir.y, dir.x)

        # contact damage
        if dist < self.radius + player.radius:
            player.take_damage(self.touch_dmg)

        # shooters/boss fire
        if self.kind in ("shooter", "boss"):
            self.reload -= dt
            if self.reload <= 0:
                self.fire(bullets, player, level)
                base = 1.4 if self.kind=="boss" else random.uniform(0.9,1.4)
                self.reload = base

    def fire(self, bullets, player, level):
        # aim with slight lead
        aim = (player.pos - self.pos)
        if aim.length_squared()==0:
            aim = pygame.math.Vector2(1,0)
        dir = aim.normalize()
        speed = 240 + level*10
        spread = 0.10 if self.kind=="boss" else 0.05
        count = 6 if self.kind=="boss" else 1
        for i in range(count):
            ang = math.atan2(dir.y, dir.x) + random.uniform(-spread, spread)
            v = vec_from_angle(ang, speed)
            bullets.append(Bullet(self.pos + dir* (self.radius+6), v, 10 + level*1.2, color=(250,160,90)))

    def draw(self, surf):
        c = (245,95,95) if self.kind!="boss" else (255,170,50)
        pygame.draw.circle(surf, c, (int(self.pos.x), int(self.pos.y)), self.radius)
        # little eye
        eye = vec_from_angle(self.target_angle, self.radius-4)
        pygame.draw.circle(surf, (30,10,10), (int(self.pos.x+eye.x), int(self.pos.y+eye.y)), 3)

# --------- pickups
class Pickup:
    def __init__(self, kind, pos, value):
        self.kind = kind  # "coin" or "heart"
        self.pos = pygame.math.Vector2(pos)
        self.value = value
        self.radius = 8 if kind=="coin" else 10
        self.color = (255,230,100) if kind=="coin" else (120,255,160)
        self.alive = True
        self.t = 0

    def update(self, dt, player):
        self.t += dt
        # magnet effect
        dist = (player.pos - self.pos).length()
        if dist < 120:
            self.pos += (player.pos - self.pos).normalize() * dt * 220
        if dist < self.radius + player.radius + 4:
            self.apply(player)

    def apply(self, player):
        if self.kind=="coin":
            player.coins += self.value
        elif self.kind=="heart":
            player.hp = clamp(player.hp + self.value, 0, player.max_hp)
        self.alive = False

    def draw(self, surf):
        r = self.radius + int(math.sin(self.t*6)*1.5)
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), r)

# --------- upgrade system
UPGRADES = [
    ("공속 업", "공격 쿨타임 -15%", "atk_rate", 0.85),
    ("검길 확장", "공격 범위 +20%", "atk_range", 1.20),
    ("근력 강화", "데미지 +25%", "damage", 1.25),
    ("체력 강화", "최대 HP +25, 즉시 +25 회복", "max_hp", 25),
    ("질주 본능", "대시 쿨타임 -20%", "dash_cd_mul", 0.80),
    ("신속", "이동 속도 +12%", "movespeed", 1.12),
    ("흡혈", "적 타격 시 체력 +2 (쿨 0.3s)", "lifesteal", 2),
    ("반사 신경", "총알 12% 확률로 무시", "bullet_ignore", 0.12),
    ("파수꾼", "접촉 피해 20% 감소", "contact_red", 0.80),
    ("상인과 친함", "동전 +30 즉시 지급", "coins", 30),
]

class UpgradeState:
    def __init__(self):
        self.choices = []
        self.lifesteal_cd = 0.0
        # derived stats on player side
        self.bullet_ignore = 0.0
        self.contact_mul = 1.0

    def roll(self):
        self.choices = random.sample(UPGRADES, 3)

    def apply(self, player, idx):
        name, desc, key, val = self.choices[idx]
        if key=="atk_rate":
            player.attack_rate *= val
        elif key=="atk_range":
            player.attack_range = int(player.attack_range * val)
        elif key=="damage":
            player.damage = int(player.damage * val)
        elif key=="max_hp":
            player.max_hp += val
            player.hp = clamp(player.hp + val, 0, player.max_hp)
        elif key=="dash_cd_mul":
            player.dash_cd *= val
        elif key=="movespeed":
            player.speed *= val
        elif key=="lifesteal":
            # store on self
            pass
        elif key=="bullet_ignore":
            self.bullet_ignore = max(self.bullet_ignore, val)
        elif key=="contact_red":
            self.contact_mul = min(self.contact_mul, val)
        elif key=="coins":
            player.coins += val

# --------- game
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.pickups = []
        self.particles = []
        self.wave = 0
        self.spawn_cd = 0
        self.state = "MENU"  # MENU, PLAY, UPGRADE, GAMEOVER
        self.upg = UpgradeState()
        self.best_wave = 0

    def spawn_wave(self):
        self.wave += 1
        self.best_wave = max(self.best_wave, self.wave)
        level = self.wave
        n = 6 + self.wave*2
        kinds = ["chaser", "shooter", "brute"]
        if self.wave % 5 == 0:
            # boss + minions
            self.enemies.append(Enemy("boss", *self.rand_edge_pos(), level))
            n += 6
        for i in range(n):
            k = random.choices(kinds, weights=[6,3,1])[0]
            x,y = self.rand_edge_pos()
            self.enemies.append(Enemy(k, x, y, level))

    def rand_edge_pos(self):
        # spawn from edges
        side = random.choice(["top","bottom","left","right"])
        if side=="top":
            return random.randint(0,WIDTH), -20
        if side=="bottom":
            return random.randint(0,WIDTH), HEIGHT+20
        if side=="left":
            return -20, random.randint(0,HEIGHT)
        return WIDTH+20, random.randint(0,HEIGHT)

    def update(self, dt, inputs, mouse_pos, mouse_down):
        if self.state=="MENU":
            return
        if self.state=="GAMEOVER":
            return
        if self.state=="UPGRADE":
            self.upg.lifesteal_cd = max(0.0, self.upg.lifesteal_cd - dt)
            return

        # PLAY
        self.player.update(dt, mouse_pos, inputs)
        self.upg.lifesteal_cd = max(0.0, self.upg.lifesteal_cd - dt)

        # attack
        if mouse_down and self.player.try_attack():
            self.swing()

        # spawn wave if clear
        if not self.enemies:
            self.state="UPGRADE"
            self.upg.roll()

        # update enemies
        for e in self.enemies:
            e.update(dt, self.player, self.bullets, self.wave)

        # update bullets
        for b in self.bullets:
            b.update(dt)

        # collisions: player with bullets
        for b in self.bullets:
            if not b.alive: continue
            if (self.player.pos - b.pos).length() < self.player.radius + b.radius:
                # bullet ignore?
                if random.random() < self.upg.bullet_ignore:
                    # spark
                    self.hit_sparks(b.pos, (180, 240, 255))
                else:
                    self.player.take_damage(b.dmg)
                b.alive = False

        # pickups
        for p in self.pickups:
            p.update(dt, self.player)

        # cleanup
        self.enemies = [e for e in self.enemies if e.alive]
        self.bullets = [b for b in self.bullets if b.alive]
        self.pickups = [p for p in self.pickups if p.alive]
        self.particles = [p for p in self.particles if p.life>0]

        if not self.player.alive:
            self.state="GAMEOVER"

    def hit_sparks(self, where, color=(255,200,120), amount=10):
        for _ in range(amount):
            ang = random.uniform(0, math.tau)
            speed = random.uniform(40, 220)
            vel = vec_from_angle(ang, speed)
            self.particles.append(Particle(where, vel, random.uniform(0.2,0.6), color))

    def swing(self):
        # apply melee damage in an arc
        angle = self.player.facing
        arc = self.player.attack_arc
        rng = self.player.attack_range
        origin = pygame.math.Vector2(self.player.pos)
        hit_any = False
        for e in self.enemies:
            to = e.pos - origin
            dist = to.length()
            if dist <= rng + e.radius:
                ang = math.atan2(to.y, to.x)
                d = abs((ang - angle + math.pi) % (2*math.pi) - math.pi)
                if d <= arc/2:
                    # damage with contact reduction on enemy touch to player handled elsewhere
                    e.hp -= self.player.damage
                    self.hit_sparks(e.pos)
                    if self.upg.lifesteal_cd<=0:
                        self.player.hp = clamp(self.player.hp + 2, 0, self.player.max_hp)  # base lifesteal 2 if taken
                    if e.hp <= 0:
                        e.alive=False
                        # drops
                        if random.random() < 0.4:
                            self.pickups.append(Pickup("coin", e.pos, random.randint(3,8)))
                        if random.random() < 0.15:
                            self.pickups.append(Pickup("heart", e.pos, random.randint(6,12)))
                    hit_any=True
        # draw a brief arc via particles
        for i in range(18):
            t = i/18
            ang = angle + (t-0.5)*arc
            pos = origin + vec_from_angle(ang, rng)
            self.particles.append(Particle(pos, vec_from_angle(ang, 30), 0.15, (255,255,255)))

    def draw(self, surf):
        surf.fill((18, 18, 24))
        # subtle arena grid
        for x in range(0, WIDTH, 40):
            pygame.draw.line(surf, (28,28,36), (x,0), (x,HEIGHT))
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(surf, (28,28,36), (0,y), (WIDTH,y))

        # entities
        for p in self.particles: p.draw(surf)
        for e in self.enemies: e.draw(surf)
        for b in self.bullets: b.draw(surf)
        for p in self.pickups: p.draw(surf)
        self.player.draw(surf)

        # HUD
        draw_text(surf, f"HP {int(self.player.hp)}/{self.player.max_hp}", 20, 10, 10)
        draw_text(surf, f"WAVE {self.wave}", 20, WIDTH-120, 10)
        draw_text(surf, f"COINS {self.player.coins}", 20, WIDTH-140, 34)
        draw_text(surf, "L-CLICK: Attack | SPACE: Dash | WASD: Move", 18, 10, HEIGHT-26, (170,190,210))

        if self.state=="MENU":
            title = "DASH & SLASH"
            draw_text(surf, title, 56, WIDTH/2, HEIGHT/2-60, (230,240,255), center=True)
            draw_text(surf, "LoL보다 재밌…진 않을 수도. 그래도 중독성 보장.", 22, WIDTH/2, HEIGHT/2, (200,210,230), center=True)
            draw_text(surf, "[ENTER] 시작  |  [M] 난이도: 보통  |  [Esc] 종료", 20, WIDTH/2, HEIGHT/2+40, (180,190,210), center=True)
        elif self.state=="UPGRADE":
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,160))
            surf.blit(s, (0,0))
            draw_text(surf, f"WAVE {self.wave} 완료! 업그레이드 선택", 30, WIDTH/2, 80, (255,255,255), center=True)
            for i,(name,desc,_,_) in enumerate(self.upg.choices):
                bx = 140 + i*260
                by = 160
                w,h = 220, 200
                pygame.draw.rect(surf, (36,36,52), (bx,by,w,h), border_radius=12)
                pygame.draw.rect(surf, (90,90,120), (bx,by,w,h), width=2, border_radius=12)
                draw_text(surf, f"{i+1}. {name}", 24, bx+16, by+20)
                draw_text(surf, desc, 18, bx+16, by+60, (210,220,230))
            draw_text(surf, "1 / 2 / 3 키로 선택", 22, WIDTH/2, HEIGHT-80, (220,230,240), center=True)
        elif self.state=="GAMEOVER":
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,160))
            surf.blit(s, (0,0))
            draw_text(surf, "GAME OVER", 64, WIDTH/2, HEIGHT/2-60, (255,160,160), center=True)
            draw_text(surf, f"최고 웨이브: {self.best_wave}", 26, WIDTH/2, HEIGHT/2, (230,230,240), center=True)
            draw_text(surf, "[R] 재시작   [Esc] 종료", 22, WIDTH/2, HEIGHT/2+50, (210,220,230), center=True)

    def handle_event(self, e, inputs):
        if self.state=="MENU":
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_RETURN:
                    self.state="PLAY"
                    self.spawn_wave()
                elif e.key==pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
        elif self.state=="UPGRADE":
            if e.type==pygame.KEYDOWN and e.unicode in ("1","2","3"):
                idx = int(e.unicode)-1
                self.upg.apply(self.player, idx)
                self.state="PLAY"
                self.spawn_wave()
        elif self.state=="GAMEOVER":
            if e.type==pygame.KEYDOWN and e.key==pygame.K_r:
                self.reset()
            elif e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        if self.state=="PLAY":
            if e.type==pygame.KEYDOWN and e.key==pygame.K_SPACE:
                self.player.try_dash(pygame.mouse.get_pos())
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                # soft pause -> back to menu? keep simple
                self.state="GAMEOVER" if not self.enemies else "UPGRADE"

# --------- main loop
def main():
    game = Game()
    inputs = {"w":False,"a":False,"s":False,"d":False}
    mouse_down = False

    while True:
        dt = clock.tick(FPS)/1000.0
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN or e.type==pygame.KEYUP:
                val = (e.type==pygame.KEYDOWN)
                if e.key==pygame.K_w: inputs["w"]=val
                if e.key==pygame.K_a: inputs["a"]=val
                if e.key==pygame.K_s: inputs["s"]=val
                if e.key==pygame.K_d: inputs["d"]=val
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                mouse_down = True
            if e.type==pygame.MOUSEBUTTONUP and e.button==1:
                mouse_down = False

            game.handle_event(e, inputs)

        mouse_pos = pygame.mouse.get_pos()
        game.update(dt, inputs, mouse_pos, mouse_down)
        game.draw(screen)

        # reticle
        pygame.draw.circle(screen, (255,255,255), mouse_pos, 10, 2)
        pygame.draw.circle(screen, (255,255,255), mouse_pos, 2)

        pygame.display.flip()

if __name__ == "__main__":
    main()
>>>>>>> 4141e3e (adspjaf)
