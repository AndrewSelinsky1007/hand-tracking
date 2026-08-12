import pygame
from sys import exit
import random
import math
from hand_tracker import HandTracker  

import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Update image load statements:
background_image = pygame.image.load(get_resource_path("flappybirdbg.png"))
bird_image = pygame.image.load(get_resource_path("flappybird.png"))
top_pipe_image = pygame.image.load(get_resource_path("toppipe.png"))
bottom_pipe_image = pygame.image.load(get_resource_path("bottompipe.png"))

# --- 1. SCALED GAME VARIABLES ---
GAME_WIDTH = 1280
GAME_HEIGHT = 720

# --- 2. 2D PHYSICS BIRD CLASS ---
bird_start_x = GAME_WIDTH / 8
bird_start_y = GAME_HEIGHT / 2
bird_width = 68
bird_height = 48

class Bird(pygame.Rect):
    def __init__(self, img):
        pygame.Rect.__init__(self, bird_start_x, bird_start_y, bird_width, bird_height)
        self.img = img
        self.vel_x = 0  
        self.vel_y = 0  

# --- 3. SCALED PIPE CLASS ---
pipe_x = GAME_WIDTH
pipe_y = 0
pipe_width = 120
pipe_height = 900

class Pipe(pygame.Rect):
    def __init__(self, img):
        pygame.Rect.__init__(self, pipe_x, pipe_y, pipe_width, pipe_height)
        self.img = img
        self.passed = False

# --- 4. SCALED GAME IMAGES ---
background_image = pygame.image.load("flappybirdbg.png")
background_image = pygame.transform.scale(background_image, (GAME_WIDTH, GAME_HEIGHT))

bird_image = pygame.image.load("flappybird.png")
bird_image = pygame.transform.scale(bird_image, (bird_width, bird_height))

top_pipe_image = pygame.image.load("toppipe.png")
top_pipe_image = pygame.transform.scale(top_pipe_image, (pipe_width, pipe_height))

bottom_pipe_image = pygame.image.load("bottompipe.png")
bottom_pipe_image = pygame.transform.scale(bottom_pipe_image, (pipe_width, pipe_height))

# --- 5. INITIALIZE ENTITIES & TRACKER ---
bird = Bird(bird_image)
pipes = []
PIPE_SPEED = -5    
gravity = 0.6
game_over = False
game_started = False  # <--- NEW: Controls the pre-round waiting state
hit_cooldown = 0  

# --- NEW: SCORING & COMBO VARIABLES ---
score = 0
high_score = 0
pending_score = 0
pending_timer = 0
consecutive_pipes = 0
pipe_halves_passed = 0  

# Persistent visual variables for combos
display_combo_pipes = 0
display_combo_score = 0

tracker = HandTracker(screen_width=GAME_WIDTH, screen_height=GAME_HEIGHT, z_threshold=-0.05, show_raw_feed=True)
prev_pts = []

# --- HELPER FUNCTION: TEXT WITH OUTLINE ---
def draw_text_outlined(surface, text, font, text_color, outline_color, x, y):
    for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2), (-2,0), (2,0), (0,-2), (0,2)]:
        out_surf = font.render(text, True, outline_color)
        surface.blit(out_surf, (x + dx, y + dy))
    
    main_surf = font.render(text, True, text_color)
    surface.blit(main_surf, (x, y))
    
    return main_surf.get_rect(topleft=(x, y))


