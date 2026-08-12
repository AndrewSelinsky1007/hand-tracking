import cv2
import mediapipe as mp
import pygame
import sys

# ==========================================
# 1. SETUP MEDIAPIPE & PYGAME
# ==========================================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,  # <--- CHANGED TO 2 HANDS
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
]

pygame.init()
WIDTH, HEIGHT = 1280, 720
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Hand Sensing Sandbox (Multi-Hand)")
clock = pygame.time.Clock()

# Camera setup using V4L2 and MJPEG
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # Disable Auto-Exposure
cap.set(cv2.CAP_PROP_FPS, 30)

font_main = pygame.font.SysFont("Consolas", 22)
font_large = pygame.font.SysFont("Consolas", 36, bold=True)

# ==========================================
# 2. MAIN INSPECTION LOOP
# ==========================================
while True:
    dt = clock.tick(30)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()
            cv2.destroyAllWindows()  # Close OpenCV raw video window
            pygame.quit()
            sys.exit()

    ret, frame = cap.read()
    window.fill((20, 24, 33))

    if ret:
        frame = cv2.flip(frame, 1)

        # ----------------------------------------------------
        # SHOW SEPARATE RAW CAMERA FEED WINDOW
        # ----------------------------------------------------
        cv2.imshow("Raw Video Feed", frame)
        cv2.waitKey(1)  # Required to keep OpenCV window responsive

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            # LOOP THROUGH ALL DETECTED HANDS (UP TO 2)
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                landmarks = hand_landmarks.landmark

                wrist = landmarks[0]
                index_tip = landmarks[8]

                pts = [(int(lm.x * WIDTH), int(lm.y * HEIGHT)) for lm in landmarks]
                
                # Static colors for the skeleton
                bone_color = (0, 255, 180) 
                for p1, p2 in HAND_CONNECTIONS:
                    pygame.draw.line(window, bone_color, pts[p1], pts[p2], 4)

                for i, lm in enumerate(landmarks):
                    px, py = pts[i]
                    # Keep the size scaling based on Z-depth, but use a static color
                    node_radius = max(4, int(14 - (lm.z * 60)))
                    node_color = (0, 255, 150) 

                    pygame.draw.circle(window, node_color, (px, py), node_radius)
                    pygame.draw.circle(window, (255, 255, 255), (px, py), 2)

                # DYNAMIC HUD OFFSET (Pushes Hand 2's text down by 200 pixels)
                y_offset = hand_idx * 200

                state_str = f"HAND {hand_idx + 1}: DETECTED"
                state_color = (0, 255, 150)
                
                state_text = font_large.render(state_str, True, state_color)
                window.blit(state_text, (30, 30 + y_offset))

                hud_lines = [
                    f"Index Tip (#8) -> X: {index_tip.x:.3f} | Y: {index_tip.y:.3f} | Z: {index_tip.z:.3f}",
                    f"Wrist     (#0) -> X: {wrist.x:.3f} | Y: {wrist.y:.3f} | Z: {wrist.z:.3f}"
                ]

                for idx, line in enumerate(hud_lines):
                    txt_surface = font_main.render(line, True, (220, 220, 230))
                    window.blit(txt_surface, (30, 80 + y_offset + (idx * 28)))

        else:
            no_hand_txt = font_large.render("NO HAND DETECTED - Hold hands up to camera", True, (255, 100, 100))
            window.blit(no_hand_txt, (WIDTH // 2 - 400, HEIGHT // 2))

    pygame.display.update()