import cv2
import time

# Initialize camera on /dev/video0 with V4L2 backend
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# Apply 720p MJPEG high-bandwidth configuration
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 60)

if not cap.isOpened():
    print("Error: Could not access /dev/video0")
    exit()

# Verify hardware settings granted
actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
target_fps = int(cap.get(cv2.CAP_PROP_FPS))

print(f"Active Stream: {actual_w}x{actual_h} @ {target_fps} FPS (MJPEG)")
print("Press 'q' in the video window to stop.")

prev_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Mirror frame horizontally for natural movement
    frame = cv2.flip(frame, 1)

    # Calculate real-time FPS
    curr_time = time.time()
    live_fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
    prev_time = curr_time

    # Render HUD status overlay
    cv2.putText(
        frame,
        f"Resolution: {actual_w}x{actual_h} | Live FPS: {int(live_fps)}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 120),
        2
    )

    cv2.imshow("WSL2 720p Camera Preview", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()