def draw():
    window.blit(background_image, (0, 0))
    window.blit(bird.img, bird)

    for pipe in pipes:
        window.blit(pipe.img, pipe)
    
    if tracker.has_hand:
        tracker.is_engaged = True 
        tracker.draw(window) 
    
    # --- HUD RENDERING ---
    text_font = pygame.font.SysFont("Consolas", 60, bold=True)
    combo_font = pygame.font.SysFont("Consolas", 40, bold=True)
    
    if game_over:
        go_str = f"Game Over! Final Score: {int(score)}"
        go_surf = text_font.render(go_str, True, "white")
        go_x = GAME_WIDTH // 2 - go_surf.get_width() // 2
        go_y = GAME_HEIGHT // 2 - 50
        draw_text_outlined(window, go_str, text_font, "white", "black", go_x, go_y)
        
        hi_str = f"High Score: {int(high_score)}"
        hi_surf = combo_font.render(hi_str, True, "gold")
        hi_x = GAME_WIDTH // 2 - hi_surf.get_width() // 2
        hi_y = go_y + 80
        draw_text_outlined(window, hi_str, combo_font, "gold", "black", hi_x, hi_y)
        
    else:
        hi_str = f"High Score: {int(high_score)}"
        hi_surf = combo_font.render(hi_str, True, "white")
        draw_text_outlined(window, hi_str, combo_font, "white", "black", GAME_WIDTH // 2 - hi_surf.get_width() // 2, 10)
        
        score_rect = draw_text_outlined(window, str(int(score)), text_font, "white", "black", 20, 10)
        
        # Draw Start Prompt if waiting
        if not game_started:
            start_str = "TOUCH BIRD TO START"
            start_surf = text_font.render(start_str, True, "white")
            draw_text_outlined(window, start_str, text_font, "white", "black", GAME_WIDTH // 2 - start_surf.get_width() // 2, GAME_HEIGHT // 2 + 100)
        
        # 3. Pending Score & Persistent Combo Display
        elif display_combo_pipes >= 2:
            time_ms = pygame.time.get_ticks()
            flash_factor = (math.sin(time_ms * 0.015) + 1) / 2  
            g_color = int(165 + (90 * flash_factor))
            flash_color = (255, g_color, 0) 
            
            draw_text_outlined(window, f"+{int(display_combo_score)}", text_font, flash_color, "black", score_rect.right + 15, 10)
            
            combo_str = f"{display_combo_pipes} consecutive pipes"
            draw_text_outlined(window, combo_str, combo_font, flash_color, "black", 20, score_rect.bottom + 5)
            
        elif pending_score > 0 and consecutive_pipes == 1:
            draw_text_outlined(window, f"+{int(pending_score)}", text_font, "white", "black", score_rect.right + 15, 10)


def move():
    global score, high_score, pending_score, pending_timer
    global consecutive_pipes, pipe_halves_passed, game_over, hit_cooldown
    global display_combo_pipes, display_combo_score
    global game_started, last_pipe_time
    
    if hit_cooldown > 0:
        hit_cooldown -= 1

    # --- ONLY APPLY PHYSICS IF GAME HAS STARTED ---
    if game_started:
        bird.vel_y += gravity
        bird.x += bird.vel_x
        bird.y += bird.vel_y

        if pending_timer > 0:
            pending_timer -= 1
            if pending_timer == 0:
                score += pending_score
                if score > high_score: high_score = score
                pending_score = 0
                consecutive_pipes = 0
                pipe_halves_passed = 0

        if bird.left < 0:
            bird.left = 0
            bird.vel_x *= -0.8  
        if bird.right > GAME_WIDTH:
            bird.right = GAME_WIDTH
            bird.vel_x *= -0.8  
        if bird.top < 0:
            bird.top = 0
            bird.vel_y *= -0.8  

        if bird.top > GAME_HEIGHT:
            if pending_score > 0 and consecutive_pipes < 2:
                score += pending_score
            if display_combo_score > 0:
                score += display_combo_score
            if score > high_score: high_score = score
            
            pending_score = 0
            display_combo_score = 0
            game_over = True
            return

    # --- COLLISION CHECK ALWAYS RUNS (SO WE CAN START THE GAME) ---
    if tracker.has_hand and tracker.pts and hit_cooldown == 0:
        collision_detected = False
        bone_vel_x, bone_vel_y = 0, 0
        nx, ny = 0, -1 
        
        catch_rect = bird.inflate(50, 50)
        
        for p1_idx, p2_idx in tracker.connections:
            p1 = tracker.pts[p1_idx]
            p2 = tracker.pts[p2_idx]
            
            if catch_rect.clipline(p1, p2):
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                length = max(1, (dx**2 + dy**2)**0.5)
                ux, uy = dx/length, dy/length
                
                n1x, n1y = -uy, ux
                n2x, n2y = uy, -ux
                
                bone_cx = (p1[0] + p2[0]) / 2
                bone_cy = (p1[1] + p2[1]) / 2
                to_bird_x = bird.centerx - bone_cx
                to_bird_y = bird.centery - bone_cy
                
                if (n1x * to_bird_x + n1y * to_bird_y) > 0:
                    nx, ny = n1x, n1y
                else:
                    nx, ny = n2x, n2y

                if len(prev_pts) == 21:
                    prev_cx = (prev_pts[p1_idx][0] + prev_pts[p2_idx][0]) / 2
                    prev_cy = (prev_pts[p1_idx][1] + prev_pts[p2_idx][1]) / 2
                    bone_vel_x = bone_cx - prev_cx
                    bone_vel_y = bone_cy - prev_cy
                
                collision_detected = True
                break 
                
        if collision_detected:
            
            # --- START GAME ON FIRST HIT ---
            if not game_started:
                game_started = True
                last_pipe_time = pygame.time.get_ticks() # Reset pipe spawn timer so they don't pile up
            else:
                if pending_score > 0:
                    if consecutive_pipes >= 2:
                        pass
                    else:
                        score += pending_score
                        if score > high_score: high_score = score
            
            pending_score = 0
            pending_timer = 0
            consecutive_pipes = 0
            pipe_halves_passed = 0

            if abs(bone_vel_x) < 4: bone_vel_x = 0
            if abs(bone_vel_y) < 4: bone_vel_y = 0

            bird.vel_x = (nx * 8) + (bone_vel_x * 0.8)
            bird.vel_y = -5 + (ny * 8) + (bone_vel_y * 0.8)

            hit_cooldown = 10 

    # --- ONLY MOVE PIPES IF GAME HAS STARTED ---
    if game_started:
        for pipe in pipes:
            pipe.x += PIPE_SPEED

            if not pipe.passed and bird.left > pipe.right:
                pipe.passed = True
                pipe_halves_passed += 1
                
                if pipe_halves_passed % 2 == 0:
                    consecutive_pipes += 1
                    
                    if consecutive_pipes == 1:
                        gap_points = 1
                        pending_timer = 120 
                        
                        if display_combo_score > 0:
                            score += display_combo_score
                            if score > high_score: high_score = score
                            display_combo_pipes = 0
                            display_combo_score = 0
                    else:
                        gap_points = 2 ** consecutive_pipes 
                        pending_timer = 0 
                    
                    pending_score += gap_points
                    
                    if consecutive_pipes >= 2:
                        display_combo_pipes = consecutive_pipes
                        display_combo_score = pending_score
            
            if bird.colliderect(pipe):
                if pending_score > 0 and consecutive_pipes < 2:
                    score += pending_score
                if display_combo_score > 0:
                    score += display_combo_score
                if score > high_score: high_score = score
                
                pending_score = 0
                display_combo_score = 0
                game_over = True
                return
                
        while len(pipes) > 0 and pipes[0].x < -pipe_width:
            pipes.pop(0)


def create_pipes():
    min_gap = 250
    max_gap = 450
    opening_space = random.randint(min_gap, max_gap)
    
    min_top_pipe_bottom = 100
    max_top_pipe_bottom = GAME_HEIGHT - opening_space - 100
    top_pipe_bottom = random.randint(int(min_top_pipe_bottom), int(max_top_pipe_bottom))
    random_pipe_y = top_pipe_bottom - pipe_height

    top_pipe = Pipe(top_pipe_image)
    top_pipe.y = random_pipe_y
    pipes.append(top_pipe)

    bottom_pipe = Pipe(bottom_pipe_image)
    bottom_pipe.y = top_pipe.y + top_pipe.height + opening_space
    pipes.append(bottom_pipe)

pygame.init()
window = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

last_pipe_time = pygame.time.get_ticks()
next_pipe_delay = 2500  

while True: 
    tracker.update()
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            tracker.close() 
            pygame.quit()
            exit()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_over:
                bird.x = bird_start_x
                bird.y = bird_start_y
                bird.vel_x = 0
                bird.vel_y = 0
                pipes.clear()
                
                score = 0
                pending_score = 0
                pending_timer = 0
                consecutive_pipes = 0
                pipe_halves_passed = 0
                display_combo_pipes = 0
                display_combo_score = 0
                
                game_over = False
                game_started = False  # Return to the waiting state
                hit_cooldown = 0
                
                last_pipe_time = pygame.time.get_ticks()
                next_pipe_delay = 2500

    # Pipes only spawn when game is active
    if game_started and current_time - last_pipe_time > next_pipe_delay and not game_over:
        create_pipes()
        last_pipe_time = current_time
        next_pipe_delay = random.randint(1800, 3600)

    if not game_over:
        move()
    
    draw()
    pygame.display.update()
    
    if tracker.has_hand and tracker.pts:
        prev_pts = tracker.pts.copy()
    else:
        prev_pts = []
        
    clock.tick(60)