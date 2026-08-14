import pygame
import sys
import random
import math
from hand_tracker2 import HandTracker

pygame.init()

WIDTH, HEIGHT = 1280, 720
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()

# Fonts for Polish
font_large = pygame.font.SysFont("Consolas", 48, bold=True)
font_medium = pygame.font.SysFont("Consolas", 24, bold=True)
font_small = pygame.font.SysFont("Consolas", 18)

# Tetris Grid Constants
BLOCK_SIZE = 30
COLS, ROWS = 10, 20
BOARD_WIDTH = COLS * BLOCK_SIZE
BOARD_HEIGHT = ROWS * BLOCK_SIZE
BOARD_X = (WIDTH - BOARD_WIDTH) // 2
BOARD_Y = (HEIGHT - BOARD_HEIGHT) // 2

SHAPES = [
    [[1, 1, 1, 1]],                            # I
    [[1, 1], [1, 1]],                          # O
    [[0, 1, 0], [1, 1, 1]],                    # T
    [[1, 0, 0], [1, 1, 1]],                    # L
    [[0, 0, 1], [1, 1, 1]],                    # J
    [[0, 1, 1], [1, 1, 0]],                    # S
    [[1, 1, 0], [0, 1, 1]]                     # Z
]

COLORS = [
    (0, 255, 255), (255, 255, 0), (128, 0, 128),
    (255, 165, 0), (0, 0, 255), (0, 255, 0), (255, 0, 0)
]

FLASH_COLORS = [(255, 50, 50), (255, 165, 0), (255, 255, 255)] # Red, Orange, White

def get_new_piece():
    shape = random.choice(SHAPES)
    color = COLORS[SHAPES.index(shape)]
    return shape, color

def create_grid():
    return [[(0, 0, 0) for _ in range(COLS)] for _ in range(ROWS)]

def check_collision(board, shape, offset):
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            if cell:
                if (cx + off_x < 0 or cx + off_x >= COLS or 
                    cy + off_y >= ROWS or 
                    (cy + off_y >= 0 and board[cy + off_y][cx + off_x] != (0, 0, 0))):
                    return True
    return False

def clear_lines(board):
    new_board = [row for row in board if (0, 0, 0) in row]
    lines_cleared = ROWS - len(new_board)
    for _ in range(lines_cleared):
        new_board.insert(0, [(0, 0, 0) for _ in range(COLS)])
    return new_board, lines_cleared

