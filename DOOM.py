import pygame
import math
import os
import random

pygame.init()

# ---------------- SCREEN ----------------
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

mouse_sens = 0.002

ASSETS = "/home/a/PycharmProjects/PythonProject/units2"


# ---------------- LOAD ----------------
def load_img(path, size=(64, 64)):
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    surf = pygame.Surface(size)
    surf.fill((200, 0, 200))
    return surf


# ---------------- MAP ----------------
game_map = [
    "1111111111111111",
    "1000000000000001",
    "1011110111111101",
    "1000000000000001",
    "1010111111110101",
    "1000000000000001",
    "1011110000111101",
    "1000000000000001",
    "1111111111111111",
]

MAP_W = len(game_map[0])
MAP_H = len(game_map)
TILE = 64


# ---------------- TEXTURES ----------------
wall_texture = load_img(f"{ASSETS}/wall.png")
player_tex = load_img(f"{ASSETS}/player.png", (120, 320))
enemy_tex = load_img(f"{ASSETS}/enemy.png", (120, 320))
weapon_img = load_img(f"{ASSETS}/weapon.png", (260, 260))


# ---------------- ROUND SYSTEM ----------------
ROUND_TIME = 999999
round_timer = ROUND_TIME
ct_score = 0
t_score = 0
round_over = False


