import pygame
import random
import math
import os
import sys

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
GRAY = (100, 100, 100)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (150, 0, 150)
ORANGE = (255, 165, 0)
DARK_GRAY = (40, 40, 40)
UI_BG = (0, 0, 0, 180) # Semi-transparent black

# Game Settings
SPIRIT_TIME_LIMIT = 5.0  # Seconds
SPIRIT_SPEED = 5
POSSESSION_RANGE = 40

# --- Asset Loading ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")

def load_image(filename, fallback_color, size=(TILE_SIZE, TILE_SIZE)):
    path = os.path.join(ASSET_DIR, filename)
    try:
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(image, size)
    except (FileNotFoundError, pygame.error):
        surf = pygame.Surface(size)
        surf.fill(fallback_color)
        return surf

# --- Visual Effects Classes ---

class Particle:
    def __init__(self, x, y, dx, dy, color, lifespan, size=4):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.max_lifespan = lifespan
        self.lifespan = lifespan
        self.size = size

    def update(self, dt):
        self.x += self.dx * dt * 60
        self.y += self.dy * dt * 60
        self.lifespan -= dt
        self.size = max(0, self.size - dt * 2)

    def draw(self, surface, camera):
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (int(self.x), int(self.y))
        cam_rect = camera.apply_rect(rect)
        pygame.draw.circle(surface, self.color, cam_rect.center, int(self.size))

class Trail:
    def __init__(self, x, y, image, duration=0.5):
        self.x = x
        self.y = y
        self.image = image.copy()
        self.duration = duration
        self.max_duration = duration
        self.alpha = 150

    def update(self, dt):
        self.duration -= dt
        self.alpha = int(255 * (self.duration / self.max_duration))
        self.image.set_alpha(self.alpha)

    def draw(self, surface, camera):
        rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.image, camera.apply_rect(rect))

# --- Game Classes ---

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.shake_duration = 0
        self.shake_magnitude = 0

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def add_shake(self, duration, magnitude):
        self.shake_duration = duration
        self.shake_magnitude = magnitude

    def update(self, target, dt):
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)
        
        if self.shake_duration > 0:
            self.shake_duration -= dt
            x += random.randint(-self.shake_magnitude, self.shake_magnitude)
            y += random.randint(-self.shake_magnitude, self.shake_magnitude)

        self.camera = pygame.Rect(x, y, self.width, self.height)

