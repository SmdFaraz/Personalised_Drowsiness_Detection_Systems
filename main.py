import cv2
import mediapipe as mp
import pygame
import time
import numpy as np

from eye_utils import eye_aspect_ratio
from mouth_utils import mouth_aspect_ratio

from ui.dashboard import (
    draw_header,
    draw_status_panel,
    draw_waiting,
    draw_calibration
)

# ------------------ INIT ------------------

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True
)

pygame.mixer.init()
pygame.mixer.music.load("assets/alarm.wav")

cap = cv2.VideoCapture(0)

# Create resizable window
cv2.namedWindow("Driver Monitoring System", cv2.WINDOW_NORMAL)

# Fullscreen toggle state
fullscreen = False

# Landmarks
LEFT_EYE = [33,160,158,133,153,144]
RIGHT_EYE = [362,385,387,263,373,380]
MOUTH = [78,81,13,311,308,402,14,178]

# Thresholds (will be calibrated)
EAR_THRESHOLD = 0.25
MAR_THRESHOLD = 0.50

# Detection params
CONSEC_FRAMES = 3
DROWSY_FRAMES = 20
YAWN_FRAMES = 15

blink_counter = 0
yawn_counter = 0

# Calibration state
calibrating = False
calibrated = False
calibration_start = 0
CALIB_DURATION = 5

ear_values = []
mar_values = []

# -------------------------------------------------

try:
    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        h, w, _ = frame.shape
        status = "WAITING"

        # -------- HEADER --------
        draw_header(frame)

        if results.multi_face_landmarks:

            for face_landmarks in results.multi_face_landmarks:

                left_eye = []
                right_eye = []
                mouth = []

                for idx in LEFT_EYE:
                    left_eye.append((
                        int(face_landmarks.landmark[idx].x * w),
                        int(face_landmarks.landmark[idx].y * h)
                    ))

                for idx in RIGHT_EYE:
                    right_eye.append((
                        int(face_landmarks.landmark[idx].x * w),
                        int(face_landmarks.landmark[idx].y * h)
                    ))

                for idx in MOUTH:
                    mouth.append((
                        int(face_landmarks.landmark[idx].x * w),
                        int(face_landmarks.landmark[idx].y * h)
                    ))

                ear = (eye_aspect_ratio(left_eye) +
                       eye_aspect_ratio(right_eye)) / 2.0

                mar = mouth_aspect_ratio(mouth)

                # -------- WAITING --------
                if not calibrated and not calibrating:
                    draw_waiting(frame, w, h)

                # -------- CALIBRATION --------
                elif calibrating:

                    elapsed = time.time() - calibration_start
                    remaining = max(0, int(CALIB_DURATION - elapsed))
                    progress = min(elapsed / CALIB_DURATION, 1.0)

                    ear_values.append(ear)
                    mar_values.append(mar)

                    draw_calibration(frame, w, h, remaining, progress)

                    if elapsed >= CALIB_DURATION:

                        EAR_THRESHOLD = np.mean(ear_values) - 0.05
                        MAR_THRESHOLD = np.mean(mar_values) + 0.10

                        calibrating = False
                        calibrated = True

                        print("\n=== CALIBRATION COMPLETE ===")
                        print(f"Average EAR: {np.mean(ear_values):.3f}")
                        print(f"Average MAR: {np.mean(mar_values):.3f}")
                        print(f"EAR Threshold: {EAR_THRESHOLD:.3f}")
                        print(f"MAR Threshold: {MAR_THRESHOLD:.3f}")
                        print("============================\n")

                # -------- NORMAL MODE --------
                elif calibrated:

                    status = "ALERT"

                    if ear < EAR_THRESHOLD:
                        blink_counter += 1
                        if blink_counter >= DROWSY_FRAMES:
                            status = "DROWSY"
                    else:
                        blink_counter = 0

                    if mar > MAR_THRESHOLD:
                        yawn_counter += 1
                        if yawn_counter >= YAWN_FRAMES:
                            status = "DROWSY"
                            yawn_counter = 0
                    else:
                        yawn_counter = 0

                    draw_status_panel(frame, ear, mar, status)

        # -------- ALARM --------
        if calibrated:
            if status == "DROWSY":
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.stop()

        # Show frame
        cv2.imshow("Driver Monitoring System", frame)

        key = cv2.waitKey(1) & 0xFF

        # -------- KEY CONTROLS --------

        # Start calibration
        if key == ord('c') and not calibrated:
            calibrating = True
            calibration_start = time.time()
            ear_values.clear()
            mar_values.clear()

        # Toggle fullscreen
        if key == ord('f'):
            fullscreen = not fullscreen

            if fullscreen:
                cv2.setWindowProperty(
                    "Driver Monitoring System",
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN
                )
            else:
                cv2.setWindowProperty(
                    "Driver Monitoring System",
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_NORMAL
                )

        # Exit
        if key == 27:
            break

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    pygame.mixer.music.stop()
    cap.release()
    cv2.destroyAllWindows()