import cv2
import mediapipe as mp
import pygame
import sys

class HandTracker:
    def __init__(self, screen_width=1280, screen_height=720, z_threshold=-0.05, show_raw_feed=True):
        self.width = screen_width
        self.height = screen_height
        self.z_threshold = z_threshold
        self.show_raw_feed = show_raw_feed

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,  
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 21 hand landmarks connections
        self.connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),        
            (0, 5), (5, 6), (6, 7), (7, 8),        
            (5, 9), (9, 10), (10, 11), (11, 12),    
            (9, 13), (13, 14), (14, 15), (15, 16),  
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) 
        ]

        # Camera setup
        # Smart Camera Setup
        if sys.platform.startswith('linux'):
            # Safe settings for WSL / Linux
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        else:
            # Clean settings for Native Windows and macOS
            self.cap = cv2.VideoCapture(0)
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.has_hand = False
        self.pts = [] 
        self.is_engaged = True 

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            self.has_hand = False
            self.pts = []
            return

        frame = cv2.flip(frame, 1)

        if self.show_raw_feed:
            cv2.imshow("Raw Camera Feed", frame)
            cv2.waitKey(1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            self.has_hand = True
            landmarks = results.multi_hand_landmarks[0].landmark
            self.pts = [(int(lm.x * self.width), int(lm.y * self.height)) for lm in landmarks]
        else:
            self.has_hand = False
            self.pts = []

    def draw(self, surface):
        if not self.has_hand or not self.pts:
            return

        bone_thickness = 4
        node_radius = 6
        
        # Clean cyan/mint colors for the whole skeleton
        bone_color = (0, 255, 180) 
        node_color = (0, 255, 150) 

        # Draw bones
        for p1, p2 in self.connections:
            pygame.draw.line(surface, bone_color, self.pts[p1], self.pts[p2], bone_thickness)

        # Draw identical joints (no yellow circles)
        for px, py in self.pts:
            pygame.draw.circle(surface, node_color, (px, py), node_radius)
            pygame.draw.circle(surface, (255, 255, 255), (px, py), 2)

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()