# ---------------- ENTITY ----------------
class Entity:
    def __init__(self, x, y, team, tex):
        self.spawn_x = x
        self.spawn_y = y
        self.x = x
        self.y = y
        self.team = team
        self.tex = tex
        self.hp = 100
        self.alive = True
        self.angle = 0
        self.target_x = x
        self.target_y = y
        self.cooldown = 0
        self.inv = 0

    def respawn(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.hp = 100
        self.alive = True
        self.inv = 120


# ---------------- SPAWNS ----------------
ct_spawns = [(120,120),(160,160),(200,200)]
t_spawns  = [(800,120),(760,160),(720,200)]

entities = []

for x,y in ct_spawns:
    entities.append(Entity(x,y,"ct",player_tex))

for x,y in t_spawns:
    entities.append(Entity(x,y,"t",enemy_tex))

player = entities[0]


# ---------------- COLLISION ----------------
def is_wall(x,y):
    i=int(x//TILE)
    j=int(y//TILE)
    if i<0 or j<0 or i>=MAP_W or j>=MAP_H:
        return True
    return game_map[j][i]=="1"


def move(e,dx,dy):
    if not is_wall(e.x+dx,e.y):
        e.x+=dx
    if not is_wall(e.x,e.y+dy):
        e.y+=dy


# ---------------- LOS ----------------
def los(x1,y1,x2,y2):
    steps=int(math.hypot(x2-x1,y2-y1))
    for i in range(0,steps,5):
        t=i/steps if steps else 0
        x=x1+(x2-x1)*t
        y=y1+(y2-y1)*t
        if is_wall(x,y):
            return False
    return True


# ---------------- SHOOT ----------------
def shoot():
    lx=math.cos(player.angle)
    ly=math.sin(player.angle)

    for e in entities:
        if e is player or not e.alive:
            continue
        if e.team==player.team:
            continue

        dx=e.x-player.x
        dy=e.y-player.y
        dist=math.hypot(dx,dy)
        if dist==0:
            continue

        dx/=dist
        dy/=dist

        if lx*dx+ly*dy>0.985 and dist<500:
            e.hp-=10
            if e.hp<=0:
                e.alive=False


# ---------------- AI (FIXED + MOVING ALWAYS) ----------------
def ai(e):
    if e is player:
        return

    if not e.alive:
        return

    target = player

    dx = target.x - e.x
    dy = target.y - e.y
    dist = math.hypot(dx, dy)

    sees = dist < 500 and los(e.x,e.y,target.x,target.y)

    # ---------------- ATTACK ----------------
    if sees:

        e.angle = math.atan2(dy,dx)

        if e.cooldown <= 0:
            if target.team != e.team:
                target.hp -= 5

                if target.hp <= 0:
                    target.alive = False

            e.cooldown = 50
        else:
            e.cooldown -= 1

    # ---------------- MOVE (IMPORTANT FIX) ----------------
    # always move - not stuck anymore
    if math.hypot(e.x-e.target_x,e.y-e.target_y) < 25:
        e.target_x = random.randint(2,MAP_W-2)*TILE
        e.target_y = random.randint(2,MAP_H-2)*TILE

    dx = e.target_x - e.x
    dy = e.target_y - e.y

    d = math.hypot(dx,dy)
    if d:
        dx/=d
        dy/=d

    move(e,dx*1.5,dy*1.5)


# ---------------- ROUND CHECK ----------------
def check_round():
    global ct_score, t_score, round_over

    ct_alive = any(e.alive and e.team=="ct" for e in entities)
    t_alive  = any(e.alive and e.team=="t" for e in entities)

    if not ct_alive or not t_alive:
        round_over = True

        if not ct_alive:
            t_score += 1
        if not t_alive:
            ct_score += 1


def reset_round():
    global round_over

    for e in entities:
        e.respawn()

    player.hp = 100
    round_over = False


# ---------------- WALLS ----------------
def draw_walls():
    start=player.angle-math.pi/6

    for r in range(160):
        ang=start+r*(math.pi/3)/160

        for d in range(1,800):
            x=player.x+math.cos(ang)*d
            y=player.y+math.sin(ang)*d

            if is_wall(x,y):
                d*=math.cos(player.angle-ang)
                h=60000/(d+0.0001)

                tx=int((x%TILE)/TILE*64)

                col=wall_texture.subsurface(tx,0,1,64)
                col=pygame.transform.scale(col,
                    (WIDTH//160,int(h)))

                screen.blit(col,
                    (r*(WIDTH//160),
                     HEIGHT//2-h//2))
                break


# ---------------- ENTITIES ----------------
def draw_entities():
    for e in entities:
        if e is player or not e.alive:
            continue

        dx=e.x-player.x
        dy=e.y-player.y

        dist=math.hypot(dx,dy)
        ang=math.atan2(dy,dx)
        diff=ang-player.angle

        if -math.pi/6<diff<math.pi/6:

            h=12000/(dist+0.0001)
            h=max(20,min(250,h))
            w=h*0.4

            sx=(diff+math.pi/6)/(math.pi/3)*WIDTH

            sprite=pygame.transform.scale(e.tex,(int(w),int(h)))

            screen.blit(sprite,(sx-w/2,HEIGHT/2-h/2))


# ---------------- MINIMAP ----------------
def draw_minimap():
    scale=0.2

    for j,row in enumerate(game_map):
        for i,c in enumerate(row):
            if c=="1":
                pygame.draw.rect(screen,(70,70,70),
                    (i*TILE*scale,j*TILE*scale,TILE*scale,TILE*scale))

    for e in entities:
        color=(0,255,0) if e.team=="ct" else (255,0,0)
        pygame.draw.circle(screen,color,
            (int(e.x*scale),int(e.y*scale)),3)

    pygame.draw.circle(screen,(0,0,255),
        (int(player.x*scale),int(player.y*scale)),4)


# ---------------- CROSSHAIR ----------------
def crosshair():
    x,y=WIDTH//2,HEIGHT//2
    s=6
    pygame.draw.line(screen,(255,0,0),(x-s,y),(x+s,y),2)
    pygame.draw.line(screen,(255,0,0),(x,y-s),(x,y+s),2)


# ---------------- LOOP ----------------
running=True
while running:

    screen.fill((20,20,20))

    mx,my=pygame.mouse.get_rel()
    player.angle+=mx*mouse_sens

    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            running=False
        if ev.type==pygame.MOUSEBUTTONDOWN:
            shoot()

    keys=pygame.key.get_pressed()
    sp=3

    if keys[pygame.K_w]:
        move(player,math.cos(player.angle)*sp,
                     math.sin(player.angle)*sp)
    if keys[pygame.K_s]:
        move(player,-math.cos(player.angle)*sp,
                     -math.sin(player.angle)*sp)
    if keys[pygame.K_a]:
        move(player,math.sin(player.angle)*sp,
                     -math.cos(player.angle)*sp)
    if keys[pygame.K_d]:
        move(player,-math.sin(player.angle)*sp,
                     math.cos(player.angle)*sp)

    for e in entities:
        ai(e)

    check_round()

    if round_over:
        reset_round()

    draw_walls()
    draw_entities()

    screen.blit(weapon_img,(WIDTH//2-130,HEIGHT-260))
    crosshair()
    draw_minimap()

    font=pygame.font.SysFont("Arial",24)
    screen.blit(font.render(f"HP:{player.hp}",True,(255,0,0)),(20,20))
    screen.blit(font.render(f"CT {ct_score} : T {t_score}",True,(255,255,255)),(20,50))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
