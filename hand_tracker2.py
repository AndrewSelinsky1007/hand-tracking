import cv2
import mediapipe as mp
import pygame
import sys
import math

class HandTracker:
    def __init__(self, screen_width=1280, screen_height=720, show_raw_feed=True):
        self.width = screen_width
        self.height = screen_height
        self.show_raw_feed = show_raw_feed

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,  
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),        
            (0, 5), (5, 6), (6, 7), (7, 8),        
            (5, 9), (9, 10), (10, 11), (11, 12),    
            (9, 13), (13, 14), (14, 15), (15, 16),  
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) 
        ]

        if sys.platform.startswith('linux'):
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        else:
            self.cap = cv2.VideoCapture(0)
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.has_hand = False
        self.pts = [] 
        
        self.hand_x = 0
        self.hand_y = 0
        self.is_fist = False
        self.fist_angle = -90
        
        # Dual-Axis scale tracking
        self.scale_x = 100 
        self.scale_y = 100 

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            self.has_hand = False
            self.pts = []
            return

        frame = cv2.flip(frame, 1)

        if self.show_raw_feed:
            cv2.imshow("Raw Video Feed", frame)
            cv2.waitKey(1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            self.has_hand = True
            landmarks = results.multi_hand_landmarks[0].landmark
            self.pts = [(int(lm.x * self.width), int(lm.y * self.height)) for lm in landmarks]

            self.hand_x = self.pts[9][0]
            self.hand_y = self.pts[9][1]

            # Measure Horizontal Width (Index to Pinky)
            self.scale_x = math.hypot(self.pts[5][0] - self.pts[17][0], self.pts[5][1] - self.pts[17][1])
            # Measure Vertical Length (Wrist to Middle Knuckle)
            self.scale_y = math.hypot(self.pts[9][0] - self.pts[0][0], self.pts[9][1] - self.pts[0][1])

            # Fist detection
            self.is_fist = True
            for tip, mcp in zip([8, 12, 16, 20], [5, 9, 13, 17]):
                dist_tip = math.hypot(landmarks[tip].x - landmarks[0].x, landmarks[tip].y - landmarks[0].y)
                dist_mcp = math.hypot(landmarks[mcp].x - landmarks[0].x, landmarks[mcp].y - landmarks[0].y)
                if dist_tip > dist_mcp * 1.3:
                    self.is_fist = False
                    break

            # Wrist rotation calculation
            dy = landmarks[9].y - landmarks[0].y
            dx = landmarks[9].x - landmarks[0].x
            self.fist_angle = math.degrees(math.atan2(dy, dx))

        else:
            self.has_hand = False
            self.pts = []
            self.is_fist = False

    def draw(self, surface, offset_x=0, offset_y=0):
        if not self.has_hand or not self.pts:
            return

        bone_thickness = 4
        node_radius = 6
        bone_color = (0, 255, 180) 
        node_color = (255, 120, 50) if self.is_fist else (0, 255, 150)

        for p1, p2 in self.connections:
            pt1 = (self.pts[p1][0] + int(offset_x), self.pts[p1][1] + int(offset_y))
            pt2 = (self.pts[p2][0] + int(offset_x), self.pts[p2][1] + int(offset_y))
            pygame.draw.line(surface, bone_color, pt1, pt2, bone_thickness)

        for px, py in self.pts:
            cx = px + int(offset_x)
            cy = py + int(offset_y)
            pygame.draw.circle(surface, node_color, (cx, cy), node_radius)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)

    def close(self):
        self.cap.release()
        cv2.destroyAllWindows()