class Map:
    def __init__(self, width=50, height=50):
        self.width = width
        self.height = height
        self.tile_size = TILE_SIZE
        self.tiles = {} 
        self.floor_tiles = []
        self.exit_pos = None
        self.floor_img = load_image("floor.png", (30, 30, 30))
        self.wall_img = load_image("wall.png", (80, 80, 80))
        self.generate_drunken_walk()

    def generate_drunken_walk(self):
        total_floors = int(self.width * self.height * 0.4) 
        cursor_x, cursor_y = self.width // 2, self.height // 2
        self.tiles[(cursor_x, cursor_y)] = 1
        self.floor_tiles.append((cursor_x, cursor_y))
        
        count = 1
        while count < total_floors:
            direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            cursor_x += direction[0]
            cursor_y += direction[1]
            cursor_x = max(1, min(self.width - 2, cursor_x))
            cursor_y = max(1, min(self.height - 2, cursor_y))
            
            if (cursor_x, cursor_y) not in self.tiles:
                self.tiles[(cursor_x, cursor_y)] = 1
                self.floor_tiles.append((cursor_x, cursor_y))
                count += 1
                
        while True:
            ex = random.choice(self.floor_tiles)
            if abs(ex[0] - self.width//2) > 10 or abs(ex[1] - self.height//2) > 10:
                self.tiles[ex] = 2 
                self.exit_pos = ex
                break

    def draw(self, surface, camera):
        start_col = max(0, -camera.camera.x // self.tile_size)
        end_col = start_col + (SCREEN_WIDTH // self.tile_size) + 2
        start_row = max(0, -camera.camera.y // self.tile_size)
        end_row = start_row + (SCREEN_HEIGHT // self.tile_size) + 2

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if (x, y) in self.tiles:
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                    cam_rect = camera.apply_rect(rect)
                    if self.tiles[(x, y)] == 2:
                        pygame.draw.rect(surface, YELLOW, cam_rect)
                        pygame.draw.rect(surface, WHITE, cam_rect, 2)
                    else:
                        surface.blit(self.floor_img, cam_rect)
                else:
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                    surface.blit(self.wall_img, camera.apply_rect(rect))

    def is_wall(self, x, y):
        grid_x = int(x // self.tile_size)
        grid_y = int(y // self.tile_size)
        return (grid_x, grid_y) not in self.tiles or self.tiles.get((grid_x, grid_y)) == 0

    def check_wall_collision(self, rect):
        start_col = int(rect.left // self.tile_size)
        end_col = int(rect.right // self.tile_size) + 1
        start_row = int(rect.top // self.tile_size)
        end_row = int(rect.bottom // self.tile_size) + 1
        
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                if (x, y) not in self.tiles or self.tiles.get((x, y)) == 0:
                     return True
        return False

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, image, speed):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = float(x)
        self.y = float(y)
        self.speed = speed

    def move_with_collision(self, dx, dy, map_obj):
        if dx != 0:
            self.x += dx
            self.rect.centerx = int(self.x)
            if map_obj.check_wall_collision(self.rect):
                self.x -= dx
                self.rect.centerx = int(self.x)
        if dy != 0:
            self.y += dy
            self.rect.centery = int(self.y)
            if map_obj.check_wall_collision(self.rect):
                self.y -= dy
                self.rect.centery = int(self.y)

class Actor(Entity):
    def __init__(self, x, y, image, speed, max_hp):
        super().__init__(x, y, image, speed)
        self.max_hp = max_hp
        self.hp = max_hp
        self.alive = True
        self.attack_cooldown = 0

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def update(self, dt, map_obj, player_ref, projectiles_group, particle_system):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

    def perform_attack(self, enemies_group, projectiles_group, particle_system, camera):
        pass 

class Projectile(Entity):
    def __init__(self, x, y, dx, dy, speed, duration, color=WHITE, size=10, damage=10, owner=None):
        img = pygame.Surface((size, size))
        img.fill(color)
        super().__init__(x, y, img, speed)
        self.vx = dx
        self.vy = dy
        self.duration = duration
        self.damage = damage
        self.color = color
        self.owner = owner
    
    def update(self, dt, map_obj, particle_system):
        self.duration -= dt
        if self.duration <= 0:
            self.kill()
        
        self.x += self.vx * self.speed
        self.y += self.vy * self.speed
        self.rect.center = (int(self.x), int(self.y))
        
        if random.random() < 0.3:
            p = Particle(self.x, self.y, 0, 0, self.color, 0.3, 2)
            particle_system.append(p)
        
        if map_obj.is_wall(self.rect.centerx, self.rect.centery):
            self.kill()
            for _ in range(5):
                p = Particle(self.x, self.y, random.gauss(0, 1), random.gauss(0, 1), self.color, 0.4)
                particle_system.append(p)

class Enemy(Actor):
    def __init__(self, x, y, image, speed, max_hp, level=1):
        hp = max_hp + (max_hp * 0.2 * (level - 1))
        super().__init__(x, y, image, speed, hp)
        self.notice_radius = 400
        self.damage = 10 + (2 * (level-1))
        self.level = level
        self.xp_value = 10 * level # XP given when killed

    def shoot_at(self, target_pos, projectiles_group, particle_system, color, size, speed, damage, cooldown):
        if self.attack_cooldown <= 0:
            angle = math.atan2(target_pos[1] - self.y, target_pos[0] - self.x)
            proj = Projectile(self.x, self.y, math.cos(angle), math.sin(angle), speed, 2.0, color, size, damage, owner=self)
            projectiles_group.add(proj)
            self.attack_cooldown = cooldown
            for _ in range(5):
                p = Particle(self.x, self.y, math.cos(angle)*2, math.sin(angle)*2, color, 0.2, 3)
                particle_system.append(p)

    def get_player_dist(self, player):
        target = player.host if (player.state == "POSSESSED" and player.host) else player.spirit_entity
        return math.hypot(target.x - self.x, target.y - self.y), target

    def ai_move_towards(self, target, map_obj):
        angle = math.atan2(target.y - self.y, target.x - self.x)
        dx = math.cos(angle) * self.speed
        dy = math.sin(angle) * self.speed
        self.move_with_collision(dx, dy, map_obj)

class Slime(Enemy):
    def __init__(self, x, y, level=1):
        img = load_image("slime.png", GREEN)
        super().__init__(x, y, img, speed=3, max_hp=30, level=level)
        self.projectile_speed = 6
        self.projectile_color = GREEN
    
    def perform_attack(self, enemies_group, projectiles_group, particle_system, camera):
        mx, my = pygame.mouse.get_pos()
        world_x = mx - camera.camera.x
        world_y = my - camera.camera.y
        self.shoot_at((world_x, world_y), projectiles_group, particle_system, self.projectile_color, 6, self.projectile_speed, self.damage, 0.3)

    def update(self, dt, map_obj, player, projectiles, particle_system):
        super().update(dt, map_obj, player, projectiles, particle_system)
        dist, target = self.get_player_dist(player)
        if dist < self.notice_radius:
            if dist > 100: self.ai_move_towards(target, map_obj)
            if self.attack_cooldown <= 0:
                self.shoot_at((target.x, target.y), projectiles, particle_system, self.projectile_color, 6, self.projectile_speed, self.damage, 1.0)

class Skeleton(Enemy):
    def __init__(self, x, y, level=1):
        img = load_image("skeleton.png", WHITE)
        super().__init__(x, y, img, speed=2, max_hp=50, level=level)
        self.projectile_speed = 7
        self.projectile_color = WHITE

    def perform_attack(self, enemies_group, projectiles_group, particle_system, camera):
         mx, my = pygame.mouse.get_pos()
         world_x = mx - camera.camera.x
         world_y = my - camera.camera.y
         self.shoot_at((world_x, world_y), projectiles_group, particle_system, self.projectile_color, 8, self.projectile_speed, self.damage, 0.5)

    def update(self, dt, map_obj, player, projectiles, particle_system):
        super().update(dt, map_obj, player, projectiles, particle_system)
        dist, target = self.get_player_dist(player)
        if dist < self.notice_radius:
            if dist > 150: self.ai_move_towards(target, map_obj)
            if self.attack_cooldown <= 0:
                self.shoot_at((target.x, target.y), projectiles, particle_system, self.projectile_color, 8, self.projectile_speed, self.damage, 2.0)

class IronKnight(Enemy):
    def __init__(self, x, y, level=1):
        img = load_image("knight.png", GRAY)
        super().__init__(x, y, img, speed=1, max_hp=100, level=level)
        self.projectile_speed = 4
        self.projectile_color = YELLOW
        self.damage = self.damage * 1.5

    def perform_attack(self, enemies_group, projectiles_group, particle_system, camera):
         mx, my = pygame.mouse.get_pos()
         world_x = mx - camera.camera.x
         world_y = my - camera.camera.y
         self.shoot_at((world_x, world_y), projectiles_group, particle_system, self.projectile_color, 14, self.projectile_speed, self.damage, 1.0)

    def update(self, dt, map_obj, player, projectiles, particle_system):
        super().update(dt, map_obj, player, projectiles, particle_system)
        dist, target = self.get_player_dist(player)
        if dist < self.notice_radius:
            self.ai_move_towards(target, map_obj)
            if self.attack_cooldown <= 0:
                 self.shoot_at((target.x, target.y), projectiles, particle_system, self.projectile_color, 14, self.projectile_speed, self.damage, 2.5)

class SpiritEntity(Entity):
    def __init__(self, x, y):
        img = load_image("spirit.png", CYAN, (24, 24))
        super().__init__(x, y, img, speed=SPIRIT_SPEED)

class Player:
    def __init__(self, start_x, start_y):
        self.state = "SPIRIT"
        self.spirit_timer = SPIRIT_TIME_LIMIT
        self.spirit_entity = SpiritEntity(start_x, start_y)
        self.host = None 
        self.start_pos = (start_x, start_y)
        
        # --- PROGRESSION STATS ---
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 100
        self.mutations = {
            "Corpse Explosion": False,
            "Time Thief": False,
            "Spirit Haste": False
        }
        self.available_upgrades = [] # Stores choices when leveling up

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            return True # Signal Level Up
        return False

    def update(self, dt, keys, map_obj, enemies, projectiles, camera, particle_system):
        if self.state == "SPIRIT":
            self.spirit_timer -= dt
            
            # Spirit Haste Mutation Logic
            current_speed = self.spirit_entity.speed
            if self.mutations["Spirit Haste"]:
                current_speed = SPIRIT_SPEED * 1.5
            
            dx, dy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
            
            if dx != 0 or dy != 0:
                length = math.hypot(dx, dy)
                dx, dy = dx/length, dy/length
                self.spirit_entity.move_with_collision(dx * current_speed, dy * current_speed, map_obj)
            
            if keys[pygame.K_SPACE]:
                closest = None
                min_dist = POSSESSION_RANGE
                for enemy in enemies:
                    dist = math.hypot(enemy.x - self.spirit_entity.x, enemy.y - self.spirit_entity.y)
                    if dist < min_dist:
                        min_dist = dist
                        closest = enemy
                if closest:
                    self.possess(closest, enemies, particle_system, camera)

        elif self.state == "POSSESSED":
            if not self.host or not self.host.alive:
                self.eject(enemies, particle_system, camera)
                return
            
            dx, dy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
            
            if dx != 0 or dy != 0:
                length = math.hypot(dx, dy)
                dx, dy = dx/length, dy/length
            
            self.host.move_with_collision(dx * self.host.speed, dy * self.host.speed, map_obj)
            
            # Update host cooldown manually since we don't call host.update()
            if self.host.attack_cooldown > 0:
                self.host.attack_cooldown -= dt

            mouse_pressed = pygame.mouse.get_pressed()
            if mouse_pressed[0]: # Left Click
                self.host.perform_attack(enemies, projectiles, particle_system, camera)
            
            if keys[pygame.K_e]:
                self.eject(enemies, particle_system, camera)

    def possess(self, enemy, enemies_group, particle_system, camera):
        self.state = "POSSESSED"
        self.host = enemy
        if enemy in enemies_group:
            enemies_group.remove(enemy)
        camera.add_shake(0.2, 5)
        for _ in range(10):
            p = Particle(enemy.x, enemy.y, random.gauss(0,1)*2, random.gauss(0,1)*2, CYAN, 0.5)
            particle_system.append(p)

    def eject(self, enemies_list, particle_system, camera):
        self.state = "SPIRIT"
        if self.host:
            self.spirit_entity.x = self.host.x
            self.spirit_entity.y = self.host.y
            self.spirit_entity.rect.center = (int(self.host.x), int(self.host.y))
            
            # --- CORPSE EXPLOSION MUTATION ---
            if self.mutations["Corpse Explosion"]:
                camera.add_shake(0.4, 15)
                # Visuals
                for _ in range(30):
                    p = Particle(self.host.x, self.host.y, random.gauss(0,1)*5, random.gauss(0,1)*5, ORANGE, 0.8, 6)
                    particle_system.append(p)
                # Damage enemies
                explode_radius = 150
                for e in enemies_list: # Note: This needs access to the enemies group or list
                    dist = math.hypot(e.x - self.host.x, e.y - self.host.y)
                    if dist < explode_radius:
                        e.take_damage(50)
            
            # Normal Eject Particles
            camera.add_shake(0.2, 5)
            for _ in range(10):
                p = Particle(self.host.x, self.host.y, random.gauss(0,1)*2, random.gauss(0,1)*2, RED, 0.5)
                particle_system.append(p)
                
            self.host = None

    def get_focus_entity(self):
        if self.state == "POSSESSED" and self.host:
            return self.host
        return self.spirit_entity

    def draw_ui(self, surface, level):
        # Spirit Timer
        rect_width = 200
        rect_height = 20
        fill = max(0, self.spirit_timer / SPIRIT_TIME_LIMIT)
        pygame.draw.rect(surface, GRAY, (10, 10, rect_width, rect_height))
        pygame.draw.rect(surface, CYAN, (10, 10, rect_width * fill, rect_height))
        pygame.draw.rect(surface, WHITE, (10, 10, rect_width, rect_height), 2)
        
        # XP Bar
        xp_width = 200
        xp_fill = self.xp / self.xp_to_next_level
        pygame.draw.rect(surface, DARK_GRAY, (10, 35, xp_width, 10))
        pygame.draw.rect(surface, PURPLE, (10, 35, xp_width * xp_fill, 10))
        font = pygame.font.SysFont(None, 20)
        xp_text = font.render(f"LVL {self.level}", True, WHITE)
        surface.blit(xp_text, (220, 32))
        
        # Host HP
        if self.state == "POSSESSED" and self.host:
            hp_fill = max(0, self.host.hp / self.host.max_hp)
            pygame.draw.rect(surface, GRAY, (10, 60, rect_width, rect_height))
            pygame.draw.rect(surface, RED, (10, 60, rect_width * hp_fill, rect_height))
            pygame.draw.rect(surface, WHITE, (10, 60, rect_width, rect_height), 2)
            font = pygame.font.SysFont(None, 24)
            img = font.render(f"Host: {type(self.host).__name__}", True, WHITE)
            surface.blit(img, (10 + rect_width + 10, 60))

        help_font = pygame.font.SysFont(None, 24)
        help_text = "WASD: Move | CLICK: Shoot | SPACE: Possess | E: Eject"
        surf = help_font.render(help_text, True, WHITE)
        surface.blit(surf, (10, SCREEN_HEIGHT - 30))
        lvl_surf = help_font.render(f"Dungeon Floor: {level}", True, YELLOW)
        surface.blit(lvl_surf, (SCREEN_WIDTH - 170, 10))

# --- Main Game Function ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spirit Thief - Progression Update")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    dungeon_level = 1
    
    # Game States: PLAYING, LEVEL_UP, GAME_OVER
    game_state = "PLAYING"

    def generate_level(level, player_obj):
        g_map = Map(60, 40)
        if len(g_map.floor_tiles) > 0:
            start_pos = g_map.floor_tiles[0]
            start_pixel = (start_pos[0] * TILE_SIZE + TILE_SIZE//2, start_pos[1] * TILE_SIZE + TILE_SIZE//2)
        else:
            start_pixel = (200, 200)

        if player_obj:
             if player_obj.state == "POSSESSED" and player_obj.host:
                player_obj.host.x = start_pixel[0]
                player_obj.host.y = start_pixel[1]
                player_obj.host.rect.center = start_pixel
                player_obj.host.max_hp += 20
                player_obj.host.hp = player_obj.host.max_hp
             else:
                player_obj.spirit_entity.x = start_pixel[0]
                player_obj.spirit_entity.y = start_pixel[1]
                player_obj.spirit_entity.rect.center = start_pixel
        else:
            player_obj = Player(start_pixel[0], start_pixel[1])
            # Force Host Start
            starter_host_type = random.choice([Slime, Skeleton, IronKnight])
            starter_host = starter_host_type(start_pixel[0], start_pixel[1], level=1)
            player_obj.possess(starter_host, [], [], Camera(0,0)) # Dummy args for groups/cam since not yet setup perfectly, but possess sets state
            # possess() calls camera.shake, but we just init cam later. That's fine.
            # possess() removes from enemies group but group is empty list. Fine.
            # possess() adds particles. Particles list is empty/local. We can pass a dummy list.
            
        cam = Camera(g_map.width * TILE_SIZE, g_map.height * TILE_SIZE)
        ens = pygame.sprite.Group()
        projs = pygame.sprite.Group()
        
        enemy_types = [Slime, Skeleton, IronKnight]
        spawn_count = 10 + (2 * level)
        
        for _ in range(spawn_count):
            if len(g_map.floor_tiles) > 0:
                pos = random.choice(g_map.floor_tiles)
                if pos == g_map.exit_pos: continue
                pixel = (pos[0] * TILE_SIZE + TILE_SIZE//2, pos[1] * TILE_SIZE + TILE_SIZE//2)
                if abs(pixel[0] - start_pixel[0]) < 300: continue
                
                etype = random.choice(enemy_types)
                e = etype(pixel[0], pixel[1], level=level)
                ens.add(e)
        return g_map, player_obj, cam, ens, projs

    game_map, player, camera, enemies, projectiles = generate_level(dungeon_level, None)
    particles = []
    trails = []
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0 
        
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False 
                
                if game_state == "GAME_OVER" and event.key == pygame.K_r:
                    dungeon_level = 1
                    game_map, player, camera, enemies, projectiles = generate_level(dungeon_level, None)
                    particles = []
                    trails = []
                    game_state = "PLAYING"

                # LEVEL UP SELECTION
                if game_state == "LEVEL_UP":
                    if event.key == pygame.K_1 and len(player.available_upgrades) >= 1:
                        player.mutations[player.available_upgrades[0]] = True
                        game_state = "PLAYING"
                    elif event.key == pygame.K_2 and len(player.available_upgrades) >= 2:
                        player.mutations[player.available_upgrades[1]] = True
                        game_state = "PLAYING"
                    elif event.key == pygame.K_3 and len(player.available_upgrades) >= 3:
                        player.mutations[player.available_upgrades[2]] = True
                        game_state = "PLAYING"

        # --- Game Logic ---
        if game_state == "PLAYING":
            keys = pygame.key.get_pressed()
            focus = player.get_focus_entity()
            camera.update(focus, dt)
            
            # Next Level Check
            current_entity = player.get_focus_entity()
            grid_pos = (int(current_entity.x // TILE_SIZE), int(current_entity.y // TILE_SIZE))
            if game_map.tiles.get(grid_pos) == 2:
                dungeon_level += 1
                game_map, player, camera, enemies, projectiles = generate_level(dungeon_level, player)
                particles = []
                trails = []
            
            # Update Entities
            # Pass 'enemies' group to player update so Corpse Explosion works
            player.update(dt, keys, game_map, enemies, projectiles, camera, particles) 
            
            for e in enemies:
                e.update(dt, game_map, player, projectiles, particles)
            
            for p in projectiles:
                p.update(dt, game_map, particles)
                # Host Hit Logic
                if player.state == "POSSESSED" and player.host:
                    if p.rect.colliderect(player.host.rect):
                        if p.owner != player.host:
                            player.host.take_damage(p.damage)
                            p.kill()
                            camera.add_shake(0.1, 3)
                # Enemy Hit Logic
                for e in enemies:
                    if p.rect.colliderect(e.rect):
                        if p.owner != e:
                            e.take_damage(p.damage)
                            p.kill()
                            if not e.alive:
                                # --- XP LOGIC ---
                                if player.gain_xp(e.xp_value):
                                    # Generate random unique upgrades
                                    possible = [k for k, v in player.mutations.items() if not v]
                                    if possible:
                                        player.available_upgrades = random.sample(possible, min(3, len(possible)))
                                        game_state = "LEVEL_UP"
                                
                                # --- TIME THIEF MUTATION ---
                                if player.mutations["Time Thief"]:
                                    player.spirit_timer = min(SPIRIT_TIME_LIMIT * 2, player.spirit_timer + 1.0)
                                    # Visual indicator for time thief
                                    particles.append(Particle(player.get_focus_entity().x, player.get_focus_entity().y, 0, -2, CYAN, 1.0, 5))
                                
                        
            if player.spirit_timer <= 0:
                game_state = "GAME_OVER"
            
            # Clean up dead enemies
            for e in list(enemies):
                if not e.alive:
                    enemies.remove(e)
            
            for p in particles[:]:
                p.update(dt)
                if p.lifespan <= 0: particles.remove(p)
            for t in trails[:]:
                t.update(dt)
                if t.duration <= 0: trails.remove(t)

        # --- Draw Loop ---
        screen.fill(BLACK)
        game_map.draw(screen, camera)
        
        for p in particles:
            if isinstance(p, Trail): p.draw(screen, camera)
        
        for e in enemies:
            screen.blit(e.image, camera.apply(e))
            hp_pct = e.hp / e.max_hp
            bar_rect = pygame.Rect(0, 0, 20, 4)
            bar_rect.midtop = e.rect.midbottom
            screen_bar = camera.apply_rect(bar_rect)
            pygame.draw.rect(screen, RED, screen_bar)
            pygame.draw.rect(screen, GREEN, (screen_bar.x, screen_bar.y, screen_bar.width * hp_pct, screen_bar.height))

        for p in projectiles:
            screen.blit(p.image, camera.apply(p))

        if player.state == "SPIRIT":
            screen.blit(player.spirit_entity.image, camera.apply(player.spirit_entity))
        elif player.state == "POSSESSED" and player.host:
            screen.blit(player.host.image, camera.apply(player.host))
            rect = camera.apply_rect(player.host.rect)
            pygame.draw.rect(screen, CYAN, rect, 2)

        for p in particles:
            if isinstance(p, Particle): p.draw(screen, camera)

        player.draw_ui(screen, dungeon_level)

        # --- OVERLAYS ---
        if game_state == "GAME_OVER":
            text = font.render("GAME OVER - Spirit Faded", True, RED)
            rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
            screen.blit(text, rect)
            sub = font.render(f"Press 'R' to Restart - ESC to Quit", True, WHITE)
            sub_rect = sub.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 40))
            screen.blit(sub, sub_rect)
        
        elif game_state == "LEVEL_UP":
            # Draw semi-transparent background
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(200)
            s.fill(BLACK)
            screen.blit(s, (0,0))
            
            title = font.render("SPIRIT EVOLUTION (Choose 1, 2, or 3)", True, YELLOW)
            screen.blit(title, (SCREEN_WIDTH//2 - 200, 100))
            
            y_offset = 200
            for i, upgrade in enumerate(player.available_upgrades):
                txt = font.render(f"{i+1}. {upgrade}", True, WHITE)
                screen.blit(txt, (SCREEN_WIDTH//2 - 100, y_offset))
                
                # Description
                desc = ""
                if upgrade == "Corpse Explosion": desc = "Ejecting causes massive Area Damage."
                if upgrade == "Time Thief": desc = "Kills restore Spirit Time."
                if upgrade == "Spirit Haste": desc = "Spirit moves 50% faster."
                
                desc_surf = pygame.font.SysFont(None, 24).render(desc, True, GRAY)
                screen.blit(desc_surf, (SCREEN_WIDTH//2 - 80, y_offset + 30))
                y_offset += 100

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