def main():
    tracker = HandTracker(screen_width=WIDTH, screen_height=HEIGHT, show_raw_feed=True)
    
    board = create_grid()
    next_pieces = [get_new_piece() for _ in range(3)]
    current_shape, current_color = get_new_piece()
    piece_x = COLS // 2 - len(current_shape[0]) // 2
    piece_y = 0

    # Game State Variables
    game_state = "PLAYING" # States: PLAYING, LINE_CLEAR, GAME_OVER
    score = 0
    hi_score = 0
    total_lines = 0
    level = 1
    
    fall_time = 0
    fall_speed = 600 

    is_grabbed = False
    rotation_state = 0 
    hold_shape = None
    hold_color = None
    can_hold = True
    
    grab_dx = 0.0 
    grab_dy = 0.0 
    initial_grab_y = 0.0 
    grab_angle = -90.0
    grab_scale_x = 100.0
    grab_scale_y = 100.0
    prev_is_fist = False

    # Animation Variables
    full_lines = []
    line_clear_start_time = 0
    level_up_start_time = -3000

    running = True
    while running:
        dt = clock.tick(30)
        current_time = pygame.time.get_ticks()
        tracker.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        just_closed_fist = False
        if tracker.has_hand:
            just_closed_fist = tracker.is_fist and not prev_is_fist

        # ==========================================
        # STATE: PLAYING
        # ==========================================
        if game_state == "PLAYING":
            if tracker.has_hand:
                piece_center_x = BOARD_X + (piece_x + len(current_shape[0]) / 2.0) * BLOCK_SIZE
                piece_center_y = BOARD_Y + (piece_y + len(current_shape) / 2.0) * BLOCK_SIZE

                # 1. ATTEMPT GRAB
                if just_closed_fist and not is_grabbed:
                    dist = math.hypot(tracker.hand_x - piece_center_x, tracker.hand_y - piece_center_y)
                    if dist < 120:  
                        is_grabbed = True
                        rotation_state = 0 
                        grab_dx = tracker.hand_x - (BOARD_X + piece_x * BLOCK_SIZE)
                        grab_dy = tracker.hand_y - (BOARD_Y + piece_y * BLOCK_SIZE)
                        initial_grab_y = tracker.hand_y 
                        grab_angle = tracker.fist_angle
                        grab_scale_x = max(tracker.scale_x, 1)
                        grab_scale_y = max(tracker.scale_y, 1)

                # 2. DRAG & ACTIONS
                if is_grabbed and tracker.is_fist:
                    dy = tracker.hand_y - initial_grab_y
                    virtual_hand_y = initial_grab_y + (dy * 1.8) if dy > 0 else tracker.hand_y

                    target_col = int((tracker.hand_x - grab_dx - BOARD_X) / BLOCK_SIZE)
                    target_row = int((virtual_hand_y - grab_dy - BOARD_Y) / BLOCK_SIZE)

                    while piece_x < target_col and not check_collision(board, current_shape, (piece_x + 1, piece_y)):
                        piece_x += 1
                    while piece_x > target_col and not check_collision(board, current_shape, (piece_x - 1, piece_y)):
                        piece_x -= 1
                    while piece_y < target_row and not check_collision(board, current_shape, (piece_x, piece_y + 1)):
                        piece_y += 1

                    # 3. ROTATION MECHANIC 
                    if tracker.fist_angle > (grab_angle + 25) and rotation_state == 0:
                        rotated = list(zip(*current_shape[::-1])) 
                        if not check_collision(board, rotated, (piece_x, piece_y)):
                            current_shape = rotated
                        rotation_state = 1
                    elif tracker.fist_angle < (grab_angle - 25) and rotation_state == 0:
                        rotated = [list(row) for row in zip(*current_shape)][::-1] 
                        if not check_collision(board, rotated, (piece_x, piece_y)):
                            current_shape = rotated
                        rotation_state = -1
                    elif (grab_angle - 12) <= tracker.fist_angle <= (grab_angle + 12):
                        rotation_state = 0

                    # 4. HOLD MECHANIC
                    is_pulled_back = (tracker.scale_x < grab_scale_x * 0.75) and (tracker.scale_y < grab_scale_y * 0.75)
                    
                    if can_hold and is_pulled_back:
                        if hold_shape is None:
                            hold_shape = current_shape
                            hold_color = current_color
                            current_shape, current_color = next_pieces.pop(0)
                            next_pieces.append(get_new_piece())
                        else:
                            temp_shape = current_shape
                            temp_color = current_color
                            current_shape = hold_shape
                            current_color = hold_color
                            hold_shape = temp_shape
                            hold_color = temp_color
                            
                        piece_x = COLS // 2 - len(current_shape[0]) // 2
                        piece_y = 0
                        can_hold = False
                        is_grabbed = False 
                
                # 5. RELEASE
                elif not tracker.is_fist:
                    is_grabbed = False 
            else:
                is_grabbed = False

            # --- GRAVITY & LOCKING ---
            fall_time += dt
            if fall_time >= fall_speed:
                piece_y += 1
                if check_collision(board, current_shape, (piece_x, piece_y)):
                    piece_y -= 1
                    
                    # Lock piece into board
                    for cy, row in enumerate(current_shape):
                        for cx, cell in enumerate(row):
                            if cell:
                                board[piece_y + cy][piece_x + cx] = current_color
                    
                    # Check for completed lines to trigger animation
                    full_lines = [i for i, row in enumerate(board) if (0, 0, 0) not in row]
                    
                    if full_lines:
                        game_state = "LINE_CLEAR"
                        line_clear_start_time = current_time
                        is_grabbed = False
                    else:
                        # Spawn Next Piece Immediately
                        current_shape, current_color = next_pieces.pop(0)
                        next_pieces.append(get_new_piece())
                        piece_x = COLS // 2 - len(current_shape[0]) // 2
                        piece_y = 0
                        can_hold = True 
                        is_grabbed = False 
                        
                        # Game Over Check
                        if check_collision(board, current_shape, (piece_x, piece_y)):
                            game_state = "GAME_OVER"
                            if score > hi_score:
                                hi_score = score
                        
                fall_time = 0

        # ==========================================
        # STATE: LINE CLEAR (Animation Pause)
        # ==========================================
        elif game_state == "LINE_CLEAR":
            if current_time - line_clear_start_time >= 1000: # 1 Second passed
                board, cleared = clear_lines(board)
                total_lines += cleared
                
                old_level = level
                level = (total_lines // 5) + 1 
                if level > old_level:
                    level_up_start_time = current_time # Trigger Level Up Flash
                
                fall_speed = max(100, 600 - ((level - 1) * 50)) 
                
                if cleared == 1: base_pts = 150
                elif cleared == 2: base_pts = 300
                elif cleared == 3: base_pts = 800
                elif cleared == 4: base_pts = 1500
                
                score += base_pts * level
                if score > hi_score:
                    hi_score = score

                # Spawn Next Piece
                current_shape, current_color = next_pieces.pop(0)
                next_pieces.append(get_new_piece())
                piece_x = COLS // 2 - len(current_shape[0]) // 2
                piece_y = 0
                can_hold = True 
                
                if check_collision(board, current_shape, (piece_x, piece_y)):
                    game_state = "GAME_OVER"
                else:
                    game_state = "PLAYING"

        # ==========================================
        # DRAWING ROUTINE
        # ==========================================
        window.fill((20, 24, 33))

        # 1. DRAW BOARD
        pygame.draw.rect(window, (40, 44, 53), (BOARD_X, BOARD_Y, BOARD_WIDTH, BOARD_HEIGHT))
        
        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                if cell != (0, 0, 0):
                    draw_c = cell
                    # Override color if this line is currently flashing
                    if game_state == "LINE_CLEAR" and y in full_lines:
                        color_idx = (current_time // 100) % 3
                        draw_c = FLASH_COLORS[color_idx]
                        
                    pygame.draw.rect(window, draw_c, 
                                     (BOARD_X + x*BLOCK_SIZE, BOARD_Y + y*BLOCK_SIZE, BLOCK_SIZE-1, BLOCK_SIZE-1))

        # 2. DRAW CURRENT PIECE (Hide during line clear)
        if game_state == "PLAYING":
            draw_color = (255, 255, 255) if is_grabbed else current_color
            for y, row in enumerate(current_shape):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(window, draw_color, 
                                         (BOARD_X + (piece_x + x)*BLOCK_SIZE, BOARD_Y + (piece_y + y)*BLOCK_SIZE, BLOCK_SIZE-1, BLOCK_SIZE-1))

        # 3. DRAW NEXT BOX (Top Left)
        next_x, next_y = BOARD_X - 160, BOARD_Y
        pygame.draw.rect(window, (40, 44, 53), (next_x, next_y, 140, 320))
        next_title = font_medium.render("NEXT", True, (200, 200, 200))
        window.blit(next_title, (next_x + 70 - next_title.get_width() // 2, next_y + 10))
        
        for i, (n_shape, n_color) in enumerate(next_pieces):
            offset_x = next_x + 70 - (len(n_shape[0]) * BLOCK_SIZE) / 2
            offset_y = next_y + 60 + (i * 90) - (len(n_shape) * BLOCK_SIZE) / 2
            for y, row in enumerate(n_shape):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(window, n_color, 
                                         (offset_x + x*BLOCK_SIZE, offset_y + y*BLOCK_SIZE, BLOCK_SIZE-1, BLOCK_SIZE-1))

        # 4. DRAW HOLD BOX (Bottom Left)
        hold_x, hold_y = BOARD_X - 160, BOARD_Y + 340
        pygame.draw.rect(window, (40, 44, 53), (hold_x, hold_y, 140, 140))
        hold_title = font_medium.render("HOLD", True, (200, 200, 200))
        window.blit(hold_title, (hold_x + 70 - hold_title.get_width() // 2, hold_y + 10))
        
        if hold_shape:
            offset_x = hold_x + 70 - (len(hold_shape[0]) * BLOCK_SIZE) / 2
            offset_y = hold_y + 70 - (len(hold_shape) * BLOCK_SIZE) / 2
            for y, row in enumerate(hold_shape):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(window, hold_color, 
                                         (offset_x + x*BLOCK_SIZE, offset_y + y*BLOCK_SIZE, BLOCK_SIZE-1, BLOCK_SIZE-1))

        # 5. DRAW STATS UI (Top Right)
        stats_x, stats_y = BOARD_X + BOARD_WIDTH + 20, BOARD_Y
        pygame.draw.rect(window, (40, 44, 53), (stats_x, stats_y, 200, 310))
        
        # Score
        score_title = font_small.render("SCORE", True, (150, 150, 150))
        score_val = font_large.render(f"{score:06d}", True, (255, 255, 255))
        window.blit(score_title, (stats_x + 15, stats_y + 15))
        window.blit(score_val, (stats_x + 15, stats_y + 35))
        
        # Hi-Score
        hi_title = font_small.render("HI-SCORE", True, (150, 150, 150))
        hi_val = font_medium.render(f"{hi_score:06d}", True, (255, 215, 0)) # Gold Color
        window.blit(hi_title, (stats_x + 15, stats_y + 95))
        window.blit(hi_val, (stats_x + 15, stats_y + 115))

        # Lines
        lines_title = font_small.render("LINES", True, (150, 150, 150))
        lines_val = font_medium.render(f"{total_lines}", True, (255, 255, 255))
        window.blit(lines_title, (stats_x + 15, stats_y + 165))
        window.blit(lines_val, (stats_x + 15, stats_y + 185))
        
        # Level (Flashing Animation synchronized for Title and Value)
        if current_time - level_up_start_time < 3000:
            c_idx = (current_time // 100) % 3
            level_flash_colors = [(255, 255, 255), (255, 255, 0), (255, 165, 0)]  # White, Yellow, Orange
            level_color = level_flash_colors[c_idx]
            level_title_color = level_color
        else:
            level_title_color = (150, 150, 150)
            level_color = (255, 255, 255)
            
        level_title = font_small.render("LEVEL", True, level_title_color)
        level_val = font_medium.render(f"{level}", True, level_color)
        window.blit(level_title, (stats_x + 15, stats_y + 235))
        window.blit(level_val, (stats_x + 15, stats_y + 255))

        # 6. STATE: GAME OVER (Overlay & Spacebar Restart)
        if game_state == "GAME_OVER":
            # Dim the screen
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            window.blit(overlay, (0, 0))
            
            # Text
            go_text = font_large.render("GAME OVER", True, (255, 50, 50))
            window.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 120))
            
            score_text = font_medium.render(f"Score: {score:06d}   Hi-Score: {hi_score:06d}", True, (255, 255, 255))
            window.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 50))

            restart_prompt = font_medium.render("PRESS SPACE TO RESTART", True, (200, 200, 200))
            window.blit(restart_prompt, (WIDTH//2 - restart_prompt.get_width()//2, HEIGHT//2 + 30))

            # Restart Logic
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                board = create_grid()
                next_pieces = [get_new_piece() for _ in range(3)]
                current_shape, current_color = get_new_piece()
                piece_x = COLS // 2 - len(current_shape[0]) // 2
                piece_y = 0
                
                score = 0
                total_lines = 0
                level = 1
                fall_speed = 600
                hold_shape = None
                can_hold = True
                is_grabbed = False
                level_up_start_time = -3000
                game_state = "PLAYING"

        # 7. SKELETON WITH DYNAMIC OFFSET
        render_offset_x = 0
        render_offset_y = 0
        
        if is_grabbed and tracker.has_hand and game_state == "PLAYING":
            visual_hand_x = BOARD_X + piece_x * BLOCK_SIZE + grab_dx
            dy = tracker.hand_y - initial_grab_y
            virtual_hand_y = initial_grab_y + (dy * 1.8) if dy > 0 else tracker.hand_y
            visual_hand_y = BOARD_Y + piece_y * BLOCK_SIZE + grab_dy
            
            render_offset_x = visual_hand_x - tracker.hand_x
            render_offset_y = visual_hand_y - tracker.hand_y

        tracker.draw(window, offset_x=render_offset_x, offset_y=render_offset_y)

        pygame.display.update()
        prev_is_fist = tracker.is_fist

    tracker.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()